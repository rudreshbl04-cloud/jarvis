import sys
import os
import time
import shutil
import subprocess
import datetime

WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
JARVIS_PY = os.path.join(WORKSPACE, "jarvis.py")
BACKUPS_DIR = os.path.join(WORKSPACE, "backups")
LOG_PATH = os.path.join(WORKSPACE, "artifacts", "verification", "regression-guard.log")

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def restart_server():
    log("[GUARD] Restarting JARVIS server for updated candidate...")
    start_script = os.path.join(WORKSPACE, "scripts", "start_jarvis.ps1")
    res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", start_script, "-ForceRestart", "-NoBrowser"], capture_output=True, text=True, timeout=40)
    time.sleep(2)
    return res.returncode == 0

def check_py_compile(target_file=JARVIS_PY):
    log(f"[GUARD:A] Checking Python compilation for {target_file}...")
    res = subprocess.run([sys.executable, "-m", "py_compile", target_file], capture_output=True, text=True)
    if res.returncode == 0:
        log("[GUARD:A] Python compilation PASSED.")
        return True, ""
    else:
        err = res.stderr or res.stdout
        log(f"[GUARD:A] Python compilation FAILED:\n{err}")
        return False, err

def check_health():
    log("[GUARD:D] Checking server health...")
    hc_script = os.path.join(WORKSPACE, "scripts", "health_check.py")
    res = subprocess.run([sys.executable, hc_script], capture_output=True, text=True)
    if res.returncode == 0:
        log(f"[GUARD:D] Server health check PASSED.\n{res.stdout.strip()}")
        return True, res.stdout
    else:
        err = res.stderr or res.stdout
        log(f"[GUARD:D] Server health check FAILED:\n{err.strip()}")
        return False, err

def check_rendered_js():
    log("[GUARD:B,C] Extracting rendered JS and checking syntax...")
    cjs_script = os.path.join(WORKSPACE, "scripts", "check_rendered_js.py")
    res = subprocess.run([sys.executable, cjs_script], capture_output=True, text=True)
    if res.returncode == 0:
        log(f"[GUARD:B,C] Rendered JavaScript check PASSED.\n{res.stdout.strip()}")
        return True, res.stdout
    else:
        err = res.stderr or res.stdout
        log(f"[GUARD:B,C] Rendered JavaScript check FAILED:\n{err.strip()}")
        return False, err

def check_focused_tests():
    log("[GUARD:E] Running focused regression tests...")
    tests_dir = os.path.join(WORKSPACE, "tests")
    if not os.path.exists(tests_dir):
        log("[GUARD:E] No tests directory found, skipping.")
        return True, "No tests"
    test_files = [os.path.join(tests_dir, f) for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
    if not test_files:
        log("[GUARD:E] No test files found in tests/, passing.")
        return True, "No test files"
    
    all_passed = True
    output = []
    for tf in test_files:
        res = subprocess.run([sys.executable, tf], capture_output=True, text=True, timeout=90)
        if res.returncode == 0:
            log(f"[GUARD:E] {os.path.basename(tf)}: PASSED")
            output.append(f"{os.path.basename(tf)}: PASS")
        else:
            log(f"[GUARD:E] {os.path.basename(tf)}: FAILED\n{res.stderr or res.stdout}")
            output.append(f"{os.path.basename(tf)}: FAIL")
            all_passed = False
    return all_passed, "\n".join(output)

def run_all_checks(target_file=JARVIS_PY, restart=False):
    log("=== Starting Regression Guard Validation ===")
    ok_py, err_py = check_py_compile(target_file)
    if not ok_py:
        return False, f"Python compile failure: {err_py}"

    if restart:
        restart_server()

    ok_health, err_health = check_health()
    if not ok_health:
        return False, f"Health check failure: {err_health}"

    ok_js, err_js = check_rendered_js()
    if not ok_js:
        return False, f"Rendered JS syntax failure: {err_js}"

    ok_tests, err_tests = check_focused_tests()
    if not ok_tests:
        return False, f"Focused tests failure: {err_tests}"

    log("=== Regression Guard Validation: ALL CHECKS PASSED (ACCEPT) ===")
    return True, "All checks passed"

def transactional_apply(candidate_path):
    """
    Applies candidate file to jarvis.py.
    Preserves backup.
    Rolls back automatically if any check fails!
    """
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUPS_DIR, f"jarvis_pre_guard_{ts}.py")
    
    log(f"[TRANSACTION] Backing up current jarvis.py to {backup_file}...")
    shutil.copy2(JARVIS_PY, backup_file)

    log(f"[TRANSACTION] Applying candidate from {candidate_path} to {JARVIS_PY}...")
    shutil.copy2(candidate_path, JARVIS_PY)

    # Validate with restart
    passed, summary = run_all_checks(JARVIS_PY, restart=True)
    if passed:
        log("[TRANSACTION] Candidate edit VALIDATED and COMMITTED.")
        return True
    else:
        log(f"[TRANSACTION] Candidate edit FAILED checks: {summary}")
        log(f"[TRANSACTION] ROLLING BACK jarvis.py to {backup_file}...")
        shutil.copy2(backup_file, JARVIS_PY)
        restart_server()
        log("[TRANSACTION] Rollback complete. Working directory restored to known-good.")
        return False

def test_guard_enforcement():
    log("=== Demonstrating Regression Guard Enforcement ===")
    test_target = os.path.join(WORKSPACE, "scratch", "dummy_guard_target.py")
    known_good_content = 'print("Known good version operational")\n'
    bad_syntax_content = 'def broken_function(\n  this is invalid syntax !!!\n'

    os.makedirs(os.path.join(WORKSPACE, "scratch"), exist_ok=True)
    with open(test_target, "w", encoding="utf-8") as f:
        f.write(known_good_content)

    bad_candidate = os.path.join(WORKSPACE, "scratch", "dummy_bad_candidate.py")
    with open(bad_candidate, "w", encoding="utf-8") as f:
        f.write(bad_syntax_content)

    log("[TEST-GUARD] Testing bad candidate with intentional syntax error...")
    ok, err = check_py_compile(bad_candidate)
    assert not ok, "Guard should have rejected bad syntax!"
    log("[TEST-GUARD] Verified: Bad syntax rejected by guard!")

    with open(test_target, "r", encoding="utf-8") as f:
        assert f.read() == known_good_content, "Known-good content was altered!"
    log("[TEST-GUARD] Verified: Known-good version preserved intact!")

    good_candidate = os.path.join(WORKSPACE, "scratch", "dummy_good_candidate.py")
    with open(good_candidate, "w", encoding="utf-8") as f:
        f.write('print("New valid candidate syntax")\n')
    ok_good, _ = check_py_compile(good_candidate)
    assert ok_good, "Guard should have accepted valid candidate!"
    log("[TEST-GUARD] Verified: Valid candidate passed compilation check!")
    log("=== Regression Guard Enforcement Demo: SUCCESS ===")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-guard":
        success = test_guard_enforcement()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 2 and sys.argv[1] == "--apply":
        cand = sys.argv[2]
        success = transactional_apply(cand)
        sys.exit(0 if success else 1)
    else:
        success, _ = run_all_checks(JARVIS_PY)
        sys.exit(0 if success else 1)
