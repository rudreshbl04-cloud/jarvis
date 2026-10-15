import os
import time
import unittest
from jarvis import REMINDERS, recover_reminders, STATE_LOCK, safe_save_json, safe_load_json

class TestStage11NotesMemoryReminders(unittest.TestCase):
    def test_atomic_storage(self):
        tmp_file = os.path.join(os.path.dirname(__file__), 'temp_test_storage.json')
        try:
            payload = {'key': 'jarvis_4.0_value', 'count': 42}
            safe_save_json(tmp_file, payload)
            loaded = safe_load_json(tmp_file, {})
            self.assertEqual(loaded.get('key'), 'jarvis_4.0_value')
            self.assertEqual(loaded.get('count'), 42)
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def test_recover_reminders_marks_missed(self):
        test_reminder_id = 'test_missed_reminder_123'
        with STATE_LOCK:
            REMINDERS.append({
                'id': test_reminder_id,
                'text': 'Test past reminder',
                'due': time.time() - 3600, # 1 hour in the past
                'status': 'pending',
                'created_at': '2026-01-01 10:00'
            })
        
        recover_reminders()

        with STATE_LOCK:
            item = next((r for r in REMINDERS if r.get('id') == test_reminder_id), None)
            self.assertIsNotNone(item)
            self.assertEqual(item.get('status'), 'missed')
            # Clean up test reminder
            REMINDERS.remove(item)

if __name__ == '__main__':
    unittest.main()
