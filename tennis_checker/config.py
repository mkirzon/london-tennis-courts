"""Configuration management for tennis checker."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class Config:
    """Configuration manager for the tennis checker."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_dir: Directory containing config files. Defaults to ../config
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        self.venues_file = self.config_dir / "venues.json"
        self.state_file = self.config_dir / "availability_state.json"

    def load_venues(self) -> List[Dict]:
        """Load venue configurations from venues.json."""
        if not self.venues_file.exists():
            print(f"Error: {self.venues_file} not found")
            return []

        try:
            with open(self.venues_file, "r") as f:
                data = json.load(f)
                return data.get("venues", [])
        except Exception as e:
            print(f"Error loading venues: {e}")
            return []

    def get_enabled_venues(
        self, enabled_venue_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get list of venues to check.

        Args:
            enabled_venue_ids: List of venue IDs to enable. If None or empty,
                             returns all venues marked as enabled in venues.json

        Returns:
            List of venue configuration dictionaries
        """
        all_venues = self.load_venues()

        if enabled_venue_ids is None or len(enabled_venue_ids) == 0:
            return [v for v in all_venues if v.get("enabled", True)]

        return [v for v in all_venues if v["id"] in enabled_venue_ids]

    def load_state(self) -> Dict:
        """Load the previous availability state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load previous state: {e}")
                return {}
        return {}

    def save_state(self, state_data: Dict) -> None:
        """Save the current availability state to file."""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
