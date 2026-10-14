import sys
import os
import time
from regression_guard import run_all_checks, JARVIS_PY, log

def watch():
    log("[WATCHER] Starting file watcher for jarvis.py regression guard...")
    last_mtime = os.path.getmtime(JARVIS_PY)
    try:
        while True:
            time.sleep(2)
            try:
                curr_mtime = os.path.getmtime(JARVIS_PY)
                if curr_mtime != last_mtime:
                    log(f"[WATCHER] Change detected in {JARVIS_PY} (mtime {curr_mtime} != {last_mtime})")
                    last_mtime = curr_mtime
                    # Give editor a moment to finish writing
                    time.sleep(0.5)
                    passed, msg = run_all_checks(JARVIS_PY)
                    log(f"[WATCHER] Validation finished. Passed: {passed}. Message: {msg}")
            except Exception as e:
                log(f"[WATCHER] Error checking mtime: {e}")
    except KeyboardInterrupt:
        log("[WATCHER] Watcher stopped by user.")

if __name__ == "__main__":
    watch()
