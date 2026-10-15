"""
Unit tests for Stage 5: Local Models, Capabilities, Routing, and Answer Quality.
Verifies:
1. Dynamic model capability inspection (chat, vision, coding, fast, speed_warning).
2. Model routing based on task type (vision, fast, default).
3. Dynamic fallback mechanism when primary model is missing or fails.
4. Honest uncertainty detection and standard phrasing ("I do not know", etc.).
5. Memory retrieval injection into prompt context without unbounded token explosion.
6. CPU-safe configuration and warning for heavy models (>= 7b) on CPU-only hardware.
"""

import unittest
import os
import sys

WORKSPACE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

os.environ['JARVIS_TEST_MODE'] = '1'
import jarvis

class TestStage5LocalModels(unittest.TestCase):
    def setUp(self):
        jarvis.app.config['TESTING'] = True
        self.client = jarvis.app.test_client()

    def test_model_capabilities_categorization(self):
        """Verify model capability inspector flags vision, fast, and heavy models accurately."""
        caps_llama = jarvis.get_model_capabilities('llama3.2:3b')
        self.assertIn('chat', caps_llama['capabilities'])
        self.assertTrue(caps_llama['is_fast'])
        self.assertFalse(caps_llama['speed_warning'])

        caps_qwen = jarvis.get_model_capabilities('qwen2.5:3b')
        self.assertIn('chat', caps_qwen['capabilities'])
        self.assertIn('coding', caps_qwen['capabilities'])
        self.assertTrue(caps_qwen['is_fast'])

        caps_mistral = jarvis.get_model_capabilities('mistral:7b')
        self.assertTrue(caps_mistral['speed_warning'])  # 7b on CPU should flag speed warning

        caps_llava = jarvis.get_model_capabilities('llava:7b')
        self.assertIn('vision', caps_llava['capabilities'])

    def test_model_selection_and_routing(self):
        """Verify choose_best_model returns appropriate model for task requirements."""
        models = ['llama3.2:3b', 'qwen2.5:3b', 'llava:7b', 'mistral:7b']
        
        # Fast preference
        chosen_fast = jarvis.choose_best_model(models, prefer_fast=True)
        self.assertIn(chosen_fast, ('llama3.2:3b', 'qwen2.5:3b'))

        # Vision requirement
        chosen_vision = jarvis.choose_best_model(models, require_vision=True)
        self.assertEqual(chosen_vision, 'llava:7b')

        # Fallback when requested model is unavailable
        fallback = jarvis.choose_best_model(['qwen2.5:3b'], preferred='non_existent_model')
        self.assertEqual(fallback, 'qwen2.5:3b')

    def test_honest_uncertainty_handling(self):
        """Verify honest uncertainty detection and fallback formatting."""
        # Query asking for impossible/fictional private knowledge
        self.assertTrue(jarvis.is_honest_uncertainty_needed("what is the secret launch code for project zeus 2029"))
        self.assertTrue(jarvis.is_honest_uncertainty_needed("tell me future stock price of apple tomorrow"))

        # Factual question should not trigger mandatory uncertainty
        self.assertFalse(jarvis.is_honest_uncertainty_needed("what is 2 + 2"))

        # Format uncertainty response
        uncertain_resp = jarvis.format_honest_uncertainty("I do not have access to real-time future stock prices.")
        self.assertIn("do not have", uncertain_resp.lower())

    def test_memory_context_retrieval(self):
        """Verify memory retrieval finds relevant stored memories for prompt context."""
        jarvis.MEMORIES = [
            {'id': 'm1', 'text': 'User prefers dark mode and concise answers', 'created_at': 1000},
            {'id': 'm2', 'text': 'User birthday is August 15', 'created_at': 2000},
            {'id': 'm3', 'text': 'User primary project is jarvis assistant', 'created_at': 3000}
        ]

        relevant = jarvis.get_relevant_memories_for_prompt("tell me about the jarvis assistant project", max_memories=2)
        self.assertTrue(any('jarvis' in m.lower() for m in relevant))
        self.assertLessEqual(len(relevant), 2)

    def test_status_endpoint_returns_model_details(self):
        """Verify /status returns detailed_models and capabilities."""
        resp = self.client.get('/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('models', data)
        self.assertIn('detailed_models', data)
        self.assertIsInstance(data['detailed_models'], list)

if __name__ == '__main__':
    unittest.main()
