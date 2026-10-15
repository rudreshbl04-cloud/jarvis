import os
import unittest
from jarvis import is_wake_only_phrase, strip_leading_wake_phrase, SETTINGS

class TestStage7VoiceAndWakeWord(unittest.TestCase):
    def test_wake_word_classification(self):
        # Primary "Hey Rubi"
        self.assertTrue(is_wake_only_phrase("Hey Rubi"))
        self.assertTrue(is_wake_only_phrase("hey rubi"))
        self.assertTrue(is_wake_only_phrase("Rubi"))
        self.assertTrue(is_wake_only_phrase("hi rubi"))
        self.assertTrue(is_wake_only_phrase("hello rubi"))

        # Legacy "Hey Jarvis"
        self.assertTrue(is_wake_only_phrase("Hey Jarvis"))
        self.assertTrue(is_wake_only_phrase("hey jarvis"))
        self.assertTrue(is_wake_only_phrase("jarvis"))

        # Non-wake phrases
        self.assertFalse(is_wake_only_phrase("Hey Rubi, set a timer for 5 minutes"))
        self.assertFalse(is_wake_only_phrase("write a ruby script"))
        self.assertFalse(is_wake_only_phrase("what is a rubi lens"))

    def test_leading_wake_phrase_stripping(self):
        cases = [
            ("Hey Rubi, what is the time?", "what is the time?"),
            ("Hey Ruby please open calculator", "please open calculator"),
            ("Hey Jarvis, search for news", "search for news"),
            ("Rubi turn off the monitor", "turn off the monitor"),
            ("Hi Rubi open notepad", "open notepad")
        ]
        for utterance, expected in cases:
            stripped = strip_leading_wake_phrase(utterance)
            self.assertEqual(stripped, expected)

    def test_wake_settings_persistence(self):
        orig = SETTINGS.get('wake_word_enabled', False)
        try:
            SETTINGS['wake_word_enabled'] = True
            self.assertTrue(SETTINGS.get('wake_word_enabled'))
            SETTINGS['wake_word_enabled'] = False
            self.assertFalse(SETTINGS.get('wake_word_enabled'))
        finally:
            SETTINGS['wake_word_enabled'] = orig

if __name__ == '__main__':
    unittest.main()
