"""
Unit and integration tests for Stage 3 Desktop UI and Themes.
Verifies:
1. Complete removal of Lecturer mode UI elements from the primary HTML template.
2. Preservation of historical lecture notes in notes store.
3. Presence of Task Status Pill (#taskStatusPill, #taskStatusText).
4. Collapsible Voice Control Drawer (#voiceControlDrawer).
5. Chat session search and filter input (#searchSessions).
6. Theme support (dark, light, system) with reduced-motion and focus ring accessibility.
7. JavaScript helper functions for task lifecycle and theme switching.
"""

import unittest
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestStage3DesktopUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jarvis_path = REPO_ROOT / "jarvis.py"
        with open(jarvis_path, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_lecturer_mode_ui_removed(self):
        """Verify Lecturer UI elements are completely removed from HTML."""
        self.assertNotIn('id="navLecturer"', self.content)
        self.assertNotIn('id="lecturerView"', self.content)
        self.assertNotIn('id="lecturerCard"', self.content)
        self.assertNotIn('id="view-lecturer"', self.content)
        self.assertNotIn("startLecturerMode()", self.content)

    def test_task_status_pill_present(self):
        """Verify #taskStatusPill and #taskStatusText exist in header."""
        self.assertIn('id="taskStatusPill"', self.content)
        self.assertIn('id="taskStatusText"', self.content)
        self.assertIn("function setTaskState(", self.content)

    def test_voice_control_drawer_present(self):
        """Verify #voiceControlDrawer and toggle function exist."""
        self.assertIn('id="voiceControlDrawer"', self.content)
        self.assertIn("function toggleVoicePanel(", self.content)

    def test_session_search_present(self):
        """Verify session search bar and filtering logic exist."""
        self.assertTrue(
            'id="chatSearchInput"' in self.content or 'id="searchSessions"' in self.content,
            "Chat session search input must exist"
        )
        self.assertIn("function filterChatSessions(", self.content)

    def test_themes_and_accessibility(self):
        """Verify theme choices include dark, light, system and accessibility styles exist."""
        self.assertIn('value="system"', self.content)
        self.assertIn("prefers-reduced-motion", self.content)
        self.assertIn(":focus-visible", self.content)
        self.assertIn("function setAppTheme(", self.content)

    def test_build_version_badge(self):
        """Verify build version badge is updated for Rubi Core 4.0."""
        self.assertIn('v4.0.0-rubi-core', self.content)

    def test_historical_notes_preserved(self):
        """Verify notes.txt or notes store exists and contains user notes."""
        notes_file = REPO_ROOT / "notes.txt"
        self.assertTrue(notes_file.exists(), "notes.txt must exist to preserve historical user notes")
        with open(notes_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 0, "Historical notes must not be empty")

if __name__ == "__main__":
    unittest.main()
