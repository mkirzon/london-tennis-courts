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
        # Directory to hold state files. Using a subdirectory avoids cluttering
        # the main config folder when multiple dates are tracked independently.
        self.state_dir = self.config_dir / "state"
        # Backwards-compatible single-file state (used when no date is provided)
        self.legacy_state_file = self.config_dir / "availability_state.json"

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

    def load_state(self, date: Optional[str] = None) -> Dict:
        """
        Load the previous availability state from file.

        Args:
            date: Optional date string (YYYY-MM-DD). If provided, load the
                  per-date state file from the `state/` subdirectory. If not
                  provided, fall back to the legacy single-file state.

        Returns:
            Parsed JSON dict of the saved state, or empty dict on error.
        """
        # If a date is provided, use per-date state file under state/
        try:
            if date:
                state_path = self.state_dir / f"availability_state_{date}.json"
            else:
                state_path = self.legacy_state_file

            if state_path.exists():
                with open(state_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load previous state: {e}")

        return {}

    def save_state(self, state_data: Dict, date: Optional[str] = None) -> None:
        """
        Save the current availability state to file.

        Args:
            state_data: JSON-serializable dict to write.
            date: Optional date string (YYYY-MM-DD). If provided, save to a
                  per-date file under the `state/` subdirectory. If not
                  provided, save to the legacy single-file state.
        """
        try:
            if date:
                # Ensure state directory exists
                self.state_dir.mkdir(parents=True, exist_ok=True)
                state_path = self.state_dir / f"availability_state_{date}.json"
            else:
                # Ensure config directory exists for legacy file
                self.legacy_state_file.parent.mkdir(parents=True, exist_ok=True)
                state_path = self.legacy_state_file

            with open(state_path, "w") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
