import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

# --- Config ---
DATE = "2025-09-13"
URL = f"https://clubspark.lta.org.uk/v0/VenueBooking/FinsburyPark/GetVenueSessions?resourceID=&startDate={DATE}&endDate={DATE}&roleId="

# Pushover credentials (set these as environment variables)
PUSHOVER_USER_KEY = "***REMOVED***"
PUSHOVER_API_TOKEN = "***REMOVED***"

# Notification mode toggle
# True: Only notify when there are NEW slots (compared to previous run)
# False: Always notify when ANY slots are available (original behavior)
NOTIFY_ONLY_ON_CHANGES = True


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
def check_availability():
    # Load previous state
    previous_availability = load_previous_state().get("availability", [])

    r = requests.get(URL)
    data = r.json()

    earliest = data["EarliestStartTime"]
    latest = data["LatestEndTime"]
    min_interval = data["MinimumInterval"]

    current_availability = []

    for resource in data["Resources"]:
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
            current_availability.append(result)

    # Determine what to notify about based on the toggle
    if NOTIFY_ONLY_ON_CHANGES:
        # Only notify on new slots
        new_slots = get_new_slots(current_availability, previous_availability)

        if new_slots:
            print(f"\n🎾 {len(new_slots)} new slot(s) detected!")
            message = f"New courts available on {DATE}:\n\n" + "\n".join(new_slots)
            send_pushover_notification(message)
        elif current_availability:
            print("\n✓ All slots were already known (no notification sent)")
        else:
            print("\n✗ No availability found")
    else:
        # Original behavior: notify whenever there's ANY availability
        if current_availability:
            print(f"\n🎾 {len(current_availability)} slot(s) available")
            message = f"Courts available on {DATE}:\n\n" + "\n".join(
                current_availability
            )
            send_pushover_notification(message)
        else:
            print("\n✗ No availability found")

    # Save current state for next run (only if tracking changes)
    if NOTIFY_ONLY_ON_CHANGES:
        save_current_state(
            {
                "availability": current_availability,
                "last_checked": datetime.now().isoformat(),
            }
        )


if __name__ == "__main__":
    check_availability()
