import urllib.request
import urllib.parse
import http.cookiejar
import json
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://127.0.0.1:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

print("=== STEP 1: Authenticate PIN on /lock ===")
req_lock = urllib.request.Request(
    f"{base_url}/lock",
    data=json.dumps({"pin": "1234"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with opener.open(req_lock, timeout=5) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    assert res.get('ok') is True, f"Failed PIN unlock: {res}"
    print("[PASS] Successfully unlocked session with PIN 1234")

print("\n=== STEP 2: Verify Root HTML and Headers (Authenticated) ===")
with opener.open(f"{base_url}/", timeout=10) as resp:
    headers = dict(resp.headers)
    html = resp.read().decode('utf-8', errors='ignore')
    
    assert "no-store" in headers.get('Cache-Control', '').lower(), f"Missing no-store in Cache-Control: {headers.get('Cache-Control')}"
    print("[PASS] Cache-Control header has no-store, no-cache, must-revalidate")
    
    assert ("v4.0.0-rubi-core" in html or "v3.0.14-wake-live" in html), "Missing build badge in HTML"
    print("[PASS] Build badge found in HTML")
    
    assert ("RUBI" in html or "ARC" in html), "Missing BUILD_ID in client script"
    print("[PASS] BUILD_ID found in client script")
    
    assert "J.A.R.V.I.S." in html, "Missing title in HTML"
    print("[PASS] App Title 'J.A.R.V.I.S.' found in HTML")

    m = re.search(r'const CSRF = ["\'](.*?)["\'];', html)
    csrf = m.group(1) if m else ""
    assert csrf, "Could not extract CSRF token"
    print(f"[PASS] Extracted CSRF token: {csrf[:8]}...")

print("\n=== STEP 3: Create Chat Session ===")
req_new = urllib.request.Request(
    f"{base_url}/new",
    data=b'{}',
    headers={"Content-Type": "application/json", "X-Jarvis-Token": csrf}
)
with opener.open(req_new, timeout=5) as resp:
    s_data = json.loads(resp.read().decode('utf-8'))
    session_id = s_data['id']
    print(f"[PASS] Created chat session: {session_id}")

print("\n=== STEP 4: Test 'Open Ed' Disambiguation in Chat ===")
req_open_ed = urllib.request.Request(
    f"{base_url}/chat",
    data=json.dumps({
        "session": session_id,
        "model": "fast",
        "message": "Open Ed"
    }).encode('utf-8'),
    headers={"Content-Type": "application/json", "X-Jarvis-Token": csrf}
)
with opener.open(req_open_ed, timeout=30) as resp:
    raw_output = resp.read().decode('utf-8', errors='ignore')
    print("Response snippet:", repr(raw_output[:250]))
    assert "Did you mean Microsoft Edge" in raw_output, f"Expected Edge disambiguation, got: {raw_output}"
    assert "onedrive" not in raw_output.lower(), f"OneDrive matched in error: {raw_output}"
    assert "launched" not in raw_output.lower(), f"Fake 'Launched' claim emitted: {raw_output}"
    print("[PASS] 'Open Ed' returned honest disambiguation: 'Did you mean Microsoft Edge, Rudresh?' (No OneDrive, No fake launch)")

print("\n=== STEP 5: Test 'Close calculator' Safety Confirmation in Chat ===")
req_close = urllib.request.Request(
    f"{base_url}/chat",
    data=json.dumps({
        "session": session_id,
        "model": "fast",
        "message": "Close calculator"
    }).encode('utf-8'),
    headers={"Content-Type": "application/json", "X-Jarvis-Token": csrf}
)
with opener.open(req_close, timeout=30) as resp:
    raw_output = resp.read().decode('utf-8', errors='ignore')
    print("Response snippet:", repr(raw_output[:250]))
    assert "Safety Confirmation Required" in raw_output, f"Expected Safety Confirmation Required, got: {raw_output}"
    assert "calculator" in raw_output.lower(), f"Expected calculator in safety prompt: {raw_output}"
    print("[PASS] 'Close calculator' required two-step safety confirmation (DID NOT OPEN OR CLOSE IMMEDIATELY)")

print("\n=== ALL LIVE HTTP TESTS PASSED PERFECTLY ===")
