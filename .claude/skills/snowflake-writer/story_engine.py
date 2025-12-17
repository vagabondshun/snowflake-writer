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


# Custom Exceptions
class SnowflakeError(Exception):
    """Base exception for Snowflake Engine errors."""
    pass


class ProjectNotFoundError(SnowflakeError):
    """Raised when attempting to access a project that doesn't exist."""
    pass


class NoProjectLoadedError(SnowflakeError):
    """Raised when attempting an operation without a loaded project."""
    pass


class InvalidStepError(SnowflakeError):
    """Raised when attempting to access an invalid step number."""
    pass


class CharacterNotFoundError(SnowflakeError):
    """Raised when attempting to access a character that doesn't exist."""
    pass


class ValidationError(SnowflakeError):
    """Raised when data validation fails."""
    pass


class SnowflakeEngine:
    """Core engine for managing Snowflake Method story projects."""

    def __init__(self, workspace_dir: str = "./snowflake_projects"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        self.current_project = None

    def _validate_scene(self, scene: Dict[str, Any]) -> None:
        """
        Validate scene structure.

        Args:
            scene: Scene dictionary to validate

        Raises:
            ValidationError: If scene structure is invalid
        """
        required_fields = ["scene_number", "gist"]
        recommended_fields = ["conflict", "disaster", "outcome"]

        # Check required fields
        for field in required_fields:
            if field not in scene:
                raise ValidationError(f"Scene missing required field: '{field}'")

        # Validate scene_number type
        if not isinstance(scene["scene_number"], int):
            raise ValidationError(
                f"scene_number must be an integer, got {type(scene['scene_number']).__name__}"
            )

        # Validate scene_number is positive
        if scene["scene_number"] <= 0:
            raise ValidationError(f"scene_number must be positive, got {scene['scene_number']}")

        # Validate string fields are not empty
        if "gist" in scene and not scene["gist"].strip():
            raise ValidationError("Scene 'gist' cannot be empty")

    def _validate_character(self, data: Dict[str, Any]) -> None:
        """
        Validate character data structure.

        Args:
            data: Character data dictionary to validate

        Raises:
            ValidationError: If character data is invalid
        """
        # Name should be provided
        if "name" not in data:
            raise ValidationError("Character data missing required field: 'name'")

        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValidationError("Character 'name' must be a non-empty string")

        # Validate role if provided
        if "role" in data:
            valid_roles = ["protagonist", "antagonist", "supporting", "mentor", "sidekick", "systemic_antagonist"]
            if data["role"] not in valid_roles:
                # Warning, not error - allow custom roles
                pass

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects in the workspace.

        Returns:
            List of dictionaries containing project info (title, last_modified, current_step)
        """
        projects = []

        for project_dir in self.workspace_dir.iterdir():
            if not project_dir.is_dir():
                continue

            metadata_path = project_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                projects.append({
                    "title": metadata.get("title", project_dir.name),
                    "folder": project_dir.name,
                    "last_modified": metadata.get("last_modified", "Unknown"),
                    "current_step": metadata.get("current_step", 0),
                    "completed_steps": metadata.get("completed_steps", [])
                })
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted project files
                continue

        # Sort by last modified date (most recent first)
        projects.sort(key=lambda x: x["last_modified"], reverse=True)
        return projects

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
                "pov_style": None,
                "use_pov_mode": True  # Default to POV mode enabled
            }
        }

        # Save metadata
        metadata_path = project_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        self.current_project = project_path
        return metadata

    def load_project(self, title: str) -> Dict[str, Any]:
        """
        Load an existing project.

        Args:
            title: The project title

        Returns:
            Project metadata dictionary

        Raises:
            ProjectNotFoundError: If the project doesn't exist
        """
        folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        folder_name = folder_name.replace(' ', '_').lower()

        project_path = self.workspace_dir / folder_name
        metadata_path = project_path / "metadata.json"

        if not metadata_path.exists():
            raise ProjectNotFoundError(f"Project '{title}' not found at {project_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        self.current_project = project_path
        return metadata

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update project metadata."""
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        metadata_path = self.current_project / "metadata.json"

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata.update(updates)
        metadata["last_modified"] = datetime.now().isoformat()

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def set_pov_mode(self, enabled: bool) -> None:
        """
        Enable or disable POV (Point of View) mode.

        When POV mode is enabled:
        - Scene list should include pov_character field
        - Health checks will verify POV characters exist in Character Bible
        - Step 9 and 10 should reference POV character perspectives

        When POV mode is disabled:
        - Scenes can be written without specific POV assignments
        - Health checks skip POV-related validations
        - Useful for omniscient narrator or non-POV narrative styles

        Args:
            enabled: True to enable POV mode, False to disable

        Example:
            engine.set_pov_mode(False)  # Disable for omniscient narrator style
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        metadata_path = self.current_project / "metadata.json"

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Update the setting
        if "settings" not in metadata:
            metadata["settings"] = {}

        metadata["settings"]["use_pov_mode"] = enabled
        metadata["last_modified"] = datetime.now().isoformat()

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def get_pov_mode(self) -> bool:
        """
        Get current POV mode status.

        Returns:
            True if POV mode is enabled, False otherwise
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        metadata_path = self.current_project / "metadata.json"

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Default to True if not set (backward compatibility)
        return metadata.get("settings", {}).get("use_pov_mode", True)

    def update_character(self, name: str, data: Dict[str, Any]) -> None:
        """
        Save or update a character profile.

        Args:
            name: Character name
            data: Character data including values, ambitions, goals, etc.

        Raises:
            ValidationError: If character data is invalid
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        # Ensure name is in data for validation
        data_with_name = {"name": name, **data}

        # Validate character data
        self._validate_character(data_with_name)

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
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

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
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

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
                    - scene_number (required, int)
                    - pov_character (optional if POV mode disabled)
                    - gist (required, str)
                    - conflict (recommended, str)
                    - disaster (recommended, str)
                    - outcome (recommended, str)

        Raises:
            ValidationError: If scene data is invalid
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        # Validate all scenes before saving
        for i, scene in enumerate(scenes):
            try:
                self._validate_scene(scene)
            except ValidationError as e:
                raise ValidationError(f"Scene at index {i}: {str(e)}")

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
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        scene_json_path = self.current_project / "scenes" / "scene_list.json"

        if not scene_json_path.exists():
            return []

        with open(scene_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_scene_plan(self, scene_number: int, content: str) -> None:
        """
        Save a scene plan (Step 9 - Scene Architecture).

        Args:
            scene_number: The scene number
            content: The scene plan content
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        plan_file = self.current_project / "scenes" / f"scene_{scene_number:03d}_plan.md"

        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(f"# Scene {scene_number} - Plan\n\n")
            f.write(f"Created: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(content)

    def save_scene_draft(self, scene_number: int, content: str) -> None:
        """
        Save a scene draft (Step 10 - Drafting).

        Args:
            scene_number: The scene number
            content: The drafted prose
        """
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        draft_file = self.current_project / "drafts" / f"scene_{scene_number:03d}.md"

        with open(draft_file, 'w', encoding='utf-8') as f:
            f.write(f"# Scene {scene_number}\n\n")
            f.write(f"Drafted: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(content)

    def save_step_output(self, step_number: int, content: str, step_name: str = None) -> None:
        """Save the output of a specific step and update metadata."""
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        step_file = self.current_project / "steps" / f"step_{step_number:02d}.md"

        with open(step_file, 'w', encoding='utf-8') as f:
            f.write(f"# Step {step_number}")
            if step_name:
                f.write(f": {step_name}")
            f.write(f"\n\nGenerated: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(content)

        # Update metadata to track completion
        metadata_path = self.current_project / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if step_number not in metadata.get('completed_steps', []):
            metadata.setdefault('completed_steps', []).append(step_number)
            metadata['completed_steps'].sort()
            metadata['current_step'] = max(metadata['completed_steps'])
            metadata['last_modified'] = datetime.now().isoformat()

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

    def get_step_output(self, step_number: int) -> Optional[str]:
        """Retrieve the output of a specific step."""
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

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
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

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
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

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
        """Get current project status and enhanced health check."""
        if not self.current_project:
            raise NoProjectLoadedError("No project currently loaded. Use init_project() or load_project() first.")

        metadata_path = self.current_project / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Count files
        characters = self.get_all_characters()
        char_count = len(characters)
        scene_list = self.get_scene_list()
        completed_steps = []

        for i in range(1, 11):
            if (self.current_project / "steps" / f"step_{i:02d}.md").exists():
                completed_steps.append(i)

        # Count drafted scenes
        drafted_scenes = len(list((self.current_project / "drafts").glob("scene_*.md")))

        # Health checks
        health_issues = []
        health_warnings = []

        # Basic completeness checks
        if 2 in completed_steps and len(metadata.get("disasters", [])) < 3:
            health_issues.append("Missing disaster definitions (should have 3 by Step 2)")

        if 3 in completed_steps and char_count == 0:
            health_issues.append("No characters defined after Step 3")

        if 8 in completed_steps and len(scene_list) == 0:
            health_issues.append("No scenes defined after Step 8")

        # Character consistency checks
        # Only check POV consistency if POV mode is enabled
        pov_mode = metadata.get("settings", {}).get("use_pov_mode", True)
        if pov_mode and scene_list and characters:
            # Check if all POV characters exist in Character Bible
            pov_characters = set(scene.get("pov_character") for scene in scene_list if scene.get("pov_character"))
            character_names = set(char.get("name") for char in characters if char.get("name"))

            missing_pov = pov_characters - character_names
            if missing_pov:
                health_warnings.append(f"POV characters not in Character Bible: {', '.join(missing_pov)}")

        # Minimum character requirements
        if 3 in completed_steps:
            char_roles = [char.get("role") for char in characters]
            if "protagonist" not in char_roles:
                health_warnings.append("No protagonist defined")
            if "antagonist" not in char_roles and "systemic_antagonist" not in char_roles:
                health_warnings.append("No antagonist defined")

        # Scene balance check
        if len(scene_list) > 0:
            target_word_count = metadata.get("settings", {}).get("target_word_count", 80000)
            recommended_scenes = target_word_count // 1500  # Assuming ~1500 words per scene
            if len(scene_list) < recommended_scenes * 0.7:
                health_warnings.append(f"Scene count ({len(scene_list)}) may be low for target word count (recommended: ~{recommended_scenes})")
            elif len(scene_list) > recommended_scenes * 1.3:
                health_warnings.append(f"Scene count ({len(scene_list)}) may be high for target word count (recommended: ~{recommended_scenes})")

        # Calculate completion percentage
        step_weights = {1: 5, 2: 5, 3: 10, 4: 10, 5: 10, 6: 15, 7: 15, 8: 10, 9: 10, 10: 10}
        total_weight = sum(step_weights.values())
        completed_weight = sum(step_weights[step] for step in completed_steps)
        completion_percentage = int((completed_weight / total_weight) * 100)

        return {
            "project_title": metadata["title"],
            "current_step": metadata.get("current_step", 0),
            "completed_steps": completed_steps,
            "completion_percentage": completion_percentage,
            "characters_defined": char_count,
            "scenes_planned": len(scene_list),
            "scenes_drafted": drafted_scenes,
            "disasters_logged": len(metadata.get("disasters", [])),
            "health_issues": health_issues,
            "health_warnings": health_warnings,
            "last_modified": metadata["last_modified"],
            "target_word_count": metadata.get("settings", {}).get("target_word_count", 80000)
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


def save_scene_plan(scene_number: int, content: str) -> None:
    """Save a scene plan."""
    get_engine().save_scene_plan(scene_number, content)


def save_scene_draft(scene_number: int, content: str) -> None:
    """Save a scene draft."""
    get_engine().save_scene_draft(scene_number, content)


def list_projects() -> List[Dict[str, Any]]:
    """List all available projects."""
    return get_engine().list_projects()


def set_pov_mode(enabled: bool) -> None:
    """Enable or disable POV mode."""
    get_engine().set_pov_mode(enabled)


def get_pov_mode() -> bool:
    """Get current POV mode status."""
    return get_engine().get_pov_mode()
