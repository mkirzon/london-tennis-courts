# Tennis Court Availability Checker

A Python script that checks tennis court availability at multiple venues (via ClubSpark LTA API) and sends push notifications via Pushover when courts are available.

## Features

- **Multi-venue support**: Check availability across multiple tennis parks
- Checks court availability for a specific date
- Converts time slots from minutes-since-midnight to human-readable format (e.g., "7am", "2pm")
- Sends push notifications via Pushover grouped by venue
- Optional state tracking to only notify on NEW availability (not on every run)
- Per-venue state tracking for accurate change detection

## Configuration

### Main Script Configuration

Edit the following variables in `check_availability.py`:

- `DATE`: Target date to check (format: "YYYY-MM-DD")
- `PUSHOVER_USER_KEY`: Your Pushover user key
- `PUSHOVER_API_TOKEN`: Your Pushover API token
- `NOTIFY_ONLY_ON_CHANGES`: Toggle notification behavior (see below)
- `ENABLED_VENUES`: List of venue IDs to check (see Venue Configuration below)

### Venue Configuration

Venues are configured in `venues.json`. Each venue has:

```json
{
  "id": "unique_venue_id",
  "name": "Display Name",
  "url_template": "https://clubspark.lta.org.uk/v0/VenueBooking/{VenueName}/GetVenueSessions?resourceID=&startDate={date}&endDate={date}&roleId=",
  "enabled": true
}
```

**Adding a New Venue:**

1. Add a new entry to the `venues` array in `venues.json`
2. Set a unique `id` (e.g., `"hampstead_heath"`)
3. Set the `name` (e.g., `"Hampstead Heath"`)
4. Set the `url_template` with the correct venue path (replace `{VenueName}` with the actual venue name from the ClubSpark URL)
5. Set `enabled: true` to enable the venue

**Example venues.json:**

```json
{
  "venues": [
    {
      "id": "finsbury_park",
      "name": "Finsbury Park",
      "url_template": "https://clubspark.lta.org.uk/v0/VenueBooking/FinsburyPark/GetVenueSessions?resourceID=&startDate={date}&endDate={date}&roleId=",
      "enabled": true
    },
    {
      "id": "clissold_park",
      "name": "Clissold Park",
      "url_template": "https://clubspark.lta.org.uk/v0/VenueBooking/ClissoldPark/GetVenueSessions?resourceID=&startDate={date}&endDate={date}&roleId=",
      "enabled": true
    }
  ]
}
```

**Controlling Which Venues to Check:**

In `check_availability.py`, modify the `ENABLED_VENUES` list:

```python
# Check specific venues only
ENABLED_VENUES = ["finsbury_park", "clissold_park"]

# Check all venues marked as enabled in venues.json
ENABLED_VENUES = []  # or None
```

### Notification Modes

The `NOTIFY_ONLY_ON_CHANGES` toggle controls notification behavior:

- **`True` (default)**: Only sends notifications when NEW slots become available
  - Tracks availability between runs using `availability_state.json`
  - Prevents repeated notifications for the same available slots
  - Shows status per venue: "All slots were already known (no notification sent)"
  - State is tracked separately for each venue

- **`False`**: Original behavior - always notifies when ANY slots are available
  - Sends notification on every run if availability exists
  - Does not track state between runs

## Usage

```bash
python check_availability.py
```

## Dependencies

```bash
pip install requests
```

## Example Output

### Multi-Venue Output

When checking multiple venues, the output is organized by venue:

```
============================================================
Checking Finsbury Park...
============================================================
Court 1: 7am–8am, 9pm–10pm
Court 2: 7am–8am, 9pm–10pm
Court 3: No availability
Court 4 (no floodlights): 7am–8am
Court 5 (no floodlights): 7am–9am
Court 6: 7am–9am, 8pm–10pm
Court 7: 8pm–10pm
Court 8: 9pm–10pm

🎾 2 new slot(s) detected at Finsbury Park

============================================================
Checking Clissold Park...
============================================================
Court 1: 2pm–3pm
Court 2: 2pm–3pm, 5pm–6pm
Court 3: No availability
Court 4: 8pm–9pm
Court 5: No availability

🎾 3 new slot(s) detected at Clissold Park

============================================================
SUMMARY
============================================================

🎾 5 total new slot(s) across all venues!
✓ Pushover notification sent
```

### Notification Format

Notifications group availability by venue:

```
New courts available on 2025-09-13:

📍 Finsbury Park:
  • Court 1: 7am–8am, 9pm–10pm
  • Court 2: 7am–8am, 9pm–10pm

📍 Clissold Park:
  • Court 1: 2pm–3pm
  • Court 2: 2pm–3pm, 5pm–6pm
  • Court 4: 8pm–9pm
```

## State Tracking

When `NOTIFY_ONLY_ON_CHANGES = True`, the script creates an `availability_state.json` file organized by venue:

```json
{
  "finsbury_park": {
    "name": "Finsbury Park",
    "availability": [
      "Court 1: 7am–8am, 9pm–10pm",
      "Court 2: 7am–8am, 9pm–10pm"
    ]
  },
  "clissold_park": {
    "name": "Clissold Park",
    "availability": [
      "Court 1: 2pm–3pm",
      "Court 2: 2pm–3pm, 5pm–6pm"
    ]
  },
  "last_checked": "2025-01-15T10:30:45.123456"
}
```

This file tracks availability per venue and is used to compare between runs to determine which slots are newly available.

## API Response Format

The script fetches data from the ClubSpark LTA booking API. The response structure is documented below using `sample-finpark.json` as reference.

### Top-Level Structure

```json
{
  "TimeZone": "Europe/London",
  "EarliestStartTime": 420,
  "LatestEndTime": 1320,
  "MinimumInterval": 60,
  "Resources": [ /* array of court resources */ ]
}
```

**Key Fields:**
- `TimeZone`: Timezone for all times in the response
- `EarliestStartTime`: Earliest booking time in minutes since midnight (420 = 7:00 AM)
- `LatestEndTime`: Latest booking time in minutes since midnight (1320 = 10:00 PM)
- `MinimumInterval`: Minimum booking interval in minutes (typically 60)
- `Resources`: Array of court resources (see below)

### Resources (Courts)

Each resource represents a tennis court:

```json
{
  "ID": "f51042cf-95c8-4aca-acdf-0206636b5db0",
  "Name": "Court 1",
  "Number": 0,
  "Lighting": 1,
  "Surface": 6,
  "Days": [ /* array of day objects */ ]
}
```

**Key Fields:**
- `ID`: Unique identifier for the court
- `Name`: Display name (e.g., "Court 1", "Court 4 (no floodlights)")
- `Number`: Court number index (0-based)
- `Lighting`: Whether court has floodlights (1 = yes, 0 = no)
- `Surface`: Court surface type (6 appears to be hard court)
- `Days`: Array of days with session data

### Days

Each day contains session information for a specific date:

```json
{
  "Date": "2025-09-13T00:00:00",
  "Sessions": [ /* array of session objects */ ]
}
```

### Sessions (Time Slots)

Each session represents a bookable time slot:

```json
{
  "ID": "056427f3-f6e7-4dca-96b8-409c5925cef3",
  "Category": 0,
  "SubCategory": 0,
  "Name": "Aug - Sep (7pm)",
  "StartTime": 420,
  "EndTime": 480,
  "Interval": 60,
  "Capacity": 1,
  "Cost": 7.0,
  "CourtCost": 7.0,
  "LightingCost": 0.0
}
```

**Key Fields:**
- `ID`: Unique identifier for the session
- `Category`: Session category (see below)
- `Name`: Session description
- `StartTime`: Start time in minutes since midnight (420 = 7:00 AM)
- `EndTime`: End time in minutes since midnight (480 = 8:00 AM)
- `Interval`: Booking interval in minutes
- `Capacity`: Number of available slots (0 = fully booked, ≥1 = available)
- `Cost`: Total cost for booking
- `CourtCost`: Base court rental cost
- `LightingCost`: Additional lighting cost (if applicable)

### Session Categories

The `Category` field indicates the session type:

| Category | Description | Bookable? |
|----------|-------------|-----------|
| `0` | **Available for booking** | ✅ Yes (if Capacity ≥ 1) |
| `1000` | **Already booked** | ❌ No (Capacity = 0) |
| `2000` | **Club program/class** (e.g., lessons, coaching) | ❌ No (Capacity = 0) |
| `8000` | **Closed** (court unavailable) | ❌ No (Capacity = 0) |

**The script only considers sessions with:**
- `Category == 0` (Available for booking)
- `Capacity >= 1` (At least one slot available)

### Example Flow

1. Script loads venue configurations from `venues.json`
2. For each enabled venue:
   - Fetches JSON from API using the venue's URL template
   - Iterates through each `Resource` (court)
   - For each court, finds the target date in `Days`
   - Scans all `Sessions` for that date
   - Identifies available slots where `Category == 0` and `Capacity >= 1`
   - Converts `StartTime`/`EndTime` from minutes to human-readable format
3. Compares with previous state (if `NOTIFY_ONLY_ON_CHANGES = True`)
4. Groups new availability by venue and sends notification

### Time Conversion

Times are stored as minutes since midnight:
- `420` minutes = 7:00 AM
- `540` minutes = 9:00 AM
- `1260` minutes = 9:00 PM

The script's `minutes_to_time()` function converts these to 12-hour format (e.g., "7am", "9pm").
