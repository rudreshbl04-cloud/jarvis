import unittest
import os
import subprocess
import urllib.request
import json

class TestWindowsStartup(unittest.TestCase):
    def test_startup_scripts_exist(self):
        workspace = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        scripts = ["start_jarvis.ps1", "stop_jarvis.ps1", "install_jarvis_startup.ps1", "verify_jarvis_startup.ps1"]
        for s in scripts:
            p = os.path.join(workspace, "scripts", s)
            self.assertTrue(os.path.exists(p), f"Script {s} should exist in scripts/")

    def test_server_healthy(self):
        req = urllib.request.Request("http://127.0.0.1:5000/manifest.json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(data.get("name"), "Jarvis")

    def test_ollama_healthy_and_models(self):
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            models = [m.get("name") for m in data.get("models", [])]
            self.assertGreaterEqual(len(models), 1, "At least one model must be present in Ollama")

if __name__ == "__main__":
    unittest.main()
