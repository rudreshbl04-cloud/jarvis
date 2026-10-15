import unittest
from jarvis import clean_text_for_speech_py, app, CSRF_TOKEN

class TestStage8SpeechOutput(unittest.TestCase):
    def test_clean_text_for_speech(self):
        # Code blocks
        text_with_code = "Here is the code:\n```python\nprint('hello')\n```\nHope that helps!"
        cleaned = clean_text_for_speech_py(text_with_code)
        self.assertNotIn("print('hello')", cleaned)
        self.assertIn("Here is the code", cleaned)
        self.assertIn("Hope that helps", cleaned)

        # URLs
        text_with_url = "Visit https://google.com for more information."
        cleaned = clean_text_for_speech_py(text_with_url)
        self.assertNotIn("https://", cleaned)
        self.assertIn("Visit", cleaned)

        # Emojis
        text_with_emojis = "Good morning! 🚀 Have a great day! 😊"
        cleaned = clean_text_for_speech_py(text_with_emojis)
        self.assertNotIn("🚀", cleaned)
        self.assertNotIn("😊", cleaned)
        self.assertIn("Good morning", cleaned)

        # Internal bracket tags
        text_with_tags = "[FAST Mode] The answer is 42."
        cleaned = clean_text_for_speech_py(text_with_tags)
        self.assertNotIn("[FAST Mode]", cleaned)
        self.assertIn("The answer is 42", cleaned)

    def test_speak_status_endpoint(self):
        client = app.test_client()
        res = client.get('/speak/status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('available', data)
        self.assertEqual(data['engine'], 'piper')
        self.assertIn('installed_voices', data)

    def test_tts_endpoint_empty_text(self):
        client = app.test_client()
        # Empty text POST
        res_post = client.post('/tts', json={'text': ''}, headers={'X-Jarvis-Token': CSRF_TOKEN})
        self.assertEqual(res_post.status_code, 204)

        # Empty text GET
        res_get = client.get('/tts?text=')
        self.assertEqual(res_get.status_code, 204)

if __name__ == '__main__':
    unittest.main()
