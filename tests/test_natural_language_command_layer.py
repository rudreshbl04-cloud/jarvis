import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import unittest
from unittest.mock import patch, MagicMock

# Import jarvis
sys.path.insert(0, os.path.abspath('.'))
import jarvis

class TestNaturalLanguageCommandLayer(unittest.TestCase):
    def setUp(self):
        with jarvis.EXECUTION_CONTEXT_LOCK:
            jarvis.EXECUTION_CONTEXT['recent_actions'].clear()
            jarvis.EXECUTION_CONTEXT['last_opened_target'] = None
            jarvis.EXECUTION_CONTEXT['last_opened_type'] = None
            jarvis.EXECUTION_CONTEXT['last_opened_url'] = None
            jarvis.EXECUTION_CONTEXT['previous_target'] = None
            jarvis.EXECUTION_CONTEXT['previous_type'] = None
            jarvis.EXECUTION_CONTEXT['last_search_query'] = None
        with jarvis.PENDING_SYSTEM_LOCK:
            jarvis.PENDING_SYSTEM_ACTION.clear()

    @patch('jarvis.launch_target', return_value=(True, 'Opened successfully', 'proc'))
    @patch('jarvis.verify_browser_running', return_value=True)
    def test_5_1_opening_websites(self, mock_ver_browser, mock_launch):
        # 1. "Open YouTube"
        res = jarvis.dispatch_action("Open YouTube")
        self.assertIn("YouTube", res)
        self.assertIn("browser verified running", res)
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_opened_target'], 'youtube')
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_opened_type'], 'url')

        # 2. "Go to YouTube"
        res = jarvis.dispatch_action("Go to YouTube")
        self.assertIn("YouTube", res)

        # 3. "Launch YouTube in my browser"
        res = jarvis.dispatch_action("Launch YouTube in my browser")
        self.assertIn("YouTube", res)

        # 4. "Take me to YouTube"
        res = jarvis.dispatch_action("Take me to YouTube")
        self.assertIn("YouTube", res)

        # 5. "Open Google"
        res = jarvis.dispatch_action("Open Google")
        self.assertIn("Google", res)
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_opened_target'], 'google')

        # 6. "Go to Google.com"
        res = jarvis.dispatch_action("Go to Google.com")
        self.assertIn("google.com", res.lower())

        # 7. "Open Gmail"
        res = jarvis.dispatch_action("Open Gmail")
        self.assertIn("Gmail", res)

        # 8. "Open the official Microsoft website"
        res = jarvis.dispatch_action("Open the official Microsoft website")
        self.assertIn("Microsoft", res)

        # 9. "Open the website in my browser" (uses last opened website)
        res = jarvis.dispatch_action("Open the website in my browser")
        self.assertIn("in browser", res)

        # 10. "Switch to Google"
        res = jarvis.dispatch_action("Switch to Google")
        self.assertIn("Google", res)

        # 11. "Go back to YouTube"
        res = jarvis.dispatch_action("Go back to YouTube")
        self.assertIn("YouTube", res)

        # 12. "Open that website again"
        res = jarvis.dispatch_action("Open that website again")
        self.assertIn("YouTube", res)

    @patch('jarvis.launch_target', return_value=(True, 'Opened successfully', 'proc'))
    @patch('jarvis.verify_app_running', return_value=True)
    def test_5_2_opening_desktop_apps(self, mock_ver_app, mock_launch):
        # 1. "Open Calculator"
        res = jarvis.dispatch_action("Open Calculator")
        self.assertIn("Calculator", res)
        self.assertIn("verified running", res)
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_opened_target'], 'calculator')
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_opened_type'], 'app')

        # 2. "Launch Notepad"
        res = jarvis.dispatch_action("Launch Notepad")
        self.assertIn("Notepad", res)

        # 3. "Open File Explorer"
        res = jarvis.dispatch_action("Open File Explorer")
        self.assertIn("File Explorer", res)

        # 4. "Start Settings"
        res = jarvis.dispatch_action("Start Settings")
        self.assertIn("Settings", res)

        # 5. "Open Paint"
        res = jarvis.dispatch_action("Open Paint")
        self.assertIn("Paint", res)

        # 6. "Switch to Calculator"
        res = jarvis.dispatch_action("Switch to Calculator")
        self.assertIn("Calculator", res)

        # 7. "Reopen the app"
        res = jarvis.dispatch_action("Reopen the app")
        self.assertIn("Calculator", res)

        # 8. "Close Calculator" (SAFETY GATE)
        res = jarvis.dispatch_action("Close Calculator")
        self.assertIn("Safety Confirmation Required", res)
        self.assertIn("calculator", res.lower())
        self.assertTrue(bool(jarvis.PENDING_SYSTEM_ACTION))

    @patch('jarvis.launch_target', return_value=(True, 'Opened successfully', 'proc'))
    @patch('jarvis.verify_browser_running', return_value=True)
    def test_5_3_searching_and_compound_commands(self, mock_ver_browser, mock_launch):
        # 1. "Open Google and search for cats"
        res = jarvis.dispatch_action("Open Google and search for cats")
        self.assertIn("Google search for cats", res)
        self.assertEqual(jarvis.EXECUTION_CONTEXT['last_search_query'], 'cats')

        # 2. "Search Google for the latest Python documentation"
        res = jarvis.dispatch_action("Search Google for the latest Python documentation")
        self.assertIn("latest Python documentation", res)

        # 3. "Search the web for machine-learning internships"
        res = jarvis.dispatch_action("Search the web for machine-learning internships")
        self.assertIn("machine-learning internships", res)

        # 4. "Open YouTube and search for Python tutorials"
        res = jarvis.dispatch_action("Open YouTube and search for Python tutorials")
        self.assertIn("YouTube search for Python tutorials", res)

        # 5. "Open Google, search for cats, and tell me what you find"
        res = jarvis.dispatch_action("Open Google, search for cats, and tell me what you find")
        self.assertIn("Google search for cats", res)
        self.assertNotIn("and tell me what you find", res)

    @patch('jarvis.launch_target', return_value=(True, 'Opened successfully', 'proc'))
    @patch('jarvis.verify_browser_running', return_value=True)
    @patch('jarvis.verify_app_running', return_value=True)
    def test_5_4_follow_up_and_contextual_commands(self, mock_ver_app, mock_ver_browser, mock_launch):
        # Baseline sequence:
        # Step 1: Open YouTube
        res1 = jarvis.dispatch_action("Open YouTube")
        self.assertIn("YouTube", res1)

        # Step 2: "What did you just open?"
        res2 = jarvis.dispatch_action("What did you just open?")
        self.assertIn("YouTube", res2)

        # Step 3: "Open Calculator"
        res3 = jarvis.dispatch_action("Open Calculator")
        self.assertIn("Calculator", res3)

        # Step 4: "Which application is active?"
        res4 = jarvis.dispatch_action("Which application is active?")
        self.assertIn("Calculator", res4)

        # Step 5: "Open it"
        res5 = jarvis.dispatch_action("Open it")
        self.assertIn("Calculator", res5)

        # Step 6: "Open the previous website"
        res6 = jarvis.dispatch_action("Open the previous website")
        self.assertIn("YouTube", res6)

        # Step 7: "Now search for dogs"
        res7 = jarvis.dispatch_action("Now search for dogs")
        self.assertIn("dogs", res7)

        # Step 8: "Cancel that"
        res8 = jarvis.dispatch_action("Cancel that")
        self.assertIn("cancelled", res8.lower())

        # Step 9: "Don't open that"
        res9 = jarvis.dispatch_action("Don't open that")
        self.assertTrue("cancelled" in res9.lower() or "will not open" in res9.lower())

        # Step 10: User correction: "Open YouTube. No, I meant Google"
        res10 = jarvis.dispatch_action("Open YouTube. No, I meant Google")
        self.assertIn("Google", res10)
        self.assertNotIn("YouTube", res10)

        # Step 11: User correction: "Open YouTube, actually Google"
        res11 = jarvis.dispatch_action("Open YouTube, actually Google")
        self.assertIn("Google", res11)
        self.assertNotIn("YouTube", res11)

if __name__ == '__main__':
    unittest.main()
