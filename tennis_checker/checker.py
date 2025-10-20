"""Core availability checking logic."""

from datetime import datetime
from typing import Dict, List, Optional

import requests

from .config import Config
from .notifier import PushoverNotifier
from .utils import expand_time_slots, format_date, get_new_slots, parse_availability


class AvailabilityChecker:
    """Check tennis court availability across multiple venues."""

    def __init__(
        self,
        config: Config,
        notifier: Optional[PushoverNotifier] = None,
        notify_only_on_changes: bool = True,
    ):
        """
        Initialize availability checker.

        Args:
            config: Configuration manager
            notifier: Notification handler (optional)
            notify_only_on_changes: Only send notifications for new availability
        """
        self.config = config
        self.notifier = notifier
        self.notify_only_on_changes = notify_only_on_changes

    def check_venue(self, venue: Dict, date: str) -> List[str]:
        """
        Check availability for a single venue.

        Args:
            venue: Venue configuration dictionary
            date: Date to check (YYYY-MM-DD format)

        Returns:
            List of availability strings (e.g., "Court 1: 7am-8am")
        """
        venue_name = venue["name"]
        url = venue["url_template"].format(date=date)

        print(f"\n{'=' * 60}")
        print(f"Checking {venue_name}...")
        print(f"{'=' * 60}")

        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching data for {venue_name}: {e}")
            return []

        earliest = data.get("EarliestStartTime", 420)
        latest = data.get("LatestEndTime", 1320)
        min_interval = data.get("MinimumInterval", 60)

        venue_availability = []

        for resource in data.get("Resources", []):
            court_name = resource["Name"]
            day = next(
                (d for d in resource["Days"] if d["Date"].startswith(date)), None
            )
            if not day:
                print(f"{court_name}: No data for {date}")
                continue

            slots = parse_availability(resource, day, earliest, latest, min_interval)

            if not slots:
                print(f"{court_name}: No availability")
            else:
                # Expand time slots to show individual hour start times
                hour_starts = expand_time_slots(slots)
                result = f"{court_name}: {', '.join(hour_starts)}"
                print(result)
                venue_availability.append(result)

        return venue_availability

    def check_all_venues(
        self, date: str, enabled_venue_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Check availability for all enabled venues.

        Args:
            date: Date to check (YYYY-MM-DD format)
            enabled_venue_ids: List of venue IDs to check (None = all enabled)

        Returns:
            Dictionary with venue results and notification status
        """
        venues = self.config.get_enabled_venues(enabled_venue_ids)

        if not venues:
            print("No venues enabled. Please check venues.json")
            return {"venues": {}, "notified": False}

        # Load previous state
        previous_state = self.config.load_state()

        # Track results across all venues
        all_results = {}
        new_availability_by_venue = {}
        total_new_slots = 0

        # Check each venue
        for venue in venues:
            venue_id = venue["id"]
            venue_name = venue["name"]

            current_availability = self.check_venue(venue, date)

            # Store current results
            all_results[venue_id] = {
                "name": venue_name,
                "availability": current_availability,
            }

            # Compare with previous state if tracking changes
            if self.notify_only_on_changes:
                previous_availability = previous_state.get(venue_id, {}).get(
                    "availability", []
                )
                new_slots = get_new_slots(current_availability, previous_availability)

                if new_slots:
                    new_availability_by_venue[venue_name] = new_slots
                    total_new_slots += len(new_slots)

                if current_availability:
                    if new_slots:
                        print(
                            f"\n🎾 {len(new_slots)} new slot(s) detected at {venue_name}"
                        )
                    else:
                        print(f"\n✓ All slots at {venue_name} were already known")
                else:
                    print(f"\n✗ No availability at {venue_name}")

        # Print summary
        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")

        # Send notification based on mode
        notified = False
        if self.notify_only_on_changes:
            if new_availability_by_venue:
                print(f"\n🎾 {total_new_slots} total new slot(s) across all venues!")
                notified = self._send_notification(
                    date, new_availability_by_venue, "New courts available"
                )
            else:
                total_slots = sum(len(v["availability"]) for v in all_results.values())
                if total_slots > 0:
                    print(
                        f"✓ {total_slots} slot(s) found, but all were already known (no notification sent)"
                    )
                else:
                    print("✗ No availability found at any venue")
        else:
            # Original behavior: notify whenever there's ANY availability
            total_slots = sum(len(v["availability"]) for v in all_results.values())

            if total_slots > 0:
                print(f"🎾 {total_slots} slot(s) available across all venues")
                notified = self._send_notification(
                    date,
                    {
                        venue_data["name"]: venue_data["availability"]
                        for venue_data in all_results.values()
                        if venue_data["availability"]
                    },
                    "Courts available",
                )
            else:
                print("✗ No availability found at any venue")

        # Save current state for next run (only if tracking changes)
        if self.notify_only_on_changes:
            self.config.save_state(
                {
                    **{
                        venue_id: {
                            "name": data["name"],
                            "availability": data["availability"],
                        }
                        for venue_id, data in all_results.items()
                    },
                    "last_checked": datetime.now().isoformat(),
                }
            )

        return {
            "venues": all_results,
            "notified": notified,
            "new_slots": (
                new_availability_by_venue if self.notify_only_on_changes else None
            ),
        }

    def _send_notification(
        self, date: str, availability_by_venue: Dict[str, List[str]], prefix: str
    ) -> bool:
        """
        Send notification grouped by venue.

        Args:
            date: Date being checked (YYYY-MM-DD format)
            availability_by_venue: Dictionary of venue_name -> availability list
            prefix: Prefix for notification title

        Returns:
            True if notification was sent successfully
        """
        if not self.notifier:
            return False

        # Format date for notification
        formatted_date = format_date(date)

        # Build notification message grouped by venue
        message_parts = [f"{prefix} on {formatted_date}:\n"]
        for venue_name, slots in availability_by_venue.items():
            message_parts.append(f"\n📍 {venue_name}:")
            message_parts.extend([f"  • {slot}" for slot in slots])

        message = "\n".join(message_parts)
        return self.notifier.send(message, "Tennis Courts Available")
