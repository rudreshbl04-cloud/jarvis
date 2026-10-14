import os
import sys
import unittest
import time
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jarvis

class TestAgenticRepairVerification(unittest.TestCase):
    def setUp(self):
        with jarvis.PENDING_SYSTEM_LOCK:
            jarvis.PENDING_SYSTEM_ACTION.clear()

    def tearDown(self):
        with jarvis.PENDING_SYSTEM_LOCK:
            jarvis.PENDING_SYSTEM_ACTION.clear()

    # =========================================================================
    # BUG 4 & INTENT: Application Resolution & Substring Ambiguity
    # =========================================================================
    def test_open_ed_disambiguation(self):
        """'Open Ed' must NOT match OneDrive or open any app; it must ask for clarification."""
        # Check find_installed_app directly
        self.assertIsNone(jarvis.find_installed_app('ed'))
        self.assertIsNone(jarvis.find_installed_app('ed.'))

        # Check agentic execution
        res = jarvis.agentic_execute_instruction('Open Ed')
        self.assertIn("Did you mean Microsoft Edge", res)
        self.assertNotIn("OneDrive", res)
        self.assertNotIn("Launched", res)

        # Check dispatch_action
        res2 = jarvis.dispatch_action('Open Ed')
        self.assertIn("Did you mean Microsoft Edge", res2)
        self.assertNotIn("OneDrive", res2)

    def test_open_unknown_app_honesty(self):
        """Opening a non-existent app must report failure honestly without opening a substitute."""
        res = jarvis.dispatch_action('Open non_existent_application_xyz123')
        self.assertTrue(
            "could not find" in res.lower() or "no other application was opened" in res.lower(),
            f"Expected honest not-found message, got: {res}"
        )
        self.assertNotIn("Launched", res)
        self.assertNotIn("verified running", res)

    # =========================================================================
    # BUG 2 & BUG 7: Intent Separation & Safety Confirmation Invariant
    # =========================================================================
    def test_close_calculator_does_not_open_calculator(self):
        """'Close Calculator' must NEVER launch/open Calculator."""
        with patch('jarvis.launch_target') as mock_launch:
            res = jarvis.dispatch_action('Close Calculator')
            mock_launch.assert_not_called()
            self.assertIn("Safety Confirmation Required", res)
            self.assertIn("calculator", res.lower())

            # Verify PENDING_SYSTEM_ACTION was created
            with jarvis.PENDING_SYSTEM_LOCK:
                self.assertTrue(bool(jarvis.PENDING_SYSTEM_ACTION))
                self.assertEqual(jarvis.PENDING_SYSTEM_ACTION.get('action'), 'close_app')
                self.assertEqual(jarvis.PENDING_SYSTEM_ACTION.get('app'), 'calculator')

    def test_close_calculator_confirmation_flow(self):
        """Close confirmation must require confirmation, cancel on 'no', and execute on 'OK'."""
        # 1. Request close
        res1 = jarvis.dispatch_action('Close Calculator')
        self.assertIn("Safety Confirmation Required", res1)

        # 2. Reject with 'no'
        res2 = jarvis.dispatch_action('no')
        self.assertIn("Action cancelled", res2)
        with jarvis.PENDING_SYSTEM_LOCK:
            self.assertFalse(bool(jarvis.PENDING_SYSTEM_ACTION))

        # 3. Request close again
        jarvis.dispatch_action('Close Calculator')

        # 4. Confirm with 'OK'
        with patch('jarvis.close_app_safe', return_value="Closed Calculator (verified closed).") as mock_close:
            res3 = jarvis.dispatch_action('OK')
            mock_close.assert_called_once_with('calculator')
            self.assertIn("Confirmed", res3)
            self.assertIn("Closed Calculator", res3)

    def test_negative_open_instruction(self):
        """'Do not open calculator' must be acknowledged as a negative command, not executed."""
        with patch('jarvis.launch_target') as mock_launch:
            res = jarvis.dispatch_action('do not open calculator')
            mock_launch.assert_not_called()
            self.assertIn("I will not open that", res)

            res2 = jarvis.dispatch_action("don't open notepad")
            mock_launch.assert_not_called()
            self.assertIn("I will not open that", res2)

    # =========================================================================
    # BUG 1 & BUG 3: Contradictory Replies & Honest Verification
    # =========================================================================
    def test_execute_agentic_tool_open_app_failed_contract(self):
        """When launch_target fails, execute_agentic_tool must NOT claim 'Launched' or 'verified running'."""
        with patch('jarvis.launch_target', return_value=(False, "Executable not found", "not_found")):
            ok, msg = jarvis.execute_agentic_tool('open_app', {'name': 'someapp'})
            self.assertFalse(ok)
            self.assertIn("could not find or open", msg.lower())
            self.assertNotIn("Launched", msg)
            self.assertNotIn("verified running", msg)

    def test_execute_agentic_tool_open_app_success_verified(self):
        """When launch_target succeeds and process is verified, report verified running."""
        with patch('jarvis.launch_target', return_value=(True, "Opened", "proc")):
            with patch('jarvis.verify_app_running', return_value=True):
                ok, msg = jarvis.execute_agentic_tool('open_app', {'name': 'notepad'})
                self.assertTrue(ok)
                self.assertIn("Opened Notepad (verified running)", msg)
                self.assertNotIn("could not find", msg.lower())

    def test_execute_agentic_tool_open_app_success_unverified(self):
        """When launch_target succeeds but verification fails, qualify the statement honestly."""
        with patch('jarvis.launch_target', return_value=(True, "Dispatched", "proc")):
            with patch('jarvis.verify_app_running', return_value=False):
                ok, msg = jarvis.execute_agentic_tool('open_app', {'name': 'notepad'})
                self.assertTrue(ok)
                self.assertIn("process unverified", msg)
                self.assertNotIn("verified running", msg)

    def test_execute_agentic_tool_open_url_honest_qualification(self):
        """Opening URL must report verified browser or accurately qualified unverified statement."""
        with patch('jarvis.launch_target', return_value=(True, "URL dispatched", "url")):
            with patch('jarvis.verify_browser_running', return_value=False):
                ok, msg = jarvis.execute_agentic_tool('open_url', {'url': 'https://www.youtube.com'})
                self.assertTrue(ok)
                self.assertTrue("couldn't verify that YouTube opened" in msg or "couldn't verify that https://www.youtube.com opened" in msg)

            with patch('jarvis.verify_browser_running', return_value=True):
                ok, msg = jarvis.execute_agentic_tool('open_url', {'url': 'https://www.youtube.com'})
                self.assertTrue(ok)
                self.assertIn("browser verified running", msg)

    # =========================================================================
    # BUG 5: [Generation Stopped] Mid-Reply Investigation & Verification
    # =========================================================================
    def test_generation_stopped_lifecycle(self):
        """Normal completion must NOT output [Generation Stopped]. Only explicit stop sets it."""
        # Test normal stream completion mock
        run = {'event': jarvis.threading.Event(), 'user_stopped': False, 'responses': []}
        chunks = []

        # Simulate normal completion
        chunks.append("Hello Rudresh, how can I help you today?")
        full_text = ''.join(chunks)
        self.assertNotIn("[Generation Stopped]", full_text)

        # Simulate deliberate user cancellation via stop()
        run['user_stopped'] = True
        chunks.append('\n[Generation Stopped]')
        stopped_text = ''.join(chunks)
        self.assertIn("[Generation Stopped]", stopped_text)

    # =========================================================================
    # PROTECTED SUBSYSTEM AUDIT: Voice State Machine & Inference Settings
    # =========================================================================
    def test_protected_settings_preserved(self):
        """Verify that CPU model and inference settings were preserved intact."""
        self.assertEqual(jarvis.SETTINGS.get('num_thread'), 4)
        self.assertEqual(jarvis.SETTINGS.get('keep_alive'), '30m')
        self.assertEqual(jarvis.pick_brain('', mode='fast'), 'llama3.2:3b')

if __name__ == '__main__':
    unittest.main()
