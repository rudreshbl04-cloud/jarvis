import os
import unittest
from jarvis import (
    run_tool, TOOLS, SAFETY_ENGINE,
    search_restricted_folder_and_open, execute_youtube_multistep_task,
    agentic_execute_instruction
)

class TestStage10AutomationLoop(unittest.TestCase):
    def test_tools_schema_and_registration(self):
        self.assertIsInstance(TOOLS, list)
        tool_names = [t['function']['name'] for t in TOOLS]
        self.assertIn('get_time', tool_names)
        self.assertIn('calculator', tool_names)
        self.assertIn('save_note', tool_names)
        self.assertIn('open_site', tool_names)

    def test_safe_read_tool_execution(self):
        time_res = run_tool('get_time', {})
        self.assertTrue(len(time_res) > 0)
        # Should contain AM or PM
        self.assertTrue('AM' in time_res or 'PM' in time_res)

        calc_res = run_tool('calculator', {'expression': '10 * 5 + 2'})
        self.assertIn('52', calc_res)

    def test_automation_safety_gate_blocking(self):
        # Shell command with dangerous instruction intercepted
        res = SAFETY_ENGINE.execute_with_safety_gate('shell_command', {'command': 'format d:'})
        self.assertFalse(res['ok'])
        err_msg = res.get('error') or res.get('reason') or ''
        self.assertIn('prohibited', err_msg.lower())

    def test_restricted_folder_search_invalid_folder(self):
        # Disallowed folder should fail safely
        ok, msg, path = search_restricted_folder_and_open('test.txt', 'system32')
        self.assertFalse(ok)
        self.assertIn("not recognized", msg.lower())
        self.assertEqual(path, [])

    def test_restricted_folder_search_nonexistent_file(self):
        # Nonexistent file in desktop should fail gracefully without hallucinations
        ok, msg, path = search_restricted_folder_and_open('non_existent_file_9999.xyz', 'desktop')
        self.assertFalse(ok)
        self.assertIn("was not found in desktop", msg)
        self.assertEqual(path, [])

    def test_agentic_restricted_folder_command(self):
        # Verify natural language command routing for folder search
        res = agentic_execute_instruction("open non_existent_file_9999.xyz in desktop")
        self.assertIsNotNone(res)
        self.assertIn("was not found in desktop", res)

    def test_youtube_multistep_command_execution(self):
        # Multi-step task returns structured plan execution summary
        res = execute_youtube_multistep_task("test query song")
        self.assertIsNotNone(res)
        self.assertTrue("YouTube" in res or "browser" in res.lower())

if __name__ == '__main__':
    unittest.main()

