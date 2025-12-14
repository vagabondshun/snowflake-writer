"""
Snowflake Story Engine - State Manager for Fiction Writing
Handles project initialization, character management, scene tracking, and context retrieval.
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SnowflakeEngine:
    """Core engine for managing Snowflake Method story projects."""

    def __init__(self, workspace_dir: str = "./snowflake_projects"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        self.current_project = None

    def init_project(self, title: str) -> Dict[str, Any]:
        """
        Initialize a new novel project with directory structure.

        Args:
            title: The working title of the novel

        Returns:
            Project metadata dictionary
        """
        # Sanitize title for folder name
        folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        folder_name = folder_name.replace(' ', '_').lower()

        project_path = self.workspace_dir / folder_name

        # Create directory structure
        project_path.mkdir(exist_ok=True)
        (project_path / "characters").mkdir(exist_ok=True)
        (project_path / "scenes").mkdir(exist_ok=True)
        (project_path / "drafts").mkdir(exist_ok=True)
        (project_path / "steps").mkdir(exist_ok=True)

        # Initialize metadata
        metadata = {
            "title": title,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "current_step": 0,
            "completed_steps": [],
            "disasters": [],
            "settings": {
                "genre": None,
                "target_word_count": 80000,
                "pov_style": None
            }
        }

        # Save metadata
        metadata_path = project_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        self.current_project = project_path
        return metadata

    def load_project(self, title: str) -> Optional[Dict[str, Any]]:
        """Load an existing project."""
        folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        folder_name = folder_name.replace(' ', '_').lower()

        project_path = self.workspace_dir / folder_name
        metadata_path = project_path / "metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        self.current_project = project_path
        return metadata

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update project metadata."""
        if not self.current_project:
            raise ValueError("No project loaded")

        metadata_path = self.current_project / "metadata.json"

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata.update(updates)
        metadata["last_modified"] = datetime.now().isoformat()

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def update_character(self, name: str, data: Dict[str, Any]) -> None:
        """
        Save or update a character profile.

        Args:
            name: Character name
            data: Character data including values, ambitions, goals, etc.
        """
        if not self.current_project:
            raise ValueError("No project loaded")

        # Sanitize character name for filename
        filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        filename = filename.replace(' ', '_').lower() + ".json"

        char_path = self.current_project / "characters" / filename

        character_data = {
            "name": name,
            "last_updated": datetime.now().isoformat(),
            **data
        }

        with open(char_path, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=2)

    def get_character(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a character profile."""
        if not self.current_project:
            raise ValueError("No project loaded")

        filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        filename = filename.replace(' ', '_').lower() + ".json"

        char_path = self.current_project / "characters" / filename

        if not char_path.exists():
            return None

        with open(char_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all character profiles."""
        if not self.current_project:
            raise ValueError("No project loaded")

        characters = []
        char_dir = self.current_project / "characters"

        for char_file in char_dir.glob("*.json"):
            with open(char_file, 'r', encoding='utf-8') as f:
                characters.append(json.load(f))

        return characters

    def update_scene_list(self, scenes: List[Dict[str, Any]]) -> None:
        """
        Update the master scene list (spreadsheet).

        Args:
            scenes: List of scene dictionaries with keys like:
                    - scene_number
                    - pov_character
                    - gist
                    - conflict
                    - disaster
                    - outcome
        """
        if not self.current_project:
            raise ValueError("No project loaded")

        scene_list_path = self.current_project / "scenes" / "scene_list.csv"

        # Define CSV headers
        headers = ["scene_number", "pov_character", "gist", "conflict", "disaster", "outcome", "notes"]

        with open(scene_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(scenes)

        # Also save as JSON for easier programmatic access
        scene_json_path = self.current_project / "scenes" / "scene_list.json"
        with open(scene_json_path, 'w', encoding='utf-8') as f:
            json.dump(scenes, f, indent=2)

    def get_scene_list(self) -> List[Dict[str, Any]]:
        """Retrieve the scene list."""
        if not self.current_project:
            raise ValueError("No project loaded")

        scene_json_path = self.current_project / "scenes" / "scene_list.json"

        if not scene_json_path.exists():
            return []

        with open(scene_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_step_output(self, step_number: int, content: str, step_name: str = None) -> None:
        """Save the output of a specific step."""
        if not self.current_project:
            raise ValueError("No project loaded")

        step_file = self.current_project / "steps" / f"step_{step_number:02d}.md"

        with open(step_file, 'w', encoding='utf-8') as f:
            f.write(f"# Step {step_number}")
            if step_name:
                f.write(f": {step_name}")
            f.write(f"\n\nGenerated: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(content)

    def get_step_output(self, step_number: int) -> Optional[str]:
        """Retrieve the output of a specific step."""
        if not self.current_project:
            raise ValueError("No project loaded")

        step_file = self.current_project / "steps" / f"step_{step_number:02d}.md"

        if not step_file.exists():
            return None

        with open(step_file, 'r', encoding='utf-8') as f:
            return f.read()

    def log_disaster(self, disaster_level: int, description: str) -> None:
        """
        Track a major disaster/plot point.

        Args:
            disaster_level: 1, 2, or 3
            description: Description of the disaster
        """
        if not self.current_project:
            raise ValueError("No project loaded")

        metadata_path = self.current_project / "metadata.json"

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        disaster_entry = {
            "level": disaster_level,
            "description": description,
            "logged_at": datetime.now().isoformat()
        }

        # Ensure disasters list exists
        if "disasters" not in metadata:
            metadata["disasters"] = []

        # Update or append disaster
        existing_idx = next((i for i, d in enumerate(metadata["disasters"]) if d["level"] == disaster_level), None)

        if existing_idx is not None:
            metadata["disasters"][existing_idx] = disaster_entry
        else:
            metadata["disasters"].append(disaster_entry)

        metadata["disasters"].sort(key=lambda x: x["level"])
        metadata["last_modified"] = datetime.now().isoformat()

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def get_context(self, step: int) -> Dict[str, Any]:
        """
        Retrieve relevant context for a specific step (RAG-lite behavior).

        Args:
            step: Step number (1-10)

        Returns:
            Dictionary containing relevant data for the step
        """
        if not self.current_project:
            raise ValueError("No project loaded")

        context = {
            "step": step,
            "metadata": None,
            "previous_steps": {},
            "characters": [],
            "scenes": [],
            "disasters": []
        }

        # Load metadata
        metadata_path = self.current_project / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                context["metadata"] = json.load(f)
                context["disasters"] = context["metadata"].get("disasters", [])

        # Step-specific context loading
        if step == 1:
            # No previous context needed
            pass

        elif step == 2:
            # Need Step 1 output
            context["previous_steps"][1] = self.get_step_output(1)

        elif step == 3:
            # Need Steps 1-2
            context["previous_steps"][1] = self.get_step_output(1)
            context["previous_steps"][2] = self.get_step_output(2)

        elif step == 4:
            # Need Step 2
            context["previous_steps"][2] = self.get_step_output(2)

        elif step == 5:
            # Need Step 3 and characters
            context["previous_steps"][3] = self.get_step_output(3)
            context["characters"] = self.get_all_characters()

        elif step == 6:
            # Need Step 4
            context["previous_steps"][4] = self.get_step_output(4)

        elif step == 7:
            # Need all previous character work
            context["previous_steps"][3] = self.get_step_output(3)
            context["previous_steps"][5] = self.get_step_output(5)
            context["characters"] = self.get_all_characters()

        elif step == 8:
            # Need Step 6 (master plan)
            context["previous_steps"][6] = self.get_step_output(6)
            context["characters"] = self.get_all_characters()

        elif step in [9, 10]:
            # Need EVERYTHING for drafting
            for i in range(1, 9):
                output = self.get_step_output(i)
                if output:
                    context["previous_steps"][i] = output

            context["characters"] = self.get_all_characters()
            context["scenes"] = self.get_scene_list()

        return context

    def get_status(self) -> Dict[str, Any]:
        """Get current project status and health check."""
        if not self.current_project:
            raise ValueError("No project loaded")

        metadata_path = self.current_project / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Count files
        char_count = len(list((self.current_project / "characters").glob("*.json")))
        scene_list = self.get_scene_list()
        completed_steps = []

        for i in range(1, 11):
            if (self.current_project / "steps" / f"step_{i:02d}.md").exists():
                completed_steps.append(i)

        # Health checks
        health_issues = []

        if 2 in completed_steps and len(metadata.get("disasters", [])) < 3:
            health_issues.append("Missing disaster definitions (should have 3 by Step 2)")

        if 3 in completed_steps and char_count == 0:
            health_issues.append("No characters defined after Step 3")

        if 8 in completed_steps and len(scene_list) == 0:
            health_issues.append("No scenes defined after Step 8")

        return {
            "project_title": metadata["title"],
            "current_step": metadata.get("current_step", 0),
            "completed_steps": completed_steps,
            "characters_defined": char_count,
            "scenes_planned": len(scene_list),
            "disasters_logged": len(metadata.get("disasters", [])),
            "health_issues": health_issues,
            "last_modified": metadata["last_modified"]
        }


# Convenience functions for direct use
_engine = None

def get_engine() -> SnowflakeEngine:
    """Get or create the global engine instance."""
    global _engine
    if _engine is None:
        _engine = SnowflakeEngine()
    return _engine


def init_project(title: str) -> Dict[str, Any]:
    """Initialize a new project."""
    return get_engine().init_project(title)


def load_project(title: str) -> Optional[Dict[str, Any]]:
    """Load an existing project."""
    return get_engine().load_project(title)


def update_character(name: str, data: Dict[str, Any]) -> None:
    """Update a character profile."""
    get_engine().update_character(name, data)


def update_scene_list(scenes: List[Dict[str, Any]]) -> None:
    """Update the scene list."""
    get_engine().update_scene_list(scenes)


def get_context(step: int) -> Dict[str, Any]:
    """Get context for a step."""
    return get_engine().get_context(step)


def log_disaster(disaster_level: int, description: str) -> None:
    """Log a disaster/plot point."""
    get_engine().log_disaster(disaster_level, description)


def get_status() -> Dict[str, Any]:
    """Get project status."""
    return get_engine().get_status()
