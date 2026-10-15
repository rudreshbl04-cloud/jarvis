import unittest
import os
import json
import time
import shutil
from pathlib import Path

from core.storage import safe_load_json, safe_save_json, checkpoint_file
from core.task_engine import TaskLifecycleEngine, TaskStatus, ActionType

class TestStage2CoreReliability(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("scratch/test_stage2_tmp")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_safe_storage_atomic_and_recovery(self):
        target_file = self.test_dir / "data.json"
        bak_file = self.test_dir / "data.json.bak"
        
        # 1. Save valid initial data
        initial_data = {"key": "val1", "count": 42}
        safe_save_json(target_file, initial_data)
        self.assertTrue(target_file.exists())
        
        # 2. Checkpoint created on subsequent save
        second_data = {"key": "val2", "count": 99}
        safe_save_json(target_file, second_data)
        self.assertTrue(bak_file.exists())
        
        # Verify checkpoint contains valid previous data
        with open(bak_file, 'r', encoding='utf-8') as f:
            bak_content = json.load(f)
        self.assertEqual(bak_content["key"], "val1")

        # 3. Simulate sudden corruption of primary file (e.g. truncated/bad JSON)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('{"key": "corrupted", "count":') # Unfinished json

        # 4. safe_load_json must recover from data.json.bak rather than resetting to default!
        recovered = safe_load_json(target_file, default={})
        self.assertEqual(recovered["key"], "val1")
        self.assertEqual(recovered["count"], 42)

    def test_task_lifecycle_transitions(self):
        engine = TaskLifecycleEngine()
        task = engine.create_task("Open calculator and compute 12 * 8", action_type=ActionType.READ_ONLY)
        self.assertEqual(task.status, TaskStatus.RECEIVED)

        # Transition to VALIDATING
        engine.transition(task.task_id, TaskStatus.VALIDATING)
        self.assertEqual(task.status, TaskStatus.VALIDATING)

        # Transition to PLANNING
        engine.transition(task.task_id, TaskStatus.PLANNING)
        self.assertEqual(task.status, TaskStatus.PLANNING)

        # Transition to EXECUTING
        engine.transition(task.task_id, TaskStatus.EXECUTING)
        self.assertEqual(task.status, TaskStatus.EXECUTING)

        # Transition to VERIFYING
        engine.transition(task.task_id, TaskStatus.VERIFYING)
        self.assertEqual(task.status, TaskStatus.VERIFYING)

        # Transition to SUCCEEDED
        engine.transition(task.task_id, TaskStatus.SUCCEEDED)
        self.assertEqual(task.status, TaskStatus.SUCCEEDED)

        # Terminal state cannot transition to EXECUTING
        engine.transition(task.task_id, TaskStatus.EXECUTING)
        self.assertEqual(task.status, TaskStatus.SUCCEEDED)

    def test_task_invalid_transition_rejected(self):
        engine = TaskLifecycleEngine()
        task = engine.create_task("Safe read query")
        # Direct RECEIVED to SUCCEEDED without execution must raise ValueError
        with self.assertRaises(ValueError):
            engine.transition(task.task_id, TaskStatus.SUCCEEDED)

    def test_task_approval_gate_and_mutation_detection(self):
        engine = TaskLifecycleEngine()
        task = engine.create_task("Delete old cache file", action_type=ActionType.NON_IDEMPOTENT)
        
        proposed_action = {"tool": "delete_file", "target": "C:/temp/cache.tmp"}
        engine.require_approval(task.task_id, proposed_action)
        self.assertEqual(task.status, TaskStatus.AWAITING_APPROVAL)
        self.assertEqual(task.approval_state, "PENDING")

        # Mutated action attempt during approval must be rejected
        mutated_action = {"tool": "delete_file", "target": "C:/Windows/system32"}
        approved = engine.grant_approval(task.task_id, mutated_action)
        self.assertFalse(approved)
        self.assertEqual(task.status, TaskStatus.FAILED)

    def test_task_idempotency_duplicate_prevention(self):
        engine = TaskLifecycleEngine()
        idemp_key = "action_send_sms_9921"

        # First execution succeeds
        t1 = engine.create_task("Send notification", action_type=ActionType.NON_IDEMPOTENT, idempotency_key=idemp_key)
        self.assertIsNotNone(t1)

        # Duplicate attempt with same idempotency key must be rejected
        with self.assertRaises(ValueError):
            engine.create_task("Send notification again", action_type=ActionType.NON_IDEMPOTENT, idempotency_key=idemp_key)

    def test_emergency_stop_cancellation(self):
        engine = TaskLifecycleEngine()
        t1 = engine.create_task("Long running automation task")
        engine.transition(t1.task_id, TaskStatus.EXECUTING)

        stopped_ids = engine.request_emergency_stop(t1.task_id)
        self.assertIn(t1.task_id, stopped_ids)
        self.assertEqual(t1.status, TaskStatus.CANCELLED)
        self.assertTrue(t1.stop_requested)

if __name__ == "__main__":
    unittest.main()
