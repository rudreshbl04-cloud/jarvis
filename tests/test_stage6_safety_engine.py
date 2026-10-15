import os
import unittest
from pathlib import Path
from jarvis import ActionRiskLevel, SharedSafetyEngine, SAFETY_ENGINE

class TestStage6SafetyEngine(unittest.TestCase):
    def test_classify_tool_risk(self):
        # Read-only / Low risk
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('get_time'), ActionRiskLevel.READ_ONLY)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('get_date'), ActionRiskLevel.READ_ONLY)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('calculate'), ActionRiskLevel.READ_ONLY)
        
        # Moderate / Medium risk
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('save_note'), ActionRiskLevel.MODERATE)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('set_reminder'), ActionRiskLevel.MODERATE)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('open_site'), ActionRiskLevel.MODERATE)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('mouse_click'), ActionRiskLevel.MODERATE)
        
        # High risk
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('delete_file'), ActionRiskLevel.HIGH)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('kill_process'), ActionRiskLevel.HIGH)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('shell_command'), ActionRiskLevel.HIGH)
        self.assertEqual(SAFETY_ENGINE.classify_tool_risk('shutdown_system'), ActionRiskLevel.HIGH)

    def test_path_safety_validation(self):
        # Safe paths
        safe, res = SAFETY_ENGINE.is_path_safe('notes.txt', allow_write=True)
        self.assertTrue(safe)

        safe, res = SAFETY_ENGINE.is_path_safe(str(Path.home() / 'Documents' / 'test.txt'), allow_write=True)
        self.assertTrue(safe)

        # Prohibited Windows system directory write
        safe, reason = SAFETY_ENGINE.is_path_safe(r'C:\Windows\System32\drivers\etc\hosts', allow_write=True)
        self.assertFalse(safe)
        self.assertIn("strictly prohibited", reason.lower())

        safe, reason = SAFETY_ENGINE.is_path_safe(r'C:\Program Files\malware.dll', allow_write=True)
        self.assertFalse(safe)

        # Empty path
        safe, reason = SAFETY_ENGINE.is_path_safe('', allow_write=True)
        self.assertFalse(safe)

    def test_command_safety_validation(self):
        # Safe commands
        safe, msg = SAFETY_ENGINE.is_command_safe('echo "Hello World"')
        self.assertTrue(safe)

        safe, msg = SAFETY_ENGINE.is_command_safe('git status')
        self.assertTrue(safe)

        # Prohibited dangerous commands
        safe, msg = SAFETY_ENGINE.is_command_safe('format c: /fs:NTFS')
        self.assertFalse(safe)
        self.assertIn('prohibited', msg.lower())

        safe, msg = SAFETY_ENGINE.is_command_safe('rmdir /s /q C:\\')
        self.assertFalse(safe)

        safe, msg = SAFETY_ENGINE.is_command_safe('del /f /s /q C:\\')
        self.assertFalse(safe)

        safe, msg = SAFETY_ENGINE.is_command_safe('reg delete HKLM\\Software')
        self.assertFalse(safe)

    def test_execute_with_safety_gate_prohibited(self):
        # Shell command with destructive payload
        res = SAFETY_ENGINE.execute_with_safety_gate('shell_command', {'command': 'format C:'})
        self.assertFalse(res['ok'])
        self.assertEqual(res['risk'], ActionRiskLevel.PROHIBITED)

        # Write to system directory
        res = SAFETY_ENGINE.execute_with_safety_gate('write_file', {'path': r'C:\Windows\System32\test.txt'})
        self.assertFalse(res['ok'])
        self.assertEqual(res['risk'], ActionRiskLevel.PROHIBITED)

    def test_test_mode_bypass(self):
        os.environ['JARVIS_TEST_MODE'] = '1'
        try:
            res = SAFETY_ENGINE.execute_with_safety_gate('open_site', {'url': 'https://google.com'})
            self.assertTrue(res['ok'])
            self.assertEqual(res['risk'], ActionRiskLevel.MODERATE)
        finally:
            os.environ.pop('JARVIS_TEST_MODE', None)

if __name__ == '__main__':
    unittest.main()
