import json
from datetime import datetime
from pathlib import Path

import requests

# --- Config ---
DATE = "2025-09-13"

# Pushover credentials (set these as environment variables)
PUSHOVER_USER_KEY = "***REMOVED***"
PUSHOVER_API_TOKEN = "***REMOVED***"

# Notification mode toggle
# True: Only notify when there are NEW slots (compared to previous run)
# False: Always notify when ANY slots are available (original behavior)
NOTIFY_ONLY_ON_CHANGES = True

# Venue selection
# List of venue IDs to check (from venues.json)
# Set to None or empty list to check all enabled venues
ENABLED_VENUES = ["finsbury_park", "clissold_park"]


# --- Venue Management ---
VENUES_FILE = Path(__file__).parent / "venues.json"


def load_venues():
    """Load venue configurations from venues.json."""
    if not VENUES_FILE.exists():
        print(f"Error: {VENUES_FILE} not found")
        return []

    try:
        with open(VENUES_FILE, "r") as f:
            data = json.load(f)
            return data.get("venues", [])
    except Exception as e:
        print(f"Error loading venues: {e}")
        return []


def get_enabled_venues():
    """Get list of venues to check based on ENABLED_VENUES setting."""
    all_venues = load_venues()

    if ENABLED_VENUES is None or len(ENABLED_VENUES) == 0:
        return [v for v in all_venues if v.get("enabled", True)]

    return [v for v in all_venues if v["id"] in ENABLED_VENUES]


# --- State Management ---
STATE_FILE = Path(__file__).parent / "availability_state.json"


def load_previous_state():
    """Load the previous availability state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load previous state: {e}")
            return {}
    return {}


def save_current_state(availability_data):
    """Save the current availability state to file."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(availability_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save state: {e}")


def get_new_slots(current_availability, previous_availability):
    """
    Compare current and previous availability to find new slots.
    Returns a list of only the newly available slots.
    """
    new_slots = []

    for court_result in current_availability:
        # Check if this exact result was in the previous state
        if court_result not in previous_availability:
            new_slots.append(court_result)

    return new_slots


# --- Helpers ---
def minutes_to_time(m):
    """Convert minutes from midnight (e.g., 420) to 12-hour format (e.g., 7am)."""
    h, mins = divmod(m, 60)

    # Convert to 12-hour format
    if h == 0:
        return "12am"
    elif h < 12:
        return f"{h}am"
    elif h == 12:
        return "12pm"
    else:
        return f"{h - 12}pm"


def parse_availability(resource, day, earliest, latest, min_interval):
    """Find available booking slots (Category 0 sessions with capacity)."""
    sessions = day.get("Sessions", [])
    availability = []

    for s in sessions:
        # Category 0 = Available for booking
        # Must have Capacity >= 1 to be bookable
        if s.get("Category") == 0 and s.get("Capacity", 0) >= 1:
            availability.append((s["StartTime"], s["EndTime"]))

    return sorted(availability, key=lambda x: x[0])


def send_pushover_notification(message, title="Tennis Court Availability"):
    """Send a notification via Pushover API."""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print("Warning: Pushover credentials not set. Skipping notification.")
        return False

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_API_TOKEN,
                "user": PUSHOVER_USER_KEY,
                "message": message,
                "title": title,
            },
        )

        if response.status_code == 200:
            print("✓ Pushover notification sent")
            return True
        else:
            print(f"Error sending Pushover notification: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Pushover notification: {e}")
        return False


# --- Main ---
def check_venue_availability(venue):
    """Check availability for a single venue."""
    venue_id = venue["id"]
    venue_name = venue["name"]
    url = venue["url_template"].format(date=DATE)

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
        day = next((d for d in resource["Days"] if d["Date"].startswith(DATE)), None)
        if not day:
            print(f"{court_name}: No data for {DATE}")
            continue

        slots = parse_availability(resource, day, earliest, latest, min_interval)

        if not slots:
            print(f"{court_name}: No availability")
        else:
            human_slots = [
                f"{minutes_to_time(start)}–{minutes_to_time(end)}"
                for start, end in slots
            ]
            result = f"{court_name}: {', '.join(human_slots)}"
            print(result)
            venue_availability.append(result)

    return venue_availability


def check_availability():
    """Check availability for all enabled venues."""
    venues = get_enabled_venues()

    if not venues:
        print("No venues enabled. Please check venues.json")
        return

    # Load previous state (organized by venue)
    previous_state = load_previous_state()

    # Track results across all venues
    all_results = {}
    new_availability_by_venue = {}
    total_new_slots = 0

    # Check each venue
    for venue in venues:
        venue_id = venue["id"]
        venue_name = venue["name"]

        current_availability = check_venue_availability(venue)

        # Store current results
        all_results[venue_id] = {
            "name": venue_name,
            "availability": current_availability,
        }

        # Compare with previous state if tracking changes
        if NOTIFY_ONLY_ON_CHANGES:
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

    # Send notification based on mode
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    if NOTIFY_ONLY_ON_CHANGES:
        if new_availability_by_venue:
            print(f"\n🎾 {total_new_slots} total new slot(s) across all venues!")

            # Build notification message grouped by venue
            message_parts = [f"New courts available on {DATE}:\n"]
            for venue_name, slots in new_availability_by_venue.items():
                message_parts.append(f"\n📍 {venue_name}:")
                message_parts.extend([f"  • {slot}" for slot in slots])

            message = "\n".join(message_parts)
            send_pushover_notification(message, "Tennis Courts Available")
        else:
            total_slots = sum(
                len(v["availability"]) for v in all_results.values()
            )
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

            # Build notification message grouped by venue
            message_parts = [f"Courts available on {DATE}:\n"]
            for venue_id, venue_data in all_results.items():
                if venue_data["availability"]:
                    message_parts.append(f"\n📍 {venue_data['name']}:")
                    message_parts.extend(
                        [f"  • {slot}" for slot in venue_data["availability"]]
                    )

            message = "\n".join(message_parts)
            send_pushover_notification(message, "Tennis Courts Available")
        else:
            print("✗ No availability found at any venue")

    # Save current state for next run (only if tracking changes)
    if NOTIFY_ONLY_ON_CHANGES:
        save_current_state(
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


if __name__ == "__main__":
    check_availability()
