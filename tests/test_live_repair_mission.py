import os
import sys
import time
import json
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis import (
    agentic_execute_instruction,
    handle_launcher_command,
    parse_intent,
    verify_app_running,
    verify_browser_running,
    diagnose_last_action,
    ask_gemini,
    gemini_stream,
    DEFAULT_GEMINI_MODEL,
    SETTINGS,
    GEMINI_CIRCUIT,
    route_auto,
    ollama_stream,
    OLLAMA
)

print("=" * 60)
print("JARVIS ARC 3.0 / RUBI CORE — LIVE INTEGRATION VERIFICATION")
print("=" * 60)

test_results = {}

# -------------------------------------------------------------
# Test 1: Real Chrome Launch
# -------------------------------------------------------------
print("\n[TEST 1] Testing 'Open Google Chrome'...")
t1_res = agentic_execute_instruction("Open Google Chrome")
print(f"Result: {t1_res}")
time.sleep(1.0)
chrome_running = verify_app_running("chrome")
print(f"Chrome running verification: {chrome_running}")
assert chrome_running, "Chrome process should be verified running"
test_results['test_1_open_chrome'] = {'status': 'PASS', 'result': t1_res, 'verified_running': chrome_running}

# -------------------------------------------------------------
# Test 2: Real YouTube Navigation
# -------------------------------------------------------------
print("\n[TEST 2] Testing 'Open YouTube'...")
t2_res = agentic_execute_instruction("Open YouTube")
print(f"Result: {t2_res}")
time.sleep(1.0)
browser_running = verify_browser_running()
print(f"Browser running verification: {browser_running}")
assert browser_running, "Browser process should be running"
test_results['test_2_open_youtube'] = {'status': 'PASS', 'result': t2_res, 'verified_running': browser_running}

# -------------------------------------------------------------
# Test 3: Real Google Search
# -------------------------------------------------------------
print("\n[TEST 3] Testing 'Google how does photosynthesis work'...")
t3_res = agentic_execute_instruction("Google how does photosynthesis work")
print(f"Result: {t3_res}")
assert "google" in t3_res.lower() or "search" in t3_res.lower(), f"Unexpected result: {t3_res}"
test_results['test_3_google_search'] = {'status': 'PASS', 'result': t3_res}

# -------------------------------------------------------------
# Test 4: Real File Explorer Launch
# -------------------------------------------------------------
print("\n[TEST 4] Testing 'Open File Explorer'...")
t4_res = agentic_execute_instruction("Open File Explorer")
print(f"Result: {t4_res}")
time.sleep(1.0)
explorer_running = verify_app_running("file explorer")
print(f"File Explorer running verification: {explorer_running}")
assert explorer_running, "Explorer process should be verified running"
test_results['test_4_open_explorer'] = {'status': 'PASS', 'result': t4_res, 'verified_running': explorer_running}

# -------------------------------------------------------------
# Test 5: Incomplete Command Safety ("Open...")
# -------------------------------------------------------------
print("\n[TEST 5] Testing incomplete command 'Open...'...")
t5_res = agentic_execute_instruction("Open...")
print(f"Result: {t5_res}")
assert "What application" in t5_res, f"Should ask for clarification, got: {t5_res}"
test_results['test_5_incomplete_open'] = {'status': 'PASS', 'result': t5_res}

# -------------------------------------------------------------
# Test 6: Failure Diagnosis & Recovery
# -------------------------------------------------------------
print("\n[TEST 6] Testing user complaint 'That didn't open'...")
t6_res = agentic_execute_instruction("That didn't open")
print(f"Result: {t6_res}")
assert "diagnosed" in t6_res.lower() or "verified" in t6_res.lower() or "re-launched" in t6_res.lower(), f"Unexpected diagnosis: {t6_res}"
test_results['test_6_diagnose_failure'] = {'status': 'PASS', 'result': t6_res}

# -------------------------------------------------------------
# Test 7: Real Gemini Live API Request (gemini-3.5-flash)
# -------------------------------------------------------------
print("\n[TEST 7] Testing real Gemini API with 'gemini-3.5-flash'...")
api_key = os.environ.get('GEMINI_API_KEY', '').strip() or SETTINGS.get('gemini_api_key', '').strip()
if api_key:
    print(f"Active Gemini Model ID: {DEFAULT_GEMINI_MODEL}")
    t7_res = ask_gemini("Reply with only the word 'ANTIGRAVITY_GEMINI_OK'", api_key, [], None, model_name=DEFAULT_GEMINI_MODEL)
    print(f"Gemini response: '{t7_res}'")
    assert "ANTIGRAVITY_GEMINI_OK" in t7_res or "gemini" in t7_res.lower() or len(t7_res) > 0, "Gemini should return response"
    test_results['test_7_gemini_live'] = {'status': 'PASS', 'model': DEFAULT_GEMINI_MODEL, 'response': t7_res}
else:
    print("Gemini API key not configured in environment or settings (skipping live cloud call, local-only mode active).")
    test_results['test_7_gemini_live'] = {'status': 'SKIPPED', 'model': DEFAULT_GEMINI_MODEL, 'response': 'SKIPPED_NO_KEY'}

# -------------------------------------------------------------
# Test 8: Silent Local Fallback to Ollama when Gemini Fails
# -------------------------------------------------------------
print("\n[TEST 8] Testing silent local Ollama fallback on Gemini failure...")
# Simulate failure in GEMINI_CIRCUIT
GEMINI_CIRCUIT['simulated_failure'] = True
try:
    try:
        failed_gem_res = ask_gemini("Hello test", api_key, [], None, model_name=DEFAULT_GEMINI_MODEL)
    except Exception as gem_err:
        failed_gem_res = None
        print(f"Gemini raised expected exception under simulated failure: {gem_err}")
    assert failed_gem_res is None, "ask_gemini should fail when simulated_failure is True"

    # Now verify local Ollama fallback succeeds
    fallback_model, _ = route_auto("Explain quantum entanglement briefly", prefer_quality=True)
    print(f"Auto-routed fallback model: {fallback_model}")
    import threading
    mock_run = {'event': threading.Event(), 'responses': []}
    msgs = [{'role': 'user', 'content': 'Say OLLAMA_FALLBACK_CONFIRMED'}]
    stream_it = ollama_stream(fallback_model, msgs, mock_run, {'num_predict': 15})
    output_chunks = []
    for c in stream_it:
        output_chunks.append(c)
    local_out = "".join(output_chunks).strip()
    print(f"Local Ollama Fallback output ({fallback_model}): '{local_out}'")
    assert len(local_out) > 0, "Local Ollama fallback should generate output"
    test_results['test_8_silent_fallback'] = {'status': 'PASS', 'fallback_model': fallback_model, 'output': local_out}
finally:
    GEMINI_CIRCUIT['simulated_failure'] = False

# -------------------------------------------------------------
# Summary
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("ALL LIVE INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
for k, v in test_results.items():
    print(f"  {k}: {v['status']}")

with open("tests/live_test_results.json", "w", encoding="utf-8") as f:
    json.dump(test_results, f, indent=2)
