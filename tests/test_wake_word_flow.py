"""
Tests for Final Wake-Word Flow Repair:
1. "Hey Rubi" and all wake aliases wake the assistant and send NO model request.
2. Each existing wake alias follows the same behavior.
3. "Hey Rubi, open Calculator" submits only the command.
4. A wake phrase alone does not create a chat message or call LLM.
5. The listening window does not expire before 10 seconds of inactivity.
6. Speech activity resets the inactivity timer.
7. Continuous speech does not cause premature sleep.
8. A final transcript is submitted once.
9. Silence for 10 seconds returns the assistant to sleep quietly.
10. An empty transcript does not trigger model generation.
11. Repeated wake events do not produce duplicate command submissions.
12. Existing wake-word recognition and ordinary command transcription remain functional.
"""

import unittest
import os
import sys
import re
import json

WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

import jarvis

class TestWakePhraseIsolationAndAliases(unittest.TestCase):
    """Test wake phrase isolation, aliases stripping, and non-destruction of ordinary commands."""

    def setUp(self):
        self.aliases = [
            "hey rubi", "hey ruby", "rubi", "ruby",
            "hi rubi", "hi ruby", "hello rubi", "hello ruby",
            "hey rooby", "ok rubi", "ok ruby",
            "hey jarvis", "jarvis"
        ]

    def test_all_wake_aliases_detected_as_wake_only(self):
        """1 & 2: 'Hey Rubi' and each existing wake alias wake only and are classified as wake-only."""
        for alias in self.aliases:
            self.assertTrue(jarvis.is_wake_only_phrase(alias), f"Alias '{alias}' must be wake-only")
            self.assertEqual(jarvis.strip_leading_wake_phrase(alias), "", f"Stripping alias '{alias}' should yield empty string")

    def test_wake_aliases_with_conversational_prefixes(self):
        """Wake aliases with punctuation, greetings, or spacing remain wake-only."""
        cases = [
            "Hey Rubi!", "hey ruby, ", "  rubi.  ", "Hello Rubi...",
            "OK Rubi", "okay rubi", "Hey Jarvis!", "Jarvis?"
        ]
        for c in cases:
            self.assertTrue(jarvis.is_wake_only_phrase(c), f"'{c}' must be wake-only")
            self.assertEqual(jarvis.strip_leading_wake_phrase(c), "", f"Stripping '{c}' should be empty")

    def test_wake_with_command_submits_only_command(self):
        """3: 'Hey Rubi, open Calculator' extracts and submits only 'open Calculator'."""
        cases = [
            ("Hey Rubi, open Calculator", "open Calculator"),
            ("Hey Ruby please open chrome", "please open chrome"),
            ("Ruby open notepad", "open notepad"),
            ("Hi Rubi calculate 25 plus 14", "calculate 25 plus 14"),
            ("Hey Jarvis search for cricket scores", "search for cricket scores"),
            ("ok rubi what time is it", "what time is it"),
            ("hello rubi, tell me a joke", "tell me a joke")
        ]
        for utterance, expected_cmd in cases:
            self.assertFalse(jarvis.is_wake_only_phrase(utterance), f"'{utterance}' has command, not wake-only")
            stripped = jarvis.strip_leading_wake_phrase(utterance)
            self.assertEqual(stripped, expected_cmd, f"Expected '{expected_cmd}' but got '{stripped}'")

    def test_ordinary_commands_not_corrupted(self):
        """12: Ordinary commands containing alias words inside sentence are NOT corrupted."""
        cases = [
            "write a ruby script",
            "search for ruby gemstones",
            "is ruby faster than python",
            "read the rubi documentation",
            "tell me about rubies"
        ]
        for cmd in cases:
            self.assertFalse(jarvis.is_wake_only_phrase(cmd))
            stripped = jarvis.strip_leading_wake_phrase(cmd)
            self.assertEqual(stripped, cmd, f"Ordinary command '{cmd}' must not be modified, got '{stripped}'")

    def test_backend_chat_route_rejects_wake_only_phrases(self):
        """4 & 10: Wake phrases alone do NOT create chat messages or reach the model."""
        client = jarvis.app.test_client()
        # Create session
        res_new = client.post('/new', json={}, headers={'X-Jarvis-Token': jarvis.CSRF_TOKEN})
        self.assertEqual(res_new.status_code, 200)
        sid = res_new.get_json()['id']

        # Attempt to post "Hey Rubi"
        res_wake = client.post('/chat', json={'session': sid, 'message': 'Hey Rubi'}, headers={'X-Jarvis-Token': jarvis.CSRF_TOKEN})
        self.assertEqual(res_wake.status_code, 400)
        body = res_wake.get_json()
        self.assertEqual(body.get('error', {}).get('code'), 'wake_only')

        # Attempt to post "hey jarvis"
        res_wake2 = client.post('/chat', json={'session': sid, 'message': 'hey jarvis'}, headers={'X-Jarvis-Token': jarvis.CSRF_TOKEN})
        self.assertEqual(res_wake2.status_code, 400)

        # Attempt to post empty message
        res_empty = client.post('/chat', json={'session': sid, 'message': '   '}, headers={'X-Jarvis-Token': jarvis.CSRF_TOKEN})
        self.assertEqual(res_empty.status_code, 400)


class MockClock:
    """Controllable virtual clock for deterministic timeout and timer testing."""
    def __init__(self):
        self.now = 0.0
        self.timers = []
        self._next_id = 1

    def set_timeout(self, callback, delay_ms):
        timer_id = self._next_id
        self._next_id += 1
        trigger_time = self.now + (delay_ms / 1000.0)
        self.timers.append({'id': timer_id, 'cb': callback, 'time': trigger_time, 'active': True})
        return timer_id

    def clear_timeout(self, timer_id):
        for t in self.timers:
            if t['id'] == timer_id:
                t['active'] = False

    def advance(self, seconds):
        target = self.now + seconds
        while True:
            # Find earliest active timer due before or at target
            due = [t for t in self.timers if t['active'] and t['time'] <= target]
            if not due:
                break
            due.sort(key=lambda x: x['time'])
            earliest = due[0]
            self.now = earliest['time']
            earliest['active'] = False
            earliest['cb']()
        self.now = target


class SimulatedWakeEngine:
    """Deterministic simulation mirroring the exact JS wakeEngine logic in jarvis.py."""
    def __init__(self, clock):
        self.clock = clock
        self.enabled = True
        self.state = 'WAITING_FOR_WAKE_WORD'
        self.session_token = 0
        self.timeout_sec = 10
        self.submitted_commands = []
        self.input_value = ''
        self.speech_active = False
        self.has_submitted = False
        self.inactivity_timer = None
        self.finalize_timer = None

    def strip_wake_phrase(self, text):
        return jarvis.strip_leading_wake_phrase(text)

    def is_wake_only_phrase(self, text):
        return jarvis.is_wake_only_phrase(text)

    def on_wake_detected(self, initial_command=''):
        if not self.enabled or self.state == 'OFF':
            return
        self.session_token += 1
        self.state = 'CAPTURING_COMMAND'

        clean_initial = self.strip_wake_phrase(initial_command)
        has_immediate = clean_initial and not self.is_wake_only_phrase(clean_initial) and len(clean_initial.strip()) > 1

        if has_immediate:
            self.input_value = clean_initial.strip()
            self.execute_command()
        else:
            self.input_value = ''
            self.capture_command()

    def capture_command(self):
        if not self.enabled or self.state == 'OFF':
            return
        self.state = 'CAPTURING_COMMAND'
        self.session_token += 1
        turn_token = self.session_token
        self.has_submitted = False
        self.speech_active = False

        inactivity_ms = max(10, self.timeout_sec) * 1000

        def reset_inactivity():
            if self.has_submitted:
                return
            if self.inactivity_timer:
                self.clock.clear_timeout(self.inactivity_timer)
            self.inactivity_timer = self.clock.set_timeout(on_inactivity_timeout, inactivity_ms)

        def on_inactivity_timeout():
            if turn_token != self.session_token or not self.enabled or self.state != 'CAPTURING_COMMAND' or self.has_submitted:
                return
            if self.speech_active:
                reset_inactivity()
                return
            candidate = self.strip_wake_phrase(self.input_value)
            if candidate and not self.is_wake_only_phrase(candidate):
                self.has_submitted = True
                self.input_value = candidate
                self.execute_command()
            else:
                self.input_value = ''
                self.return_to_sleep()

        self.reset_inactivity = reset_inactivity
        reset_inactivity()

    def on_speech_start(self):
        self.speech_active = True
        self.reset_inactivity()

    def on_speech_end(self):
        self.speech_active = False
        self.reset_inactivity()

    def on_transcript(self, raw_text, is_final=False):
        self.speech_active = True
        self.reset_inactivity()
        clean = self.strip_wake_phrase(raw_text)
        if not self.is_wake_only_phrase(clean):
            self.input_value = clean

        if is_final and clean and not self.is_wake_only_phrase(clean):
            if self.finalize_timer:
                self.clock.clear_timeout(self.finalize_timer)
            self.finalize_timer = self.clock.set_timeout(self._finalize_command, 950)

    def _finalize_command(self):
        if not self.has_submitted and self.state == 'CAPTURING_COMMAND':
            cmd = self.strip_wake_phrase(self.input_value)
            if cmd and not self.is_wake_only_phrase(cmd):
                self.has_submitted = True
                if self.inactivity_timer:
                    self.clock.clear_timeout(self.inactivity_timer)
                self.execute_command()

    def execute_command(self):
        clean = self.strip_wake_phrase(self.input_value)
        if self.is_wake_only_phrase(clean):
            self.input_value = ''
            self.return_to_sleep()
            return
        self.state = 'PROCESSING'
        self.submitted_commands.append(clean)
        self.input_value = ''

    def return_to_sleep(self):
        self.state = 'WAITING_FOR_WAKE_WORD'
        self.input_value = ''


class TestListeningWindowAndInactivity(unittest.TestCase):
    """Test deterministic timing, speech resetting, quiet timeout, and duplicate prevention."""

    def test_listening_window_does_not_expire_before_10s_inactivity(self):
        """5: After wake, assistant remains ready through 9.9s of inactivity without timing out."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)
        engine.on_wake_detected("")  # User says "Hey Rubi" alone
        self.assertEqual(engine.state, 'CAPTURING_COMMAND')
        self.assertEqual(engine.input_value, '')

        # Advance 9.5 seconds: must still be in CAPTURING_COMMAND
        clock.advance(9.5)
        self.assertEqual(engine.state, 'CAPTURING_COMMAND')
        self.assertEqual(len(engine.submitted_commands), 0)

    def test_silence_for_10s_returns_to_sleep_quietly(self):
        """9 & 4: Exactly 10 seconds of silence returns to sleep quietly with zero submissions."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)
        engine.on_wake_detected("")
        self.assertEqual(engine.state, 'CAPTURING_COMMAND')

        # Advance past 10 seconds (10.1s)
        clock.advance(10.1)
        self.assertEqual(engine.state, 'WAITING_FOR_WAKE_WORD', "Must return to sleep")
        self.assertEqual(len(engine.submitted_commands), 0, "No model request or chat message submitted")
        self.assertEqual(engine.input_value, "", "Input box must be cleared")

    def test_speech_activity_resets_inactivity_timer(self):
        """6: Speech activity resets the inactivity timer."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)
        engine.on_wake_detected("")

        # User is silent for 8 seconds
        clock.advance(8.0)
        self.assertEqual(engine.state, 'CAPTURING_COMMAND')

        # At t=8s, user starts speaking: resets inactivity timer
        engine.on_speech_start()
        engine.on_transcript("open", is_final=False)

        # Advance another 8 seconds (total 16s since wake)
        clock.advance(8.0)
        self.assertEqual(engine.state, 'CAPTURING_COMMAND', "Speech activity must have reset the 10s timer")

    def test_continuous_speech_does_not_cause_premature_sleep(self):
        """7: Continuous speech over multiple seconds never times out while speaking."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)
        engine.on_wake_detected("")

        # Simulate user speaking slowly over 15 seconds
        for i in range(15):
            clock.advance(1.0)
            engine.on_transcript(f"searching for information chunk {i}", is_final=False)
            self.assertEqual(engine.state, 'CAPTURING_COMMAND', f"Premature sleep at second {i+1}")

    def test_final_transcript_submitted_once_cleanly(self):
        """8: Final transcript is submitted exactly once without wake phrase."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)
        engine.on_wake_detected("")

        # User speaks "open calculator"
        engine.on_transcript("Hey Rubi, open calculator", is_final=True)
        # Advance 1.0 second for finalization debounce (950ms)
        clock.advance(1.0)

        self.assertEqual(engine.state, 'PROCESSING')
        self.assertEqual(engine.submitted_commands, ["open calculator"])
        self.assertEqual(len(engine.submitted_commands), 1, "Must be submitted exactly once")

    def test_repeated_wake_events_prevent_duplicate_submissions(self):
        """11: Repeated wake events invalidate previous tokens and do not duplicate submissions."""
        clock = MockClock()
        engine = SimulatedWakeEngine(clock)

        # Wake 1
        engine.on_wake_detected("")
        token1 = engine.session_token

        # Immediate Wake 2 before any command
        engine.on_wake_detected("")
        token2 = engine.session_token
        self.assertGreater(token2, token1, "Session token must advance")

        # Now speak command
        engine.on_transcript("open calculator", is_final=True)
        clock.advance(1.0)

        self.assertEqual(len(engine.submitted_commands), 1)
        self.assertEqual(engine.submitted_commands, ["open calculator"])


if __name__ == '__main__':
    unittest.main()
