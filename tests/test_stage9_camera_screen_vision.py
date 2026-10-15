import unittest
import base64
from jarvis import capture_screen_image, pick_vision_model, analyze_screen_with_vision

class TestStage9CameraScreenVision(unittest.TestCase):
    def test_capture_screen_image(self):
        b64 = capture_screen_image(max_dim=256, quality=50)
        if b64 is not None:
            raw = base64.b64decode(b64)
            # JPEG magic bytes: FF D8 FF
            self.assertTrue(raw.startswith(b'\xff\xd8\xff'), "Captured image must be valid JPEG data")

    def test_pick_vision_model(self):
        v_model = pick_vision_model()
        self.assertIsInstance(v_model, str)
        self.assertTrue(len(v_model) > 0)

    def test_analyze_screen_missing_model_feedback(self):
        # Pass a 1x1 dummy jpeg
        dummy_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
        b64_dummy = base64.b64encode(dummy_jpeg).decode('utf-8')
        res = analyze_screen_with_vision("What is on screen?", b64_img=b64_dummy)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

if __name__ == '__main__':
    unittest.main()
