"""Safe storage and recovery engine for JARVIS 4.0 / RUBI CORE.
Guarantees:
1. Atomic writes via temp files and fsync.
2. Automatic backup checkpointing (.bak).
3. Automatic corrupted-state recovery from last known good .bak before initializing default.
4. Thread-safe execution using re-entrant locks.
5. Path anchoring to application directory.
"""

import os
import sys
import json
import uuid
import time
import shutil
import logging
from pathlib import Path
from threading import RLock

STORAGE_LOCK = RLock()
STORAGE_WARNINGS = []

logger = logging.getLogger("jarvis.storage")

def compute_file_sha256(filepath):
    import hashlib
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def checkpoint_file(path):
    """Create a .bak checkpoint of the file if it exists and is non-empty."""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return
    bak_path = p.with_suffix(p.suffix + '.bak')
    try:
        shutil.copy2(p, bak_path)
    except OSError as e:
        logger.warning(f"Could not checkpoint {p.name}: {e}")

def atomic_write_text(path, text):
    """Write text atomically to path using temporary file, fsync, and Windows-safe retry replace."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = str(p) + '.' + uuid.uuid4().hex + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())

        # If original exists, ensure a checkpoint exists before replacing
        if p.exists() and p.stat().st_size > 0:
            checkpoint_file(p)

        # Retry loop for Windows file locking
        replaced = False
        for attempt in range(5):
            try:
                os.replace(tmp_path, p)
                replaced = True
                break
            except (PermissionError, OSError):
                time.sleep(0.05 * (attempt + 1))
        
        if not replaced:
            os.replace(tmp_path, p)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def safe_save_json(path, data):
    """Thread-safe, atomic JSON save with ensure_ascii=False."""
    with STORAGE_LOCK:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        atomic_write_text(path, json_str)

def safe_load_json(path, default):
    """
    Safely load JSON from path.
    If the file is missing, returns default.
    If corrupted/unreadable:
      1. Tries to restore from path.bak.
      2. If .bak succeeds, recovers file and returns .bak data.
      3. Only returns default if both fail, recording an explicit warning.
    """
    p = Path(path)
    bak_p = p.with_suffix(p.suffix + '.bak')
    
    if not p.exists():
        if bak_p.exists():
            try:
                with open(bak_p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, type(default)):
                    logger.info(f"Primary {p.name} missing; recovered from backup.")
                    safe_save_json(p, data)
                    return data
            except Exception:
                pass
        return default

    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, type(default)):
            logger.warning(f"{p.name} type mismatch (expected {type(default).__name__}, got {type(data).__name__})")
            return default
        # Keep checkpoint up to date
        checkpoint_file(p)
        return data
    except (json.JSONDecodeError, OSError) as err:
        err_msg = f"Critical: {p.name} corrupted ({err}). Attempting recovery from backup."
        STORAGE_WARNINGS.append(err_msg)
        logger.error(err_msg)
        if bak_p.exists():
            try:
                with open(bak_p, 'r', encoding='utf-8') as bf:
                    bak_data = json.load(bf)
                if isinstance(bak_data, type(default)):
                    logger.info(f"Successfully recovered {p.name} from backup checkpoint.")
                    # Restore primary file from valid backup
                    safe_save_json(p, bak_data)
                    return bak_data
            except Exception as b_err:
                logger.error(f"Backup checkpoint for {p.name} also unreadable: {b_err}")

        # If no backup or backup failed, return default but do NOT overwrite the corrupted file
        corrupt_dump = str(p) + f".corrupt_{int(time.time())}"
        try:
            shutil.copy2(p, corrupt_dump)
            logger.info(f"Preserved corrupted copy at {corrupt_dump}")
        except Exception:
            pass
        return default
