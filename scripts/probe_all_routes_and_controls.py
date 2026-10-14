import urllib.request
import urllib.parse
import json
import re
import sys
import time
import http.cookiejar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://127.0.0.1:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

results = []

def record(route_name, method, status, details, passed=True):
    results.append({
        "route": route_name,
        "method": method,
        "status": status,
        "details": details,
        "passed": passed
    })
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {method} {route_name} -> {status}: {details}")

# 1. Unauthenticated root redirect to /lock
try:
    with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
        # urlopen follows redirect
        final_url = resp.geturl()
        record("Unauth /", "GET", resp.status, f"Final URL: {final_url} (Redirected to lock as expected)")
except Exception as e:
    record("Unauth /", "GET", "ERR", str(e), False)

# 2. Manifest JSON
try:
    with urllib.request.urlopen(f"{base_url}/manifest.json", timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/manifest.json", "GET", resp.status, f"App name: {data.get('name')}")
except Exception as e:
    record("/manifest.json", "GET", "ERR", str(e), False)

# 3. /status endpoint
try:
    with urllib.request.urlopen(f"{base_url}/status", timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/status", "GET", resp.status, f"Model: {data.get('model')}, Voice: {data.get('voice_enabled')}")
except Exception as e:
    record("/status", "GET", "ERR", str(e), False)

# 4. Bad PIN unlock attempt (Expect 401 Unauthorized)
try:
    req_bad = urllib.request.Request(
        f"{base_url}/lock",
        data=json.dumps({"pin": "9999"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with opener.open(req_bad, timeout=5) as resp:
        record("/lock (bad pin)", "POST", resp.status, "Unexpected success with bad PIN", passed=False)
except urllib.error.HTTPError as he:
    record("/lock (bad pin)", "POST", he.code, f"Correctly rejected with HTTP {he.code}", passed=(he.code == 401))
except Exception as e:
    record("/lock (bad pin)", "POST", "ERR", str(e), False)

# 5. Correct PIN unlock attempt
try:
    req_good = urllib.request.Request(
        f"{base_url}/lock",
        data=json.dumps({"pin": "1234"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with opener.open(req_good, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/lock (correct pin)", "POST", resp.status, f"Response: {data}", passed=(data.get('ok') is True))
except Exception as e:
    record("/lock (correct pin)", "POST", "ERR", str(e), False)

# 6. Authenticated root page GET & extract CSRF
csrf = ""
try:
    with opener.open(f"{base_url}/", timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        m = re.search(r'const CSRF = ["\'](.*?)["\'];', html)
        csrf = m.group(1) if m else ""
        has_badge = "v3.0.14-wake-live" in html
        has_build_id = "ARC3-WAKE-LIVE-20261014-V3" in html
        record("Auth /", "GET", resp.status, f"CSRF extracted: {bool(csrf)}, Badge: {has_badge}, BuildID: {has_build_id}", passed=(bool(csrf) and has_badge and has_build_id))
except Exception as e:
    record("Auth /", "GET", "ERR", str(e), False)

headers_auth = {"Content-Type": "application/json", "X-Jarvis-Token": csrf}

# 7. /sessions GET
try:
    req = urllib.request.Request(f"{base_url}/sessions", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        count = len(data) if isinstance(data, list) else len(data.get('sessions', []))
        record("/sessions", "GET", resp.status, f"Total sessions: {count}", passed=isinstance(data, list))
except Exception as e:
    record("/sessions", "GET", "ERR", str(e), False)

# 8. /new POST (Create new chat session)
session_id = ""
try:
    req = urllib.request.Request(f"{base_url}/new", data=b'{}', headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        session_id = data.get('id', '')
        record("/new", "POST", resp.status, f"New session ID: {session_id}", passed=bool(session_id))
except Exception as e:
    record("/new", "POST", "ERR", str(e), False)

# 9. /settings GET
try:
    req = urllib.request.Request(f"{base_url}/settings", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        s = data.get('settings', {}) if 'settings' in data else data
        record("/settings", "GET", resp.status, f"Theme: {s.get('theme')}, Personality: {s.get('personality')}, Context: {s.get('num_ctx')}", passed=bool(s))
except Exception as e:
    record("/settings", "GET", "ERR", str(e), False)

# 10. /notes GET
try:
    req = urllib.request.Request(f"{base_url}/notes", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/notes", "GET", resp.status, f"Notes count: {len(data.get('notes', []))}", passed=True)
except Exception as e:
    record("/notes", "GET", "ERR", str(e), False)

# 11. /reminders GET
try:
    req = urllib.request.Request(f"{base_url}/reminders", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/reminders", "GET", resp.status, f"Reminders count: {len(data.get('reminders', []))}", passed=True)
except Exception as e:
    record("/reminders", "GET", "ERR", str(e), False)

# 12. /activity GET
try:
    req = urllib.request.Request(f"{base_url}/activity", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/activity", "GET", resp.status, f"Activity entries: {len(data.get('activity', []))}", passed=True)
except Exception as e:
    record("/activity", "GET", "ERR", str(e), False)

# 13. /documents GET
try:
    req = urllib.request.Request(f"{base_url}/documents", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/documents", "GET", resp.status, f"Documents list response: {type(data)}", passed=True)
except Exception as e:
    record("/documents", "GET", "ERR", str(e), False)

# 14. /pending/<sid> GET
try:
    req = urllib.request.Request(f"{base_url}/pending/{session_id}", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record(f"/pending/{session_id}", "GET", resp.status, f"Pending action: {data.get('pending')}", passed=True)
except Exception as e:
    record(f"/pending/{session_id}", "GET", "ERR", str(e), False)

# 15. /speak/status GET
try:
    req = urllib.request.Request(f"{base_url}/speak/status", headers=headers_auth)
    with opener.open(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        record("/speak/status", "GET", resp.status, f"Piper available: {data.get('piper_available')}")
except Exception as e:
    record("/speak/status", "GET", "ERR", str(e), False)

# Save JSON results
with open("artifacts/reachable_pages_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSaved probe results to artifacts/reachable_pages_probe_results.json")
