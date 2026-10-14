import sys
import re
import urllib.request
import urllib.parse
import http.cookiejar
import subprocess
import os

def extract_and_check_rendered_js(base_url="http://127.0.0.1:5000", pin="1234"):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Step 1: Unlock session with PIN
    try:
        lock_url = f"{base_url}/lock"
        data = json_bytes = b'{"pin":"' + pin.encode('utf-8') + b'"}'
        req = urllib.request.Request(lock_url, data=data, headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=5) as resp:
            pass
    except Exception as e:
        print(f"[RENDERED_JS] Warning: /lock request failed ({e}), trying root directly...")

    # Step 2: Fetch rendered HTML from root /
    try:
        with opener.open(f"{base_url}/", timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[RENDERED_JS] Error fetching rendered HTML from {base_url}/: {e}")
        return False

    # Step 3: Extract inline <script> blocks
    # Match <script> tags without src attribute
    script_pattern = re.compile(r'<script(?![^>]*\bsrc\b)[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
    scripts = script_pattern.findall(html)
    
    if not scripts:
        print("[RENDERED_JS] Error: No inline <script> tags found in rendered HTML!")
        return False

    combined_js = "\n\n// --- SCRIPT BLOCK SEPARATOR ---\n\n".join(scripts)
    os.makedirs("scratch", exist_ok=True)
    os.makedirs("artifacts/verification", exist_ok=True)
    
    scratch_target = os.path.abspath("scratch/extracted-rendered.js")
    artifact_target = os.path.abspath("artifacts/verification/extracted-rendered.js")
    
    with open(scratch_target, "w", encoding="utf-8") as f:
        f.write(combined_js)
    with open(artifact_target, "w", encoding="utf-8") as f:
        f.write(combined_js)

    print(f"[RENDERED_JS] Extracted {len(scripts)} inline script blocks ({len(combined_js)} chars) to {scratch_target}")

    # Step 4: Run node --check
    try:
        res = subprocess.run(["node", "--check", scratch_target], capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            print("[RENDERED_JS] node --check PASSED: Rendered JavaScript is syntactically valid!")
            return True
        else:
            print("[RENDERED_JS] node --check FAILED with syntax error:")
            print(res.stderr)
            return False
    except Exception as err:
        print(f"[RENDERED_JS] Failed to execute node --check: {err}")
        return False

if __name__ == "__main__":
    ok = extract_and_check_rendered_js()
    sys.exit(0 if ok else 1)
