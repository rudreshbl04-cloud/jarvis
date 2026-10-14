import unittest
import urllib.request
import urllib.parse
import json
import re
import time
import os
import sys

# Ensure project root is in path
WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from jarvis import (
    split_launcher_chain,
    is_launcher_command,
    parse_intent,
    handle_launcher_command,
    quick_command,
    launch_target
)

class TestDef06LauncherRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000"
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        # Acquire CSRF token
        html = cls.opener.open(f"{cls.base_url}/").read().decode('utf-8')
        m = re.search(r'const CSRF = ["\'](.*?)["\'];', html)
        assert m, "CSRF token required"
        cls.csrf = m.group(1)

    def setUp(self):
        # Create fresh session for each test
        req = urllib.request.Request(
            f"{self.base_url}/new",
            data=b'{}',
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req, timeout=5) as r:
            self.sid = json.loads(r.read().decode('utf-8'))['id']

    # -------------------------------------------------------------------------
    # Layer 1: Parser Tests
    # -------------------------------------------------------------------------
    def test_youtube_music_phrasings_parser(self):
        cases = [
            ("Open YouTube and play a song.", "a song"),
            ("Open YouTube and play a song", "a song"),
            ("Open YouTube and play song", ""),
            ("open youtube and play music", "music"),
            ("open youtube and play believer", "believer"),
            ("open youtube and play shape of you", "shape of you"),
            ("play a song on youtube", "a song"),
            ("play shape of you on youtube", "shape of you"),
            ("search youtube for coldplay", "coldplay"),
            ("look up interstellar trailer on youtube", "interstellar trailer"),
            ("go to youtube and play jazz", "jazz")
        ]
        for phrase, expected_q in cases:
            steps = split_launcher_chain(phrase)
            self.assertIsNotNone(steps, f"Failed to parse YouTube phrase: '{phrase}'")
            self.assertEqual(steps[0][0], 'web_search')
            self.assertEqual(steps[0][1]['engine'], 'youtube')
            if expected_q:
                self.assertEqual(steps[0][1]['query'], expected_q)

    def test_google_search_phrasings_parser(self):
        cases = [
            ("Open Google and search Python tutorials", "Python tutorials"),
            ("Open Google and search X.", "X"),
            ("Open Google and search X", "X"),
            ("Open Google and search for the weather", "the weather"),
            ("Search Google for Python tutorials", "Python tutorials"),
            ("search on google for python", "python"),
            ("search on google machine learning", "machine learning"),
            ("go to google and search Python", "Python"),
            ("look up quantum physics on google", "quantum physics"),
            ("google artificial intelligence", "artificial intelligence")
        ]
        for phrase, expected_q in cases:
            steps = split_launcher_chain(phrase)
            self.assertIsNotNone(steps, f"Failed to parse Google phrase: '{phrase}'")
            self.assertEqual(steps[0][0], 'web_search')
            self.assertEqual(steps[0][1]['engine'], 'google')
            self.assertEqual(steps[0][1]['query'], expected_q)

    def test_whatsapp_control_parser(self):
        for phrase in ["Open WhatsApp", "open whatsapp", "launch whatsapp"]:
            steps = split_launcher_chain(phrase)
            self.assertIsNotNone(steps, f"Failed to parse WhatsApp phrase: '{phrase}'")
            self.assertEqual(steps[0][0], 'open_target')
            self.assertIn("whatsapp", steps[0][1]['target'].lower())

    # -------------------------------------------------------------------------
    # Layer 2: Dispatcher & Handler Execution Tests
    # -------------------------------------------------------------------------
    def test_youtube_music_dispatcher_execution(self):
        res = handle_launcher_command("Open YouTube and play a song.")
        self.assertIsNotNone(res)
        self.assertIn("Opened YouTube to play music", res)

        res2 = handle_launcher_command("Open YouTube and play shape of you")
        self.assertIsNotNone(res2)
        self.assertIn("Opened YouTube search for shape of you", res2)

    def test_google_search_dispatcher_execution(self):
        res = handle_launcher_command("Open Google and search Python tutorials")
        self.assertIsNotNone(res)
        self.assertIn("Opened Google search for Python tutorials", res)

        res2 = handle_launcher_command("Open Google and search X.")
        self.assertIsNotNone(res2)
        self.assertEqual(res2, "Opened Google search for X.")

    def test_whatsapp_dispatcher_execution(self):
        res = handle_launcher_command("Open WhatsApp")
        self.assertIsNotNone(res)
        self.assertIn("Opened WhatsApp", res)

    # -------------------------------------------------------------------------
    # Layer 3: Live Backend Integration (/chat endpoint in voice mode)
    # -------------------------------------------------------------------------
    def _send_chat(self, msg, voice=True):
        req = urllib.request.Request(
            f"{self.base_url}/chat",
            data=json.dumps({
                "session": self.sid,
                "message": msg,
                "model": "fast",
                "is_voice_mode": voice
            }).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req, timeout=30) as r:
            return r.read().decode('utf-8', errors='replace')

    def test_live_chat_youtube_music(self):
        reply = self._send_chat("Open YouTube and play a song.", voice=True)
        self.assertIn("Opened YouTube to play music", reply)
        self.assertNotIn("I will open. What's next?", reply)

    def test_live_chat_google_search(self):
        reply = self._send_chat("Open Google and search Python tutorials", voice=True)
        self.assertIn("Opened Google search for Python tutorials", reply)
        self.assertNotIn("I will open. What's next?", reply)

    def test_live_chat_whatsapp_control(self):
        reply = self._send_chat("Open WhatsApp", voice=True)
        self.assertIn("Opened WhatsApp", reply)

    # -------------------------------------------------------------------------
    # Layer 4: Real Windows Browser Observable Activity Log Verification
    # -------------------------------------------------------------------------
    def test_observable_activity_logging(self):
        act_file = os.path.join(WORKSPACE, "activity.json")
        self.assertTrue(os.path.exists(act_file))
        with open(act_file, 'r', encoding='utf-8') as f:
            act_list = json.load(f)
        
        # Check that open_url activities were logged with real browser PIDs
        recent_urls = [a for a in act_list[-20:] if a.get('tool') == 'open_url']
        self.assertGreater(len(recent_urls), 0, "Expected open_url activity log entries")
        last_url_log = recent_urls[-1]
        self.assertEqual(last_url_log['state'], 'done')
        self.assertIn('https://', last_url_log['result'])

if __name__ == "__main__":
    unittest.main()
