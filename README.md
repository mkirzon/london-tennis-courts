# Tennis Court Availability Checker

A Python package that checks tennis court availability at multiple venues (via ClubSpark LTA API) and sends push notifications via Pushover when courts are available.

## Features

- **Multi-venue support**: Check availability across multiple tennis parks
- **Modular architecture**: Clean, maintainable code structure
- **Smart notifications**: Only notify on NEW availability (configurable)
- **Per-venue state tracking**: Accurate change detection for each venue
- **Command-line interface**: Easy to use with flexible options
- **Configurable**: Manage venues via JSON configuration
- **Human-readable dates**: Shows "Monday Oct. 20" format
- **Individual time slots**: Lists each available hour separately (e.g., "2pm, 3pm, 5pm")

## Project Structure

```
tennis-availability-checker/
├── tennis_checker/          # Main package
│   ├── __init__.py         # Package initialization
│   ├── checker.py          # Core availability checking logic
│   ├── config.py           # Configuration management
│   ├── notifier.py         # Pushover notification handling
│   └── utils.py            # Utility functions
├── config/                  # Configuration files
│   ├── venues.json         # Venue definitions
│   └── availability_state.json  # State tracking (auto-generated)
├── examples/                # Sample API responses
│   ├── sample-finpark.json
│   └── sample-clissold.json
├── check_availability.py    # CLI entry point
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
├── .gitignore              # Git ignore rules
└── README.md              # This file
```

## Installation

### Option 1: Local Development

1. Clone or download the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Install as Package

```bash
pip install -e .
```

This installs the package in editable mode and creates a `tennis-checker` command.

## Configuration

### Venue Configuration

Venues are configured in `config/venues.json`:

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

**Adding a New Venue:**

1. Add a new entry to the `venues` array
2. Set a unique `id` (e.g., `"hampstead_heath"`)
3. Set the `name` (e.g., `"Hampstead Heath"`)
4. Set the `url_template` with the correct ClubSpark venue path
5. Set `enabled: true`

### Pushover Credentials

Set your Pushover credentials in the CLI arguments:

```bash
python check_availability.py \
  --pushover-user YOUR_USER_KEY \
  --pushover-token YOUR_API_TOKEN
```

Or modify the defaults in `check_availability.py`.

## Usage

### Basic Usage

Check all enabled venues for today:
```bash
python check_availability.py
```

### Check Specific Date

```bash
python check_availability.py --date 2025-09-13
```

### Check Specific Venues Only

```bash
python check_availability.py --venues finsbury_park clissold_park
```

### Disable Notifications (Test Mode)

```bash
python check_availability.py --no-notify
```

### Always Notify (Don't Track Changes)

By default, the checker only notifies on NEW availability. To get notifications every time there's ANY availability:

```bash
python check_availability.py --notify-always
```

### Full Command Options

```bash
python check_availability.py --help
```

```
options:
  -h, --help            show this help message and exit
  --date DATE           Date to check (YYYY-MM-DD format). Defaults to today.
  --venues VENUES [VENUES ...]
                        Venue IDs to check. If not specified, checks all enabled venues.
  --notify-always       Always send notifications when courts are available (not just for new slots)
  --pushover-user PUSHOVER_USER
                        Pushover user key
  --pushover-token PUSHOVER_TOKEN
                        Pushover API token
  --no-notify           Disable notifications (just print results)
```

## Example Output

### Multi-Venue Output

Times are shown as individual hour start times, making it easy to see each available booking slot:

```
Checking availability for Friday Sep. 13...

============================================================
Checking Finsbury Park...
============================================================
Court 1: 7am, 9pm
Court 2: 7am, 9pm
Court 3: No availability
Court 4 (no floodlights): 7am
Court 5 (no floodlights): 7am, 8am
Court 6: 7am, 8am, 8pm, 9pm
Court 7: 8pm, 9pm
Court 8: 9pm

🎾 2 new slot(s) detected at Finsbury Park

============================================================
Checking Clissold Park...
============================================================
Court 1: 2pm
Court 2: 2pm, 5pm
Court 3: No availability
Court 4: 8pm
Court 5: No availability

🎾 3 new slot(s) detected at Clissold Park

============================================================
SUMMARY
============================================================

🎾 5 total new slot(s) across all venues!
✓ Pushover notification sent
```

### Notification Format

Notifications show individual start times grouped by venue with human-readable dates:

```
New courts available on Friday Sep. 13:

📍 Finsbury Park:
  • Court 1: 7am, 9pm
  • Court 2: 7am, 9pm

📍 Clissold Park:
  • Court 1: 2pm
  • Court 2: 2pm, 5pm
  • Court 4: 8pm
```

## State Tracking

By default (when `--notify-always` is NOT used), the checker persists the last-seen availability so it can notify only on NEW slots.

Design choices considered:

- Single global JSON file (`config/availability_state.json`) — simple, backwards-compatible, but harder to use when checking multiple dates independently because every run would overwrite the same file.
- One file per date (`config/state/availability_state_YYYY-MM-DD.json`) — isolates state per date, safe for concurrent or scheduled checks of different dates, and easy to inspect or rotate.
- Embedded DB (SQLite) — robust and queryable, but adds complexity and an extra dependency for a small project.

Chosen approach: one file per date in `config/state/`.

Rationale:

- Minimal changes to the existing code and no new dependencies.
- Clearly separates state for different dates so you can run checks for multiple dates (e.g., today and a future date) without collisions.
- Keeps a legacy fallback to `config/availability_state.json` when no date is provided, preserving backward compatibility.

Behavior and file locations:

- Per-date state files are written to `config/state/availability_state_YYYY-MM-DD.json` when a `--date` is supplied (or when the checker is invoked programmatically with a date).
- If no date is supplied and the code calls the legacy path, the checker will read/write `config/availability_state.json`.
- Each state file contains a map of venue IDs to the last-known availability and a `last_checked` timestamp.

Example per-date file path:

```
config/state/availability_state_2025-09-13.json
```

This change makes the checker safe to run concurrently for multiple dates (e.g., scheduled checks for today and for a tournament date) and makes it straightforward to inspect historical state for specific dates.

## Scheduling (Cron/Task Scheduler)

To run the checker automatically:

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/tennis-availability-checker && /path/to/venv/bin/python check_availability.py

# Run every 15 minutes
*/15 * * * * cd /path/to/tennis-availability-checker && /path/to/venv/bin/python check_availability.py
```

### Windows (Task Scheduler)

Create a batch file `run_checker.bat`:

```batch
@echo off
cd /d C:\path\to\tennis-availability-checker
venv\Scripts\python.exe check_availability.py
```

Then schedule it in Task Scheduler.

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest tests/
```

### Code Structure

- **`tennis_checker/checker.py`**: Main availability checking logic
- **`tennis_checker/config.py`**: Configuration and state management
- **`tennis_checker/notifier.py`**: Pushover notification handling
- **`tennis_checker/utils.py`**: Helper functions (time conversion, parsing)
- **`check_availability.py`**: CLI interface

## API Response Format

The script fetches data from the ClubSpark LTA booking API. Key fields:

- **`Resources`**: Array of courts
- **`Days`**: Array of dates with sessions
- **`Sessions`**: Array of time slots
  - `Category`: 0 = Available, 1000 = Booked, 2000 = Class, 8000 = Closed
  - `Capacity`: Number of available slots (≥1 = bookable)
  - `StartTime`/`EndTime`: Minutes since midnight (e.g., 840 = 2pm)

The script expands time ranges into individual hour start times. For example:
- A slot from 2pm-4pm becomes: "2pm, 3pm"
- A slot from 5pm-6pm becomes: "5pm"

See `examples/` directory for sample API responses.

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

**Issue**: "No venues enabled"
- **Solution**: Check `config/venues.json` exists and has venues with `enabled: true`

**Issue**: "Error fetching data for [venue]"
- **Solution**: Check your internet connection and verify the venue URL is correct

**Issue**: Not receiving notifications
- **Solution**: Verify Pushover credentials are correct and you're not using `--no-notify`

**Issue**: Getting notified for same slots repeatedly
- **Solution**: Ensure you're not using `--notify-always` and `config/availability_state.json` is being created/updated
