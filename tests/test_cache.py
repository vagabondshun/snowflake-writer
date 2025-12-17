"""
Unit tests for caching functionality

Run with: python -m pytest tests/test_cache.py
Or: python tests/test_cache.py
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story_engine import SnowflakeEngine


class TestCaching(unittest.TestCase):
    """Test suite for caching functionality"""

    def setUp(self):
        """Create a temporary workspace for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = SnowflakeEngine(workspace_dir=self.temp_dir)
        self.engine.init_project("Cache Test")

    def tearDown(self):
        """Clean up temporary workspace after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_stats_initial(self):
        """Test that cache stats start at zero"""
        stats = self.engine.get_cache_stats()

        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["hit_rate_percent"], 0)

    def test_step_output_cache_miss(self):
        """Test cache miss when reading step for first time"""
        self.engine.save_step_output(1, "Step 1 content", "One-Sentence Hook")

        # Clear stats to test fresh read
        self.engine.clear_cache_stats()

        # First read - should be cache miss
        content = self.engine.get_step_output(1)
        stats = self.engine.get_cache_stats()

        self.assertIn("Step 1 content", content)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)

    def test_step_output_cache_hit(self):
        """Test cache hit when reading step second time"""
        self.engine.save_step_output(1, "Step 1 content", "One-Sentence Hook")

        # Clear stats
        self.engine.clear_cache_stats()

        # First read - cache miss
        self.engine.get_step_output(1)

        # Second read - should be cache hit
        content = self.engine.get_step_output(1)
        stats = self.engine.get_cache_stats()

        self.assertIn("Step 1 content", content)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_percent"], 50.0)

    def test_character_cache_miss_then_hit(self):
        """Test character caching"""
        self.engine.update_character("Alice", {"role": "protagonist"})

        # Clear stats
        self.engine.clear_cache_stats()

        # First read - cache miss
        chars1 = self.engine.get_all_characters()
        stats1 = self.engine.get_cache_stats()

        self.assertEqual(len(chars1), 1)
        self.assertEqual(stats1["misses"], 1)
        self.assertEqual(stats1["hits"], 0)

        # Second read - cache hit
        chars2 = self.engine.get_all_characters()
        stats2 = self.engine.get_cache_stats()

        self.assertEqual(len(chars2), 1)
        self.assertEqual(stats2["hits"], 1)
        self.assertEqual(stats2["misses"], 1)

    def test_scene_list_cache_miss_then_hit(self):
        """Test scene list caching"""
        scenes = [
            {"scene_number": 1, "gist": "Opening scene"},
            {"scene_number": 2, "gist": "Second scene"}
        ]
        self.engine.update_scene_list(scenes)

        # Clear stats
        self.engine.clear_cache_stats()

        # First read - cache miss
        scenes1 = self.engine.get_scene_list()
        stats1 = self.engine.get_cache_stats()

        self.assertEqual(len(scenes1), 2)
        self.assertEqual(stats1["misses"], 1)

        # Second read - cache hit
        scenes2 = self.engine.get_scene_list()
        stats2 = self.engine.get_cache_stats()

        self.assertEqual(len(scenes2), 2)
        self.assertEqual(stats2["hits"], 1)

    def test_cache_invalidation_on_character_update(self):
        """Test that cache is invalidated when character is updated"""
        self.engine.update_character("Alice", {"role": "protagonist"})

        # Read to populate cache
        self.engine.get_all_characters()

        # Clear stats
        self.engine.clear_cache_stats()

        # Update character - should invalidate cache
        self.engine.update_character("Bob", {"role": "antagonist"})

        # Next read should be cache miss
        chars = self.engine.get_all_characters()
        stats = self.engine.get_cache_stats()

        self.assertEqual(len(chars), 2)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)

    def test_cache_invalidation_on_scene_update(self):
        """Test that cache is invalidated when scene list is updated"""
        scenes = [{"scene_number": 1, "gist": "Scene 1"}]
        self.engine.update_scene_list(scenes)

        # Read to populate cache
        self.engine.get_scene_list()

        # Clear stats
        self.engine.clear_cache_stats()

        # Update scene list - should invalidate cache
        scenes2 = [
            {"scene_number": 1, "gist": "Scene 1"},
            {"scene_number": 2, "gist": "Scene 2"}
        ]
        self.engine.update_scene_list(scenes2)

        # Next read should be cache miss
        result = self.engine.get_scene_list()
        stats = self.engine.get_cache_stats()

        self.assertEqual(len(result), 2)
        self.assertEqual(stats["misses"], 1)

    def test_cache_invalidation_on_step_save(self):
        """Test that step cache is invalidated when step is saved"""
        self.engine.save_step_output(1, "Original content", "Hook")

        # Read to populate cache
        self.engine.get_step_output(1)

        # Clear stats
        self.engine.clear_cache_stats()

        # Update step - should invalidate that step's cache
        self.engine.save_step_output(1, "Updated content", "Hook")

        # Next read should be cache miss
        content = self.engine.get_step_output(1)
        stats = self.engine.get_cache_stats()

        self.assertIn("Updated content", content)
        self.assertEqual(stats["misses"], 1)

    def test_cache_cleared_on_project_switch(self):
        """Test that cache is cleared when switching projects"""
        # Add some data
        self.engine.update_character("Alice", {"role": "protagonist"})
        self.engine.get_all_characters()  # Populate cache

        # Create another project
        self.engine.init_project("Another Project")

        # Clear stats to test fresh
        self.engine.clear_cache_stats()

        # Reading from new project should be cache miss
        chars = self.engine.get_all_characters()
        stats = self.engine.get_cache_stats()

        self.assertEqual(len(chars), 0)  # New project has no characters
        self.assertEqual(stats["misses"], 1)

    def test_cache_performance_benefit(self):
        """Test that caching provides performance benefit"""
        import time

        # Create multiple steps
        for i in range(1, 6):
            self.engine.save_step_output(i, f"Content for step {i}", f"Step {i}")

        # Clear cache and stats
        self.engine._clear_cache()
        self.engine.clear_cache_stats()

        # First read (cold cache)
        start = time.time()
        for i in range(1, 6):
            self.engine.get_step_output(i)
        cold_time = time.time() - start

        # Second read (warm cache)
        start = time.time()
        for i in range(1, 6):
            self.engine.get_step_output(i)
        warm_time = time.time() - start

        stats = self.engine.get_cache_stats()

        # Cache should be faster
        self.assertLess(warm_time, cold_time)

        # Should have 5 hits from second read
        self.assertEqual(stats["hits"], 5)
        self.assertEqual(stats["misses"], 5)
        self.assertEqual(stats["hit_rate_percent"], 50.0)

    def test_clear_cache_stats(self):
        """Test clearing cache stats"""
        self.engine.save_step_output(1, "Content", "Hook")
        self.engine.get_step_output(1)
        self.engine.get_step_output(1)

        # Should have some stats
        stats = self.engine.get_cache_stats()
        self.assertGreater(stats["total_requests"], 0)

        # Clear stats
        self.engine.clear_cache_stats()

        # Should be reset
        stats = self.engine.get_cache_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
