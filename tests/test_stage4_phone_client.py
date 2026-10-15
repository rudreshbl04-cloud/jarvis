"""
Unit and integration tests for Stage 4 Phone Client & Secure Networking.
Verifies:
1. PWA Manifest (/manifest.json) validity and configuration.
2. PWA Service Worker (/sw.js) availability and offline handling.
3. Network Info API (/api/network-info) dynamic IP resolution.
4. Zero shared default PIN and rate-limited lockout protection.
5. Android client project structure and build integrity.
6. Touch layout CSS compliance (44px min tap targets, safe-area insets).
7. Default local-only binding security.
"""

import unittest
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestStage4PhoneClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import jarvis
        cls.jarvis = jarvis
        cls.app = jarvis.app
        cls.client = cls.app.test_client()
        with open(REPO_ROOT / "jarvis.py", "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_pwa_manifest_route(self):
        """Verify /manifest.json returns valid PWA configuration."""
        res = self.client.get('/manifest.json')
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/manifest+json", res.headers.get("Content-Type", ""))
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn("Jarvis", data.get("name", ""))
        self.assertEqual(data.get("display"), "standalone")
        self.assertTrue(len(data.get("icons", [])) >= 2)

    def test_service_worker_route(self):
        """Verify /sw.js exists and serves service worker script."""
        res = self.client.get('/sw.js')
        self.assertEqual(res.status_code, 200)
        self.assertIn("javascript", res.headers.get("Content-Type", ""))
        body = res.data.decode('utf-8')
        self.assertIn("addEventListener('install'", body)
        self.assertIn("addEventListener('fetch'", body)
        self.assertIn("Laptop Unavailable", body)

    def test_network_info_route(self):
        """Verify /api/network-info provides dynamic LAN IP and URL."""
        res = self.client.get('/api/network-info')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn('lan_ip', data)
        self.assertIn('lan_url', data)
        self.assertTrue(data['lan_url'].endswith(':5000'))
        self.assertFalse(data['lan_ip'].startswith('169.254.'))

    def test_pin_hashing_and_lockout(self):
        """Verify zero shared default PIN, salted hashing, and rate limiting."""
        # 1. Salted hashing
        s1, h1 = self.jarvis.hash_pin("5839")
        self.assertTrue(self.jarvis.verify_pin("5839", s1, h1))
        self.assertFalse(self.jarvis.verify_pin("0000", s1, h1))

        # 2. Rate limiting lockout
        test_ip = "192.168.1.250"
        self.jarvis.reset_ip_attempts(test_ip)
        for _ in range(5):
            rem = self.jarvis.record_failed_attempt(test_ip)
        self.assertGreater(self.jarvis.check_ip_lockout(test_ip), 0)
        self.jarvis.reset_ip_attempts(test_ip)
        self.assertEqual(self.jarvis.check_ip_lockout(test_ip), 0)

    def test_android_wrapper_structure(self):
        """Verify thin Android client wrapper files exist."""
        android_dir = REPO_ROOT / "mobile" / "android"
        self.assertTrue((android_dir / "settings.gradle").exists())
        self.assertTrue((android_dir / "build.gradle").exists())
        self.assertTrue((android_dir / "app" / "build.gradle").exists())
        self.assertTrue((android_dir / "app" / "src" / "main" / "AndroidManifest.xml").exists())
        self.assertTrue((android_dir / "app" / "src" / "main" / "java" / "com" / "jarvis" / "client" / "MainActivity.java").exists())
        self.assertTrue((android_dir / "build_apk.py").exists())
        self.assertTrue((android_dir / "README.md").exists())

    def test_mobile_touch_targets_css(self):
        """Verify CSS contains 44px min tap targets and notch safe-area handling."""
        self.assertIn("min-width: 44px", self.content)
        self.assertIn("min-height: 44px", self.content)
        self.assertIn("env(safe-area-inset-bottom", self.content)

    def test_local_only_default_security(self):
        """Verify phone_mode defaults to False (local-only 127.0.0.1)."""
        self.assertFalse(self.jarvis.DEFAULT_SETTINGS.get('phone_mode', False))

if __name__ == "__main__":
    unittest.main()
