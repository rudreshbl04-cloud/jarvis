import unittest
from jarvis import app

class TestStage13Diagnostics(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_diagnostics_endpoint(self):
        resp = self.client.get('/diagnostics')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get('version'), '4.0.0-rubi-core')
        self.assertIn('system_resources', data)
        self.assertIn('action_queue', data)
        self.assertIn('circuit_state', data)
        self.assertIn('installed_models', data)

        res = data['system_resources']
        self.assertIn('ram_used_mb', res)
        self.assertIn('ram_total_mb', res)

if __name__ == '__main__':
    unittest.main()
