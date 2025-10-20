import os
from datetime import datetime, timedelta

import requests

# --- Config ---
DATE = "2025-09-13"
URL = f"https://clubspark.lta.org.uk/v0/VenueBooking/FinsburyPark/GetVenueSessions?resourceID=&startDate={DATE}&endDate={DATE}&roleId="

# Pushover credentials (set these as environment variables)
PUSHOVER_USER_KEY = "***REMOVED***"
PUSHOVER_API_TOKEN = "***REMOVED***"


# --- Helpers ---
def minutes_to_time(m):
    """Convert minutes from midnight (e.g., 420) to HH:MM string."""
    h, mins = divmod(m, 60)
    return f"{h:02d}:{mins:02d}"


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
    r = requests.get(URL)
    data = r.json()

    earliest = data["EarliestStartTime"]
    latest = data["LatestEndTime"]
    min_interval = data["MinimumInterval"]

    availability_found = []

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
            availability_found.append(result)

    if availability_found:
        message = f"Courts available on {DATE}:\n\n" + "\n".join(availability_found)
        send_pushover_notification(message)


if __name__ == "__main__":
    check_availability()
