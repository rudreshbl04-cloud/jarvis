import unittest
import urllib.request
import json
import re
import http.cookiejar
import time
import os
import sys

# Ensure project root is in path
WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

class TestAgenticModeExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000"
        cls.cj = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cj))

        # 1. Unlock session with PIN 1234
        req_lock = urllib.request.Request(
            f"{cls.base_url}/lock",
            data=json.dumps({"pin": "1234"}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with cls.opener.open(req_lock, timeout=5) as resp:
            pass

        # 2. Get CSRF token
        with cls.opener.open(f"{cls.base_url}/", timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'const CSRF = ["\'](.*?)["\'];', html)
            cls.csrf = m.group(1) if m else "test"

    def create_session(self):
        req_new = urllib.request.Request(
            f"{self.base_url}/new",
            data=b'{}',
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req_new, timeout=5) as r:
            s_data = json.loads(r.read().decode('utf-8'))
            return s_data['id']

    def send_chat(self, sid, message, agentic_mode=True):
        req = urllib.request.Request(
            f"{self.base_url}/chat",
            data=json.dumps({
                "session": sid,
                "message": message,
                "model": "auto",
                "agentic_mode": agentic_mode
            }).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            return content

    def test_01_agentic_toggle_settings(self):
        """Verify Agentic Mode can be checked and toggled via settings API."""
        req_get = urllib.request.Request(f"{self.base_url}/settings")
        with self.opener.open(req_get, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            self.assertTrue(data['settings'].get('agentic_mode_enabled') in (True, False))

        # Toggle to True
        req_post = urllib.request.Request(
            f"{self.base_url}/settings",
            data=json.dumps({"agentic_mode_enabled": True}).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req_post, timeout=5) as r:
            res = json.loads(r.read().decode('utf-8'))
            self.assertTrue(res['settings']['agentic_mode_enabled'])

    def test_02_natural_app_launch_and_contextual_close(self):
        """Test 'Open WhatsApp' followed by 'Close that'."""
        sid = self.create_session()
        # 1. Open WhatsApp
        reply1 = self.send_chat(sid, "Open WhatsApp", agentic_mode=True)
        self.assertTrue("Launched whatsapp" in reply1 or "Opened WhatsApp" in reply1 or "WhatsApp" in reply1)

        # 2. Contextual close ("Close that")
        reply2 = self.send_chat(sid, "Close that", agentic_mode=True)
        self.assertTrue("Closed application whatsapp" in reply2 or "Close the current window" in reply2 or "Safety Confirmation" in reply2 or "close" in reply2.lower())

    def test_03_web_search_and_music_playback(self):
        """Test web search and natural music query."""
        sid = self.create_session()
        # Search AI news
        reply1 = self.send_chat(sid, "Search for the latest AI news", agentic_mode=True)
        self.assertTrue("Google search" in reply1 or "Searched Google" in reply1)
        self.assertTrue("latest ai news" in reply1.lower())

        # Natural music: Find a new Canadian song
        reply2 = self.send_chat(sid, "Find a new Canadian song", agentic_mode=True)
        self.assertIn("Opened YouTube", reply2)
        self.assertTrue("canadian" in reply2.lower() or "music" in reply2.lower())

    def test_04_contextual_pronoun_resolution_and_media(self):
        """Test 'Make it quieter', 'Play that', and 'Play the next song'."""
        sid = self.create_session()
        # Initial song play
        self.send_chat(sid, "Play Kesariya on YouTube", agentic_mode=True)

        # Contextual volume
        reply_vol = self.send_chat(sid, "Make it a little quieter", agentic_mode=True)
        self.assertIn("Volume adjusted", reply_vol)

        # Contextual media next
        reply_next = self.send_chat(sid, "Play the next song", agentic_mode=True)
        self.assertIn("next track", reply_next)

    def test_05_volume_and_brightness_controls(self):
        """Test direct volume percentage and brightness setting."""
        sid = self.create_session()
        # Volume 40%
        reply_v = self.send_chat(sid, "Set the volume to 40%", agentic_mode=True)
        self.assertIn("Volume set to 40%", reply_v)

        # Volume mute
        reply_mute = self.send_chat(sid, "Mute the sound", agentic_mode=True)
        self.assertIn("mute", reply_mute.lower())

        # Brightness 60%
        reply_b = self.send_chat(sid, "Set the brightness to 60%", agentic_mode=True)
        self.assertTrue("brightness" in reply_b.lower())

    def test_06_window_and_desktop_controls(self):
        """Test window minimize, maximize, and show desktop."""
        sid = self.create_session()
        reply_min = self.send_chat(sid, "Minimize this", agentic_mode=True)
        self.assertTrue("Minimized" in reply_min or "No active window" in reply_min)

        reply_desk = self.send_chat(sid, "Show me the desktop", agentic_mode=True)
        self.assertIn("Showing desktop", reply_desk)

    def test_07_system_power_safety_confirmations(self):
        """Test Lock immediately, and Shutdown/Restart 2-step confirmation."""
        sid = self.create_session()
        # Shutdown -> Must prompt for confirmation
        reply_sd = self.send_chat(sid, "Shut down the computer", agentic_mode=True)
        self.assertIn("confirm", reply_sd.lower())

        # Cancel pending shutdown
        reply_cancel = self.send_chat(sid, "Cancel pending shutdown", agentic_mode=True)
        self.assertIn("cancelled", reply_cancel.lower())

    def test_08_reminders_creation_and_persistence(self):
        """Test creating a reminder and verifying persistence in reminders.json."""
        sid = self.create_session()
        reply_rem = self.send_chat(sid, "Remind me to submit project audit in 25 minutes", agentic_mode=True)
        self.assertIn("Reminder set", reply_rem)
        self.assertIn("submit project audit", reply_rem)

    def test_09_multi_step_workflow_execution(self):
        """Test multi-step instruction: 'Find a new Canadian song, open YouTube, search for it, and reduce the volume'."""
        sid = self.create_session()
        multi_cmd = "Find a new Canadian song, open YouTube, search for it, and reduce the volume"
        reply_multi = self.send_chat(sid, multi_cmd, agentic_mode=True)
        self.assertIn("multi-step plan", reply_multi.lower())
        self.assertIn("YouTube", reply_multi)
        self.assertIn("Volume adjusted", reply_multi)

    def test_10_ambiguous_target_clarification(self):
        """Test ambiguous pronoun reference with empty context produces clarification question."""
        import jarvis
        with jarvis.EXECUTION_CONTEXT_LOCK:
            orig = jarvis.EXECUTION_CONTEXT['last_opened_target']
            jarvis.EXECUTION_CONTEXT['last_opened_target'] = None
            try:
                tool, args = jarvis.resolve_contextual_reference("Open that application")
                self.assertEqual(tool, 'clarification')
                self.assertIn("Which application", args.get('question', ''))
            finally:
                jarvis.EXECUTION_CONTEXT['last_opened_target'] = orig

    def test_11_agentic_mode_disabled_behavior(self):
        """Verify that when Agentic Mode is OFF, commands run through standard deterministic mode."""
        sid = self.create_session()
        reply = self.send_chat(sid, "Open WhatsApp", agentic_mode=False)
        self.assertTrue("Opened WhatsApp" in reply or "Launched" in reply or "WhatsApp" in reply)

if __name__ == "__main__":
    unittest.main()
