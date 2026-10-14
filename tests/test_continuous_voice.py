import unittest
import urllib.request
import json
import re
import http.cookiejar
import http.client
import time

class TestContinuousVoiceMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://127.0.0.1:5000"
        cls.cj = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cj))
        # 1. Unlock session with PIN 1234
        req = urllib.request.Request(
            f"{cls.base_url}/lock",
            data=json.dumps({"pin": "1234"}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with cls.opener.open(req, timeout=5) as resp:
            pass

        # 2. Get CSRF token from rendered root page
        with cls.opener.open(f"{cls.base_url}/", timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'const CSRF = ["\'](.*?)["\'];', html)
            cls.csrf = m.group(1) if m else "test"

    def test_voice_stop_phrases_logic(self):
        stop_patterns = [
            r"^stop listening$",
            r"^stop listening please$",
            r"^jarvis stop listening$",
            r"^please stop listening$",
            r"^thats all$",
            r"^that is all$",
            r"^thats all jarvis$",
            r"^that will be all$",
            r"^that will be all jarvis$",
            r"^stop voice mode$",
            r"^quit listening$"
        ]
        
        valid_stops = [
            "stop listening", "Stop Listening", "STOP LISTENING",
            "that's all", "thats all", "That is all", "that will be all",
            "stop listening please", "jarvis stop listening"
        ]
        
        for phrase in valid_stops:
            cleaned = re.sub(r'[^a-z0-9\s]', '', phrase.lower()).strip()
            matched = any(re.match(p, cleaned) for p in stop_patterns)
            self.assertTrue(matched, f"Phrase '{phrase}' should be recognized as a voice stop command")

        normal_commands = [
            "play some music", "open notepad", "what is the weather",
            "that's great", "stop the music", "all done with homework"
        ]
        for cmd in normal_commands:
            cleaned = re.sub(r'[^a-z0-9\s]', '', cmd.lower()).strip()
            matched = any(re.match(p, cleaned) for p in stop_patterns)
            self.assertFalse(matched, f"Normal command '{cmd}' must NOT be treated as a stop command")

    def test_five_turn_conversational_execution(self):
        # Create session via /new
        req_new = urllib.request.Request(
            f"{self.base_url}/new",
            data=b'{}',
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req_new, timeout=5) as r:
            s_data = json.loads(r.read().decode('utf-8'))
            session_id = s_data['id']

        turns = [
            "Hi Jarvis, how are you?",
            "What is 2 plus 2?",
            "Tell me a one line tech fact.",
            "What is the capital of France?",
            "Thank you Jarvis."
        ]
        
        for idx, turn_prompt in enumerate(turns, 1):
            req = urllib.request.Request(
                f"{self.base_url}/chat",
                data=json.dumps({
                    "session": session_id,
                    "model": "fast",
                    "is_voice_mode": True,
                    "message": turn_prompt
                }).encode('utf-8'),
                headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
            )
            # Drain complete response so server does not hold active generation state
            max_wait = 45
            t0 = time.time()
            success = False
            for attempt in range(3):
                try:
                    with self.opener.open(req, timeout=45) as resp:
                        content = resp.read()
                        self.assertGreater(len(content), 0, f"Turn {idx} should receive streaming response")
                        success = True
                        break
                except http.client.IncompleteRead as ie:
                    self.assertGreater(len(ie.partial), 0, f"Turn {idx} got partial content")
                    success = True
                    break
                except urllib.error.HTTPError as he:
                    if he.code == 409 and attempt < 2:
                        time.sleep(1.0)
                        continue
                    self.fail(f"Turn {idx} encountered HTTP error: {he}")
                except Exception as e:
                    self.fail(f"Turn {idx} encountered error: {e}")
            self.assertTrue(success, f"Turn {idx} failed to complete")
            time.sleep(0.5)

    def test_natural_music_command_routing(self):
        # Create new session
        req_new = urllib.request.Request(
            f"{self.base_url}/new",
            data=b'{}',
            headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
        )
        with self.opener.open(req_new, timeout=10) as r:
            session_id = json.loads(r.read().decode('utf-8'))['id']

        queries = [
            "play shape of you",
            "I want to listen to a new Canadian song",
            "play some jazz music",
            "I want to watch interstellar trailer"
        ]
        for q in queries:
            req = urllib.request.Request(
                f"{self.base_url}/chat",
                data=json.dumps({
                    "session": session_id,
                    "model": "fast",
                    "is_voice_mode": True,
                    "message": q
                }).encode('utf-8'),
                headers={"Content-Type": "application/json", "X-Jarvis-Token": self.csrf}
            )
            content = ""
            for attempt in range(3):
                try:
                    with self.opener.open(req, timeout=30) as resp:
                        content = resp.read().decode('utf-8', errors='ignore')
                        break
                except http.client.IncompleteRead as ie:
                    content = ie.partial.decode('utf-8', errors='ignore')
                    break
                except urllib.error.HTTPError as he:
                    if he.code == 409 and attempt < 2:
                        time.sleep(1.0)
                        continue
                    raise
            
            self.assertTrue("youtube" in content.lower(), f"Command '{q}' should route to YouTube, got: {content}")
            time.sleep(0.5)

if __name__ == "__main__":
    unittest.main()
