# Tennis Court Availability Checker

A Python script that checks tennis court availability at Finsbury Park (via ClubSpark LTA API) and sends push notifications via Pushover when courts are available.

## Features

- Checks court availability for a specific date
- Converts time slots from minutes-since-midnight to human-readable format (e.g., "7am", "2pm")
- Sends push notifications via Pushover
- Optional state tracking to only notify on NEW availability (not on every run)

## Configuration

Edit the following variables in `check_availability.py`:

- `DATE`: Target date to check (format: "YYYY-MM-DD")
- `PUSHOVER_USER_KEY`: Your Pushover user key
- `PUSHOVER_API_TOKEN`: Your Pushover API token
- `NOTIFY_ONLY_ON_CHANGES`: Toggle notification behavior (see below)

### Notification Modes

The `NOTIFY_ONLY_ON_CHANGES` toggle controls notification behavior:

- **`True` (default)**: Only sends notifications when NEW slots become available
  - Tracks availability between runs using `availability_state.json`
  - Prevents repeated notifications for the same available slots
  - Shows status: "All slots were already known (no notification sent)"

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

1. Script fetches JSON from API
2. Iterates through each `Resource` (court)
3. For each court, finds the target date in `Days`
4. Scans all `Sessions` for that date
5. Identifies available slots where `Category == 0` and `Capacity >= 1`
6. Converts `StartTime`/`EndTime` from minutes to human-readable format
7. Sends notification if new availability detected (depending on `NOTIFY_ONLY_ON_CHANGES` setting)

### Time Conversion

Times are stored as minutes since midnight:
- `420` minutes = 7:00 AM
- `540` minutes = 9:00 AM
- `1260` minutes = 9:00 PM

The script's `minutes_to_time()` function converts these to 12-hour format (e.g., "7am", "9pm").

## Example Output

```
Court 1: 7am–8am, 9pm–10pm
Court 2: 7am–8am, 9pm–10pm
Court 3: 7am–8am, 4pm–5pm, 8pm–10pm
Court 4 (no floodlights): 7am–8am
Court 5 (no floodlights): 7am–9am
Court 6: 7am–9am, 8pm–10pm
Court 7: 8pm–10pm
Court 8: 9pm–10pm

🎾 3 new slot(s) detected!
✓ Pushover notification sent
```

## State Tracking

When `NOTIFY_ONLY_ON_CHANGES = True`, the script creates an `availability_state.json` file:

```json
{
  "availability": [
    "Court 1: 7am–8am, 9pm–10pm",
    "Court 2: 7am–8am, 9pm–10pm"
  ],
  "last_checked": "2025-01-15T10:30:45.123456"
}
```

This file is used to compare availability between runs and determine which slots are newly available.
