"""
Unit tests for story_engine.py

Run with: python -m pytest tests/test_story_engine.py
Or: python tests/test_story_engine.py
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story_engine import (
    SnowflakeEngine,
    ProjectNotFoundError,
    NoProjectLoadedError,
    ValidationError,
)


class TestSnowflakeEngine(unittest.TestCase):
    """Test suite for SnowflakeEngine class"""

    def setUp(self):
        """Create a temporary workspace for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = SnowflakeEngine(workspace_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temporary workspace after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestProjectManagement(TestSnowflakeEngine):
    """Tests for project initialization and loading"""

    def test_init_project_creates_structure(self):
        """Test that init_project creates proper directory structure"""
        metadata = self.engine.init_project("Test Novel")

        # Check metadata
        self.assertEqual(metadata["title"], "Test Novel")
        self.assertIn("created", metadata)
        self.assertIn("settings", metadata)
        self.assertTrue(metadata["settings"]["use_pov_mode"])

        # Check directories
        project_path = Path(self.temp_dir) / "test_novel"
        self.assertTrue(project_path.exists())
        self.assertTrue((project_path / "characters").exists())
        self.assertTrue((project_path / "scenes").exists())
        self.assertTrue((project_path / "drafts").exists())
        self.assertTrue((project_path / "steps").exists())
        self.assertTrue((project_path / "metadata.json").exists())

    def test_load_project_success(self):
        """Test loading an existing project"""
        self.engine.init_project("My Novel")
        metadata = self.engine.load_project("My Novel")

        self.assertEqual(metadata["title"], "My Novel")

    def test_load_project_not_found(self):
        """Test loading a non-existent project raises error"""
        with self.assertRaises(ProjectNotFoundError):
            self.engine.load_project("NonExistent Novel")

    def test_list_projects_empty(self):
        """Test listing projects when none exist"""
        projects = self.engine.list_projects()
        self.assertEqual(projects, [])

    def test_list_projects_multiple(self):
        """Test listing multiple projects"""
        self.engine.init_project("Novel One")
        self.engine.init_project("Novel Two")

        projects = self.engine.list_projects()
        self.assertEqual(len(projects), 2)

        titles = [p["title"] for p in projects]
        self.assertIn("Novel One", titles)
        self.assertIn("Novel Two", titles)


class TestPOVMode(TestSnowflakeEngine):
    """Tests for POV mode functionality"""

    def test_pov_mode_default_enabled(self):
        """Test that POV mode is enabled by default"""
        self.engine.init_project("POV Test")
        self.assertTrue(self.engine.get_pov_mode())

    def test_set_pov_mode_disable(self):
        """Test disabling POV mode"""
        self.engine.init_project("POV Test")
        self.engine.set_pov_mode(False)
        self.assertFalse(self.engine.get_pov_mode())

    def test_set_pov_mode_enable(self):
        """Test re-enabling POV mode"""
        self.engine.init_project("POV Test")
        self.engine.set_pov_mode(False)
        self.engine.set_pov_mode(True)
        self.assertTrue(self.engine.get_pov_mode())

    def test_pov_mode_persists_after_reload(self):
        """Test that POV mode setting persists after reloading project"""
        self.engine.init_project("POV Test")
        self.engine.set_pov_mode(False)

        # Reload project
        self.engine.load_project("POV Test")
        self.assertFalse(self.engine.get_pov_mode())

    def test_pov_mode_without_project_raises_error(self):
        """Test that setting POV mode without loaded project raises error"""
        with self.assertRaises(NoProjectLoadedError):
            self.engine.set_pov_mode(True)


class TestCharacterManagement(TestSnowflakeEngine):
    """Tests for character management"""

    def test_update_character_basic(self):
        """Test creating a basic character"""
        self.engine.init_project("Test Novel")

        char_data = {
            "role": "protagonist",
            "motivation": "Save the world"
        }
        self.engine.update_character("Alice", char_data)

        # Verify file was created
        char_path = Path(self.temp_dir) / "test_novel" / "characters" / "alice.json"
        self.assertTrue(char_path.exists())

        # Verify data
        retrieved = self.engine.get_character("Alice")
        self.assertEqual(retrieved["name"], "Alice")
        self.assertEqual(retrieved["role"], "protagonist")

    def test_update_character_validation_empty_name(self):
        """Test that empty character name raises ValidationError"""
        self.engine.init_project("Test Novel")

        with self.assertRaises(ValidationError):
            self.engine.update_character("", {"role": "protagonist"})

    def test_update_character_validation_missing_name(self):
        """Test that character with no name field raises ValidationError"""
        self.engine.init_project("Test Novel")

        # This should work because name is passed as parameter
        self.engine.update_character("Bob", {"role": "antagonist"})

        # But internally if data is missing 'name', validation catches it
        # Test internal validation directly
        with self.assertRaises(ValidationError):
            self.engine._validate_character({})

    def test_get_all_characters(self):
        """Test retrieving all characters"""
        self.engine.init_project("Test Novel")

        self.engine.update_character("Alice", {"role": "protagonist"})
        self.engine.update_character("Bob", {"role": "antagonist"})

        chars = self.engine.get_all_characters()
        self.assertEqual(len(chars), 2)

        names = [c["name"] for c in chars]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)


class TestSceneManagement(TestSnowflakeEngine):
    """Tests for scene management"""

    def test_update_scene_list_valid(self):
        """Test updating scene list with valid data"""
        self.engine.init_project("Test Novel")

        scenes = [
            {
                "scene_number": 1,
                "pov_character": "Alice",
                "gist": "Opening scene",
                "conflict": "Test conflict",
                "disaster": "Test disaster"
            },
            {
                "scene_number": 2,
                "pov_character": "Bob",
                "gist": "Second scene",
                "conflict": "Test conflict 2",
                "disaster": "Test disaster 2"
            }
        ]

        self.engine.update_scene_list(scenes)

        # Verify scenes were saved
        retrieved = self.engine.get_scene_list()
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0]["scene_number"], 1)

    def test_update_scene_list_validation_missing_scene_number(self):
        """Test that scene without scene_number raises ValidationError"""
        self.engine.init_project("Test Novel")

        invalid_scenes = [
            {
                "gist": "Scene without number"
            }
        ]

        with self.assertRaises(ValidationError) as context:
            self.engine.update_scene_list(invalid_scenes)

        self.assertIn("scene_number", str(context.exception))

    def test_update_scene_list_validation_invalid_scene_number_type(self):
        """Test that scene with non-integer scene_number raises ValidationError"""
        self.engine.init_project("Test Novel")

        invalid_scenes = [
            {
                "scene_number": "one",  # String instead of int
                "gist": "Test scene"
            }
        ]

        with self.assertRaises(ValidationError) as context:
            self.engine.update_scene_list(invalid_scenes)

        self.assertIn("integer", str(context.exception))

    def test_update_scene_list_validation_negative_scene_number(self):
        """Test that scene with negative scene_number raises ValidationError"""
        self.engine.init_project("Test Novel")

        invalid_scenes = [
            {
                "scene_number": -1,
                "gist": "Test scene"
            }
        ]

        with self.assertRaises(ValidationError) as context:
            self.engine.update_scene_list(invalid_scenes)

        self.assertIn("positive", str(context.exception))

    def test_update_scene_list_validation_empty_gist(self):
        """Test that scene with empty gist raises ValidationError"""
        self.engine.init_project("Test Novel")

        invalid_scenes = [
            {
                "scene_number": 1,
                "gist": "   "  # Only whitespace
            }
        ]

        with self.assertRaises(ValidationError) as context:
            self.engine.update_scene_list(invalid_scenes)

        self.assertIn("gist", str(context.exception))


class TestStepManagement(TestSnowflakeEngine):
    """Tests for step output management"""

    def test_save_step_output_updates_metadata(self):
        """Test that save_step_output updates completed_steps in metadata"""
        self.engine.init_project("Test Novel")

        self.engine.save_step_output(1, "Step 1 content", "One-Sentence Hook")

        # Load metadata and check completed_steps
        metadata_path = Path(self.temp_dir) / "test_novel" / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        self.assertIn(1, metadata["completed_steps"])
        self.assertEqual(metadata["current_step"], 1)

    def test_save_step_output_creates_file(self):
        """Test that save_step_output creates the step file"""
        self.engine.init_project("Test Novel")

        self.engine.save_step_output(2, "Step 2 content", "Five-Sentence Structure")

        step_file = Path(self.temp_dir) / "test_novel" / "steps" / "step_02.md"
        self.assertTrue(step_file.exists())

        content = step_file.read_text(encoding='utf-8')
        self.assertIn("Step 2 content", content)

    def test_get_step_output(self):
        """Test retrieving step output"""
        self.engine.init_project("Test Novel")

        test_content = "This is step 3 content"
        self.engine.save_step_output(3, test_content, "Character Sheets")

        retrieved = self.engine.get_step_output(3)
        self.assertIn(test_content, retrieved)


class TestHealthCheck(TestSnowflakeEngine):
    """Tests for health check functionality"""

    def test_get_status_basic(self):
        """Test basic status retrieval"""
        self.engine.init_project("Test Novel")

        status = self.engine.get_status()

        self.assertEqual(status["project_title"], "Test Novel")
        self.assertEqual(status["current_step"], 0)
        self.assertEqual(status["completion_percentage"], 0)
        self.assertEqual(status["characters_defined"], 0)
        self.assertEqual(status["scenes_planned"], 0)

    def test_get_status_with_progress(self):
        """Test status with some progress"""
        self.engine.init_project("Test Novel")

        # Complete some steps
        self.engine.save_step_output(1, "Hook", "One-Sentence Hook")
        self.engine.save_step_output(2, "Structure", "Five-Sentence Structure")

        # Add a character
        self.engine.update_character("Alice", {"role": "protagonist"})

        status = self.engine.get_status()

        self.assertEqual(len(status["completed_steps"]), 2)
        self.assertEqual(status["current_step"], 2)
        self.assertGreater(status["completion_percentage"], 0)
        self.assertEqual(status["characters_defined"], 1)

    def test_get_status_health_warnings(self):
        """Test health check warnings"""
        self.engine.init_project("Test Novel")

        # Complete step 3 without defining characters
        self.engine.save_step_output(3, "Characters", "Character Sheets")

        status = self.engine.get_status()

        # Should have health issue about no characters
        self.assertGreater(len(status["health_issues"]), 0)


class TestSceneSaving(TestSnowflakeEngine):
    """Tests for scene plan and draft saving"""

    def test_save_scene_plan(self):
        """Test saving scene plan"""
        self.engine.init_project("Test Novel")

        plan_content = "This is the plan for scene 1"
        self.engine.save_scene_plan(1, plan_content)

        plan_file = Path(self.temp_dir) / "test_novel" / "scenes" / "scene_001_plan.md"
        self.assertTrue(plan_file.exists())

        content = plan_file.read_text(encoding='utf-8')
        self.assertIn(plan_content, content)

    def test_save_scene_draft(self):
        """Test saving scene draft"""
        self.engine.init_project("Test Novel")

        draft_content = "This is the draft for scene 1"
        self.engine.save_scene_draft(1, draft_content)

        draft_file = Path(self.temp_dir) / "test_novel" / "drafts" / "scene_001.md"
        self.assertTrue(draft_file.exists())

        content = draft_file.read_text(encoding='utf-8')
        self.assertIn(draft_content, content)


class TestDisasterTracking(TestSnowflakeEngine):
    """Tests for disaster logging"""

    def test_log_disaster(self):
        """Test logging a disaster"""
        self.engine.init_project("Test Novel")

        self.engine.log_disaster(1, "First major disaster")

        metadata_path = Path(self.temp_dir) / "test_novel" / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        self.assertEqual(len(metadata["disasters"]), 1)
        self.assertEqual(metadata["disasters"][0]["level"], 1)
        self.assertEqual(metadata["disasters"][0]["description"], "First major disaster")

    def test_log_multiple_disasters(self):
        """Test logging all three disasters"""
        self.engine.init_project("Test Novel")

        self.engine.log_disaster(1, "Disaster 1")
        self.engine.log_disaster(2, "Disaster 2")
        self.engine.log_disaster(3, "Disaster 3")

        status = self.engine.get_status()
        self.assertEqual(status["disasters_logged"], 3)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
