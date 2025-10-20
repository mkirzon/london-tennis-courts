# Project Structure Documentation

## Overview

This project has been reorganized according to Python best practices, transforming a monolithic script into a well-structured, modular package.

## Directory Structure

```
tennis-availability-checker/
│
├── tennis_checker/              # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── checker.py              # Core availability checking logic
│   ├── config.py               # Configuration and state management
│   ├── notifier.py             # Pushover notification handling
│   └── utils.py                # Utility functions
│
├── config/                      # Configuration directory
│   ├── venues.json             # Venue definitions (version controlled)
│   └── availability_state.json # State tracking (auto-generated, gitignored)
│
├── examples/                    # Sample data directory
│   ├── sample-finpark.json     # Example API response from Finsbury Park
│   └── sample-clissold.json    # Example API response from Clissold Park
│
├── venv/                        # Virtual environment (gitignored)
│
├── check_availability.py        # CLI entry point
├── setup.py                    # Package installation configuration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # Main documentation

```

## Module Responsibilities

### tennis_checker/checker.py
**Purpose**: Core business logic for checking availability

**Key Classes**:
- `AvailabilityChecker`: Main class that orchestrates venue checks

**Key Methods**:
- `check_venue()`: Check a single venue
- `check_all_venues()`: Check all enabled venues
- `_send_notification()`: Internal notification helper

**Dependencies**: config, notifier, utils, requests

### tennis_checker/config.py
**Purpose**: Configuration and state management

**Key Classes**:
- `Config`: Manages venue configuration and state persistence

**Key Methods**:
- `load_venues()`: Load venue definitions from JSON
- `get_enabled_venues()`: Filter enabled venues
- `load_state()`: Load previous availability state
- `save_state()`: Persist current availability state

**Dependencies**: json, pathlib

### tennis_checker/notifier.py
**Purpose**: Handle push notifications

**Key Classes**:
- `PushoverNotifier`: Send notifications via Pushover API

**Key Methods**:
- `send()`: Send a notification with title and message

**Dependencies**: requests

### tennis_checker/utils.py
**Purpose**: Utility functions used across the project

**Key Functions**:
- `minutes_to_time()`: Convert minutes since midnight to human-readable time
- `parse_availability()`: Parse API response to find available slots
- `get_new_slots()`: Compare current and previous availability

**Dependencies**: typing

### check_availability.py
**Purpose**: Command-line interface

**Key Functions**:
- `main()`: Parse arguments and orchestrate the availability check

**Features**:
- Flexible CLI arguments for date, venues, notification settings
- Uses argparse for professional command-line interface
- Returns appropriate exit codes

## Configuration Files

### config/venues.json
**Purpose**: Define venues to check

**Format**:
```json
{
  "venues": [
    {
      "id": "unique_venue_id",
      "name": "Display Name",
      "url_template": "API_URL_with_{date}_placeholder",
      "enabled": true
    }
  ]
}
```

**Version Controlled**: Yes

### config/availability_state.json
**Purpose**: Track availability between runs

**Format**:
```json
{
  "venue_id": {
    "name": "Venue Name",
    "availability": ["Court 1: 7am-8am", ...]
  },
  "last_checked": "ISO_8601_timestamp"
}
```

**Version Controlled**: No (in .gitignore)
**Auto-generated**: Yes

## Design Decisions

### Why Separate Modules?

1. **Maintainability**: Each module has a single, clear responsibility
2. **Testability**: Functions can be tested in isolation
3. **Reusability**: Modules can be imported and used independently
4. **Readability**: Smaller files are easier to understand

### Why Config Directory?

1. **Separation of Concerns**: Configuration separate from code
2. **Easy Updates**: Non-developers can modify venues.json
3. **State Management**: State file location is predictable
4. **Deployment**: Can mount config directory in containers

### Why Examples Directory?

1. **Documentation**: Shows API response structure
2. **Testing**: Can be used for unit tests
3. **Development**: Work offline with sample data

### Why Keep CLI at Root?

1. **Convenience**: Easy to run `python check_availability.py`
2. **Backward Compatibility**: Similar interface to original script
3. **Entry Point**: Clear entry point for the application

## Migration from Old Structure

### Old Structure
```
check_availability.py  (single monolithic file ~300 lines)
venues.json
availability_state.json
sample-*.json
```

### Changes Made

1. **Code Split**: Monolithic script → 4 modules + CLI
2. **File Organization**: Config and examples in separate directories
3. **Better Imports**: Module-based imports instead of global functions
4. **Type Hints**: Added throughout for better IDE support
5. **Documentation**: Comprehensive docstrings for all functions/classes
6. **CLI Enhancement**: Professional argument parsing with argparse

### Benefits

- **Code Reusability**: Can import `tennis_checker` in other projects
- **Testing**: Can test individual functions
- **Extensibility**: Easy to add new notification services, venues, etc.
- **Professional**: Follows Python packaging standards
- **Installation**: Can be installed as a package with `pip install -e .`

## Future Enhancements

Possible additions to consider:

1. **Tests**: Add `tests/` directory with pytest
2. **CI/CD**: Add GitHub Actions or similar
3. **Docker**: Add Dockerfile for containerization
4. **Additional Notifiers**: Support Slack, Discord, email, etc.
5. **Web Interface**: Add Flask/FastAPI frontend
6. **Database**: Store historical availability data
7. **Analytics**: Track availability patterns over time
8. **Multi-threading**: Check venues in parallel for faster execution

## Development Workflow

### Making Changes

1. Modify code in `tennis_checker/` modules
2. Update `README.md` if user-facing changes
3. Test with `python check_availability.py --no-notify`
4. Commit changes

### Adding a New Venue

1. Edit `config/venues.json`
2. Add venue entry with correct URL template
3. Test with `python check_availability.py --venues new_venue_id --no-notify`

### Adding a New Feature

1. Determine appropriate module
2. Add function/class to module
3. Update CLI if needed
4. Update README
5. Consider adding tests

## Best Practices Followed

✅ **Modular Design**: Separation of concerns
✅ **Type Hints**: For better IDE support and documentation
✅ **Docstrings**: Comprehensive documentation
✅ **Git Ignore**: Proper .gitignore configuration
✅ **Virtual Environment**: Dependencies isolated
✅ **Package Structure**: Standard Python package layout
✅ **CLI Tool**: Professional command-line interface
✅ **Configuration Files**: Separate from code
✅ **Setup Script**: Standard setup.py for installation
✅ **README**: Comprehensive user documentation

## Related Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Real Python - Python Application Layouts](https://realpython.com/python-application-layouts/)
