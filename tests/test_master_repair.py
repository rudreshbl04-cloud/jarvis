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
    dispatch_action,
    quick_command
)

class TestMasterRepair(unittest.TestCase):
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
    # 1. Chained Launcher Commands (DEF-07)
    # -------------------------------------------------------------------------
    def test_chained_launcher_then(self):
        steps = split_launcher_chain("Open YouTube then Notepad")
        self.assertIsNotNone(steps)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0], ('open_target', {'target': 'YouTube'}))
        self.assertEqual(steps[1], ('open_target', {'target': 'Notepad'}))

    def test_chained_launcher_and_then(self):
        steps = split_launcher_chain("Open YouTube and then Notepad")
        self.assertIsNotNone(steps)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0], ('open_target', {'target': 'YouTube'}))
        self.assertEqual(steps[1], ('open_target', {'target': 'Notepad'}))

    def test_chained_launcher_list(self):
        steps = split_launcher_chain("Open Chrome, Notepad, Photos, Downloads, and Documents")
        self.assertIsNotNone(steps)
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0], ('open_target', {'target': 'Chrome'}))
        self.assertEqual(steps[1], ('open_target', {'target': 'Notepad'}))
        self.assertEqual(steps[2], ('open_target', {'target': 'Photos'}))
        self.assertEqual(steps[3], ('open_target', {'target': 'Downloads'}))
        self.assertEqual(steps[4], ('open_target', {'target': 'Documents'}))

    # -------------------------------------------------------------------------
    # 2. Generic Search (DEF-08)
    # -------------------------------------------------------------------------
    def test_generic_search(self):
        steps = split_launcher_chain("Search for cricket score")
        self.assertIsNotNone(steps)
        self.assertEqual(steps[0], ('web_search', {'engine': 'google', 'query': 'cricket score'}))

        intent, details = parse_intent("Search for cricket score")
        self.assertEqual(intent, 'web_search')
        self.assertEqual(details['query'], 'cricket score')

    # -------------------------------------------------------------------------
    # 3. Contextual Close "Close that" (DEF-09)
    # -------------------------------------------------------------------------
    def test_close_that_intent(self):
        for phrase in ("Close that", "close it", "close this", "close window"):
            intent, _ = parse_intent(phrase)
            self.assertEqual(intent, 'close_window', f"Failed for {phrase}")
            res = dispatch_action(phrase)
            self.assertIn("Safety Confirmation Required", res)
            self.assertIn("active window", res)

    # -------------------------------------------------------------------------
    # 4. Mixed Kannada-English Commands (DEF-10)
    # -------------------------------------------------------------------------
    def test_kannada_commands(self):
        # Open commands
        steps = split_launcher_chain("YouTube open maadu")
        self.assertIsNotNone(steps)
        self.assertEqual(steps[0], ('open_target', {'target': 'YouTube'}))

        # Search commands
        steps_g1 = split_launcher_chain("Google alli search maadu")
        self.assertIsNotNone(steps_g1)
        self.assertEqual(steps_g1[0], ('open_target', {'target': 'google'}))

        steps_g2 = split_launcher_chain("Google alli search maadu cricket score")
        self.assertIsNotNone(steps_g2)
        self.assertEqual(steps_g2[0], ('web_search', {'engine': 'google', 'query': 'cricket score'}))

        steps_g3 = split_launcher_chain("cricket score Google alli search maadu")
        self.assertIsNotNone(steps_g3)
        self.assertEqual(steps_g3[0], ('web_search', {'engine': 'google', 'query': 'cricket score'}))

    # -------------------------------------------------------------------------
    # 5. Page Navigation Commands (DEF-11)
    # -------------------------------------------------------------------------
    def test_page_navigation(self):
        for cmd, expected in [
            ("page down", "Paged down"),
            ("page up", "Paged up"),
            ("go to top", "Scrolled to top"),
            ("go to bottom", "Scrolled to bottom")
        ]:
            res = dispatch_action(cmd)
            self.assertIn(expected, res)

    # -------------------------------------------------------------------------
    # 6. Natural Music Commands (Kesariya & Canadian Song)
    # -------------------------------------------------------------------------
    def test_natural_music_phrasings(self):
        res1 = dispatch_action("Play Kesariya on YouTube")
        self.assertIn("Opened YouTube search for Kesariya", res1)

        res2 = dispatch_action("I want to listen to a new Canadian song")
        self.assertTrue("Opened YouTube search" in res2 or "opened it on YouTube" in res2)

    # -------------------------------------------------------------------------
    # 7. Backend Integration /chat Endpoint Execution
    # -------------------------------------------------------------------------
    def test_chat_chained_launcher_execution(self):
        req = urllib.request.Request(
            f"{self.base_url}/chat",
            data=json.dumps({
                "session": self.sid,
                "model": "fast",
                "message": "Open YouTube then Notepad"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req, timeout=15) as r:
            body = r.read().decode('utf-8', errors='ignore')
            self.assertIn("YouTube", body)
            self.assertIn("Notepad", body)

if __name__ == '__main__':
    unittest.main()
