"""Utility functions for tennis checker."""

from typing import List, Tuple


def minutes_to_time(minutes: int) -> str:
    """
    Convert minutes from midnight to 12-hour format.

    Args:
        minutes: Minutes since midnight (e.g., 420 for 7:00 AM)

    Returns:
        Time in 12-hour format (e.g., "7am", "2pm")
    """
    hours, _ = divmod(minutes, 60)

    # Convert to 12-hour format
    if hours == 0:
        return "12am"
    elif hours < 12:
        return f"{hours}am"
    elif hours == 12:
        return "12pm"
    else:
        return f"{hours - 12}pm"


def parse_availability(
    resource: dict, day: dict, earliest: int, latest: int, min_interval: int
) -> List[Tuple[int, int]]:
    """
    Find available booking slots from venue resource data.

    Args:
        resource: Resource (court) data from API
        day: Day data containing sessions
        earliest: Earliest booking time in minutes
        latest: Latest booking time in minutes
        min_interval: Minimum booking interval in minutes

    Returns:
        List of (start_time, end_time) tuples in minutes since midnight
    """
    sessions = day.get("Sessions", [])
    availability = []

    for session in sessions:
        # Category 0 = Available for booking
        # Must have Capacity >= 1 to be bookable
        if session.get("Category") == 0 and session.get("Capacity", 0) >= 1:
            availability.append((session["StartTime"], session["EndTime"]))

    return sorted(availability, key=lambda x: x[0])


def get_new_slots(
    current_availability: List[str], previous_availability: List[str]
) -> List[str]:
    """
    Compare current and previous availability to find new slots.

    Args:
        current_availability: Current availability strings
        previous_availability: Previous availability strings

    Returns:
        List of newly available slots
    """
    new_slots = []

    for court_result in current_availability:
        # Check if this exact result was in the previous state
        if court_result not in previous_availability:
            new_slots.append(court_result)

    return new_slots
