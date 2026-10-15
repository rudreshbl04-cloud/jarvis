"""Controlled Task Lifecycle and Execution Engine for JARVIS 4.0 / RUBI CORE.

Lifecycle:
  RECEIVED -> VALIDATING -> PLANNING -> AWAITING_APPROVAL -> EXECUTING -> VERIFYING -> SUCCEEDED / FAILED / CANCELLED / EXPIRED

Action Classification:
  - READ_ONLY (e.g., read file, check status, get time)
  - IDEMPOTENT (e.g., set volume to 50, ensure app running)
  - REVERSIBLE (e.g., open app, create draft note)
  - NON_IDEMPOTENT (e.g., send message, delete data, payment, shutdown)
"""

import time
import uuid
import threading
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("jarvis.task_engine")

class TaskStatus:
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

    TERMINAL_STATES = {SUCCEEDED, FAILED, CANCELLED, EXPIRED}

class ActionType:
    READ_ONLY = "READ_ONLY"
    IDEMPOTENT = "IDEMPOTENT"
    REVERSIBLE = "REVERSIBLE"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"

VALID_TRANSITIONS = {
    TaskStatus.RECEIVED: {TaskStatus.VALIDATING, TaskStatus.PLANNING, TaskStatus.AWAITING_APPROVAL, TaskStatus.EXECUTING, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.VALIDATING: {TaskStatus.PLANNING, TaskStatus.AWAITING_APPROVAL, TaskStatus.EXECUTING, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.PLANNING: {TaskStatus.AWAITING_APPROVAL, TaskStatus.EXECUTING, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.AWAITING_APPROVAL: {TaskStatus.EXECUTING, TaskStatus.PLANNING, TaskStatus.CANCELLED, TaskStatus.EXPIRED, TaskStatus.FAILED},
    TaskStatus.EXECUTING: {TaskStatus.VERIFYING, TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.VERIFYING: {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.SUCCEEDED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
    TaskStatus.EXPIRED: set(),
}

class Task:
    def __init__(
        self,
        task_id: str,
        request_text: str,
        action_type: str = ActionType.READ_ONLY,
        timeout_seconds: float = 60.0,
        idempotency_key: Optional[str] = None
    ):
        self.task_id = task_id
        self.request_text = request_text.strip()
        self.action_type = action_type
        self.status = TaskStatus.RECEIVED
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.timeout_seconds = timeout_seconds
        self.expires_at = self.created_at + timeout_seconds
        
        self.plan: List[Dict[str, Any]] = []
        self.authorized_tools: List[str] = []
        self.approval_state: str = "NOT_REQUIRED"  # NOT_REQUIRED, PENDING, APPROVED, REJECTED, EXPIRED
        self.approval_bound_action: Optional[Dict[str, Any]] = None
        self.execution_records: List[Dict[str, Any]] = []
        self.verification_result: Optional[Dict[str, Any]] = None
        self.outcome: Optional[str] = None
        self.error: Optional[str] = None
        self.idempotency_key = idempotency_key
        self.stop_requested = False

    def is_expired(self) -> bool:
        return time.time() > self.expires_at and self.status not in TaskStatus.TERMINAL_STATES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "request_text": self.request_text,
            "action_type": self.action_type,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "timeout_seconds": self.timeout_seconds,
            "expires_at": self.expires_at,
            "plan_step_count": len(self.plan),
            "approval_state": self.approval_state,
            "execution_records_count": len(self.execution_records),
            "verification_result": self.verification_result,
            "outcome": self.outcome,
            "error": self.error,
            "stopped": self.stop_requested
        }

class TaskLifecycleEngine:
    def __init__(self, max_history: int = 200):
        self.lock = threading.RLock()
        self.tasks: Dict[str, Task] = {}
        self.active_task_id: Optional[str] = None
        self.recent_idempotency_keys: Dict[str, float] = {}  # key -> timestamp
        self.max_history = max_history

    def create_task(
        self,
        request_text: str,
        action_type: str = ActionType.READ_ONLY,
        timeout_seconds: float = 60.0,
        idempotency_key: Optional[str] = None
    ) -> Task:
        with self.lock:
            # Check idempotency for non-idempotent operations
            if idempotency_key and action_type == ActionType.NON_IDEMPOTENT:
                now = time.time()
                # Purge old keys (> 300s)
                self.recent_idempotency_keys = {
                    k: ts for k, ts in self.recent_idempotency_keys.items() if now - ts < 300
                }
                if idempotency_key in self.recent_idempotency_keys:
                    raise ValueError(f"Duplicate non-idempotent action rejected (idempotency key: {idempotency_key})")
                self.recent_idempotency_keys[idempotency_key] = now

            task_id = f"task_{uuid.uuid4().hex[:10]}"
            task = Task(
                task_id=task_id,
                request_text=request_text,
                action_type=action_type,
                timeout_seconds=timeout_seconds,
                idempotency_key=idempotency_key
            )
            self.tasks[task_id] = task
            self.active_task_id = task_id
            self._prune_history()
            return task

    def transition(self, task_id: str, new_status: str, reason: Optional[str] = None) -> Task:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found.")

            if task.status in TaskStatus.TERMINAL_STATES:
                return task

            allowed = VALID_TRANSITIONS.get(task.status, set())
            if new_status not in allowed:
                raise ValueError(f"Invalid task transition from {task.status} to {new_status}")

            task.status = new_status
            task.updated_at = time.time()
            if reason:
                if new_status == TaskStatus.FAILED:
                    task.error = reason
                elif new_status in (TaskStatus.CANCELLED, TaskStatus.EXPIRED):
                    task.outcome = reason

            if new_status in TaskStatus.TERMINAL_STATES and self.active_task_id == task_id:
                self.active_task_id = None

            return task

    def require_approval(self, task_id: str, action_details: Dict[str, Any]) -> Task:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found.")
            task.approval_state = "PENDING"
            task.approval_bound_action = action_details
            self.transition(task_id, TaskStatus.AWAITING_APPROVAL)
            return task

    def grant_approval(self, task_id: str, proposed_action: Dict[str, Any]) -> bool:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            if task.is_expired():
                self.transition(task_id, TaskStatus.EXPIRED, "Approval timeout expired.")
                return False
            if task.approval_state != "PENDING":
                return False
            # Verify that action has not mutated since approval was requested
            if task.approval_bound_action != proposed_action:
                self.transition(task_id, TaskStatus.FAILED, "Action parameters modified after approval request.")
                return False

            task.approval_state = "APPROVED"
            return True

    def reject_approval(self, task_id: str, reason: str = "User rejected operation.") -> Task:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found.")
            task.approval_state = "REJECTED"
            return self.transition(task_id, TaskStatus.CANCELLED, reason)

    def request_emergency_stop(self, task_id: Optional[str] = None) -> List[str]:
        """Cancel active task(s) and set stop flag."""
        with self.lock:
            cancelled_ids = []
            targets = [self.tasks[task_id]] if task_id and task_id in self.tasks else list(self.tasks.values())
            for t in targets:
                if t.status not in TaskStatus.TERMINAL_STATES:
                    t.stop_requested = True
                    self.transition(t.task_id, TaskStatus.CANCELLED, "Emergency Stop triggered.")
                    cancelled_ids.append(t.task_id)
            self.active_task_id = None
            return cancelled_ids

    def record_step(self, task_id: str, step_num: int, tool: str, args: Dict[str, Any], result: Any, success: bool):
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            rec = {
                "step": step_num,
                "tool": tool,
                "timestamp": time.time(),
                "success": success,
                "result_preview": str(result)[:300]
            }
            task.execution_records.append(rec)
            task.updated_at = time.time()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            t = self.tasks.get(task_id)
            return t.to_dict() if t else None

    def get_active_task(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            if self.active_task_id and self.active_task_id in self.tasks:
                return self.tasks[self.active_task_id].to_dict()
            return None

    def _prune_history(self):
        if len(self.tasks) > self.max_history:
            # Sort by created_at and keep newest
            sorted_tasks = sorted(self.tasks.items(), key=lambda kv: kv[1].created_at)
            to_remove = sorted_tasks[:-self.max_history]
            for tid, _ in to_remove:
                if tid != self.active_task_id:
                    del self.tasks[tid]

# Global singleton task engine instance
TASK_ENGINE = TaskLifecycleEngine()
