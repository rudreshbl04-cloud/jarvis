import os
import unittest
from jarvis import (
    get_gemini_api_key,
    GEMINI_CIRCUIT,
    record_gemini_failure,
    record_gemini_success,
    reset_gemini_circuit
)

class TestStage12GeminiServices(unittest.TestCase):
    def test_gemini_api_key_retrieval(self):
        # Even without key, returns string without exception
        key = get_gemini_api_key()
        self.assertIsInstance(key, str)

    def test_gemini_circuit_breaker(self):
        # Reset circuit first
        reset_gemini_circuit()
        self.assertEqual(GEMINI_CIRCUIT['consecutive_failures'], 0)
        self.assertEqual(GEMINI_CIRCUIT['trip_time'], 0)

        # Record generic transient failure
        record_gemini_failure('Connection timeout')
        self.assertEqual(GEMINI_CIRCUIT['consecutive_failures'], 1)

        # Reset
        reset_gemini_circuit()
        self.assertEqual(GEMINI_CIRCUIT['consecutive_failures'], 0)
        self.assertEqual(GEMINI_CIRCUIT['trip_time'], 0)

    def test_record_gemini_success(self):
        record_gemini_failure('Connection timeout')
        self.assertEqual(GEMINI_CIRCUIT['consecutive_failures'], 1)
        record_gemini_success()
        self.assertEqual(GEMINI_CIRCUIT['consecutive_failures'], 0)

if __name__ == '__main__':
    unittest.main()
