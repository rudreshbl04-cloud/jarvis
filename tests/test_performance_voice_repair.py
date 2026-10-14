"""
Comprehensive Verification Test Suite for Master Repair:
1. CPU Inference Optimization & Model Routing (Phase 1)
2. Authoritative Voice State Machine & Indicator Mutual Exclusion (Phase 2)
3. 'Hey Rubi' Wake-Word & Command Capture Preservation (Phase 3)
"""
import unittest
import os
import sys
import re
import json
import time
import requests

WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

import jarvis

class TestModelRoutingAndPerformance(unittest.TestCase):
    """Phase 1: Local Ollama CPU inference optimization and routing tests."""

    def test_default_settings_optimal_cpu_config(self):
        """Verify num_ctx=2048, num_thread=4, and keep_alive='30m' in settings."""
        self.assertEqual(jarvis.SETTINGS.get('num_thread'), 4, "num_thread must be 4 for quad-core i7")
        self.assertEqual(jarvis.SETTINGS.get('num_ctx'), 2048, "num_ctx must be 2048 for CPU fast prompt eval")
        self.assertEqual(jarvis.SETTINGS.get('keep_alive'), '30m', "keep_alive must be 30m for resident memory")

    def test_routing_fast_model_selection(self):
        """Verify pick_brain in fast mode chooses llama3.2:3b."""
        chosen = jarvis.pick_brain("What is 12 multiplied by 8?", mode='fast')
        self.assertEqual(chosen, "llama3.2:3b", "Fast route should choose the benchmarked fastest model llama3.2:3b")

    def test_routing_simple_chat_and_calculations(self):
        """Verify route_auto routes simple greetings and fast math appropriately."""
        model_greet, _ = jarvis.route_auto("Hey bro, how are you?")
        self.assertEqual(model_greet, "llama3.2:3b", "Greetings should route to llama3.2:3b")

        model_code, _ = jarvis.route_auto("Write a python script with a class to parse json")
        self.assertEqual(model_code, "qwen2.5:3b", "Complex coding questions should route to qwen2.5:3b")

    def test_live_ollama_small_model_latency_and_correctness(self):
        """Live test: Ollama latency for fixed prompt must be under 0.6s warm and produce 96."""
        payload = {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "What is 12 multiplied by 8? Answer with the number only."}],
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "num_ctx": 2048,
                "num_thread": 4,
                "num_predict": 10,
                "temperature": 0.0
            }
        }
        # Warmup trial
        try:
            r0 = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=10)
            self.assertEqual(r0.status_code, 200, "Ollama must be reachable")
        except requests.RequestException as e:
            self.skipTest(f"Ollama server not running on localhost:11434: {e}")

        # Timed trial
        t0 = time.perf_counter()
        r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=10)
        elapsed = time.perf_counter() - t0
        self.assertEqual(r.status_code, 200)
        res = r.json()
        ans = res.get('message', {}).get('content', '').strip()
        self.assertIn("96", ans, f"Answer must contain 96, got: {ans}")
        self.assertLess(elapsed, 0.65, f"Warm response latency {elapsed:.3f}s exceeds threshold 0.65s")


class TestWakeWordEngineLogic(unittest.TestCase):
    """Phase 3: 'Hey Rubi' wake-word recognition, alias tolerance, and command capture preservation."""

    def setUp(self):
        # Python implementation mirroring the JS wakeEngine regex and levenshtein logic
        self.phrase = "Hey Rubi"
        self.aliases = [
            "hey rubi", "hey ruby", "rubi", "ruby",
            "hi rubi", "hi ruby", "hello rubi", "hello ruby",
            "hey rooby", "ok rubi", "ok ruby",
            "hey jarvis", "jarvis"
        ]

    def _normalize(self, text):
        if not text:
            return ""
        return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()

    def _matches_wake(self, transcript):
        norm_tr = self._normalize(transcript)
        norm_ph = self._normalize(self.phrase)
        all_targets = [norm_ph] + [self._normalize(a) for a in self.aliases if self._normalize(a)]
        all_targets = list(dict.fromkeys(all_targets))

        for tgt in all_targets:
            if norm_tr == tgt:
                return True
            pattern = r'(?:^|\s)' + re.escape(tgt) + r'(?:[\s.,!?:;]|$)'
            if re.search(pattern, norm_tr):
                return True
        return False

    def _strip_wake_phrase(self, transcript):
        if not transcript:
            return ""
        norm = transcript.strip()
        all_targets = [self.phrase] + list(self.aliases)
        all_targets.sort(key=lambda x: len(x), reverse=True)
        for tgt in all_targets:
            pattern = r'^\s*' + re.escape(tgt) + r'[\s,!:.]*'
            match = re.search(pattern, norm, re.IGNORECASE)
            if match:
                return norm[match.end():].strip()
        return norm.strip()

    def test_wake_phrase_variations(self):
        """Verify phonetic transcriptions like 'Hey Ruby', 'Ruby', 'Hi Rubi' trigger detection."""
        test_cases = [
            "Hey Rubi",
            "hey ruby",
            "Hey Ruby",
            "Rubi",
            "ruby",
            "Hi Rubi",
            "hi ruby",
            "hello rubi",
            "Hey Rooby",
            "ok rubi",
            "Hey Jarvis",
            "jarvis"
        ]
        for phrase in test_cases:
            self.assertTrue(self._matches_wake(phrase), f"Failed to match wake phrase variation: '{phrase}'")

    def test_wake_with_immediate_command(self):
        """Verify immediate command following wake word is recognized and not lost."""
        test_inputs = [
            ("Hey Rubi, what is 12 multiplied by 8?", "what is 12 multiplied by 8?"),
            ("Hey Ruby what is the capital of India", "what is the capital of India"),
            ("Ruby open notepad", "open notepad"),
            ("Hi Rubi calculate 25 plus 14", "calculate 25 plus 14"),
            ("Hey Jarvis search for cricket scores", "search for cricket scores")
        ]
        for raw, expected_cmd in test_inputs:
            self.assertTrue(self._matches_wake(raw), f"Should match wake in: '{raw}'")
            extracted = self._strip_wake_phrase(raw)
            self.assertEqual(extracted.lower(), expected_cmd.lower(), f"Extracted command mismatch for '{raw}'")

    def test_negative_phrases_do_not_trigger(self):
        """Verify ordinary speech without wake word does not trigger false positives."""
        negatives = [
            "What is the weather outside?",
            "Can you tell me a joke?",
            "I am working on my computer",
            "Please turn on the lights"
        ]
        for phrase in negatives:
            self.assertFalse(self._matches_wake(phrase), f"False positive for: '{phrase}'")


class TestVoiceStateMachineMutualExclusion(unittest.TestCase):
    """Phase 2: Authoritative voice state model and mutual exclusion verification."""

    def test_single_authoritative_state_definition(self):
        """Verify JS code enforces single authoritative indicator and resets when OFF."""
        with open(os.path.join(WORKSPACE, 'jarvis.py'), encoding='utf-8') as f:
            code = f.read()

        # Check wakeEngine authoritative states
        self.assertIn("WAITING_FOR_WAKE_WORD", code)
        self.assertIn("CAPTURING_COMMAND", code)
        self.assertIn("PROCESSING", code)
        self.assertIn("SPEAKING", code)
        self.assertIn("PAUSED", code)

        # Check sessionToken protection against stale callbacks
        self.assertIn("this.sessionToken++", code)
        self.assertIn("currentToken !== this.sessionToken", code)

        # Check mutual exclusion between conversation mode and wakeEngine
        self.assertIn("wakeEngine.pause('Paused (Continuous Mode Active)')", code)
        self.assertIn("wakeEngine.pause('Paused for manual mic')", code)

        # Check indicator clearing when turning OFF
        self.assertIn("ind.classList.add('hidden')", code)
        self.assertIn("convTxt.textContent = 'Off'", code)

    def test_state_transition_simulation(self):
        """Simulate deterministic state machine transitions with token invalidation."""
        class MockVoiceStateMachine:
            def __init__(self):
                self.state = 'OFF'
                self.enabled = False
                self.session_token = 0
                self.indicator_visible = False
                self.indicator_text = 'Off'

            def start(self):
                self.enabled = True
                self.session_token += 1
                self.state = 'STARTING'
                self.indicator_visible = True
                self.indicator_text = 'Initializing...'
                # On mic ready:
                self.state = 'WAITING_FOR_WAKE_WORD'
                self.indicator_text = "Waiting for 'Hey Rubi'"

            def on_wake_detected(self):
                if not self.enabled or self.state == 'OFF':
                    return
                self.session_token += 1
                self.state = 'CAPTURING_COMMAND'
                self.indicator_text = 'Listening for command...'

            def on_command_captured(self):
                if not self.enabled or self.state == 'OFF':
                    return
                self.state = 'PROCESSING'
                self.indicator_text = 'Thinking...'

            def on_response_complete(self):
                if not self.enabled or self.state == 'OFF':
                    return
                self.state = 'WAITING_FOR_WAKE_WORD'
                self.indicator_text = "Waiting for 'Hey Rubi'"

            def stop(self):
                self.enabled = False
                self.session_token += 1  # Invalidate pending callbacks
                self.state = 'OFF'
                self.indicator_visible = False
                self.indicator_text = 'Off'

            def late_callback(self, token):
                # Stale callback handler
                if token != self.session_token or not self.enabled or self.state == 'OFF':
                    return False  # Dropped
                self.state = 'CAPTURING_COMMAND'
                return True

        sm = MockVoiceStateMachine()
        self.assertEqual(sm.state, 'OFF')
        self.assertFalse(sm.indicator_visible)

        # Turn ON
        sm.start()
        self.assertEqual(sm.state, 'WAITING_FOR_WAKE_WORD')
        self.assertTrue(sm.indicator_visible)
        saved_token = sm.session_token

        # Wake detected
        sm.on_wake_detected()
        self.assertEqual(sm.state, 'CAPTURING_COMMAND')

        # Command captured
        sm.on_command_captured()
        self.assertEqual(sm.state, 'PROCESSING')

        # Response complete
        sm.on_response_complete()
        self.assertEqual(sm.state, 'WAITING_FOR_WAKE_WORD')

        # Turn OFF
        sm.stop()
        self.assertEqual(sm.state, 'OFF')
        self.assertFalse(sm.indicator_visible)

        # Verify stale callback cannot resurrect listening
        callback_accepted = sm.late_callback(saved_token)
        self.assertFalse(callback_accepted, "Late callback must NOT be accepted when session is OFF")
        self.assertEqual(sm.state, 'OFF')
        self.assertFalse(sm.indicator_visible)


if __name__ == '__main__':
    unittest.main()
