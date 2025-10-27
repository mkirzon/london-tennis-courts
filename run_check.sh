#!/bin/bash

# Tennis Court Availability Checker - Launchd Wrapper
# Logs all output (stdout + stderr) to /tmp/tennis_check.log

# Set PATH so launchd can find python
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Export Pushover credentials for notifications
export PUSHOVER_USER="u6swfpe91tfxz718f6dx91m1tikdi6"
export PUSHOVER_TOKEN="a7zimuio4jfzpj7yw5cbq5av3bbau3"

# Set log file
LOG_FILE="/tmp/tennis_check.log"

# Date(s) to check (space-separated for multiple dates)
DATES="2025-11-01 2025-11-02"
# Set expiration date to the latest date in DATES
EXPIRATION_DATE="2025-11-02"

# Project directory
PROJECT_DIR="/Users/mkirzon/Scripts/tennis-availability-checker"

{
  echo "--------------------------------------------"
  echo "$(date): Starting tennis availability check"

  # Check if we've passed the expiration date
  CURRENT_DATE=$(date +%Y-%m-%d)
  if [[ "$CURRENT_DATE" > "$EXPIRATION_DATE" ]]; then
      echo "$(date): Job expired (expiration date: $EXPIRATION_DATE). Exiting."
      exit 0
  fi

  # Change to project directory
  cd "$PROJECT_DIR" || { echo "$(date): Failed to cd into $PROJECT_DIR"; exit 1; }

  # Activate virtual environment
  if [[ -f "$PROJECT_DIR/venv/bin/activate" ]]; then
      source "$PROJECT_DIR/venv/bin/activate"
      echo "$(date): Virtual environment activated."
  else
      echo "$(date): Virtual environment not found."
      exit 1
  fi

  # Run the Python script
  echo "$(date): Running check_availability.py for dates: $DATES"
  /Users/mkirzon/Scripts/tennis-availability-checker/venv/bin/python check_availability.py --date $DATES

  echo "$(date): Finished run successfully."

} >> "$LOG_FILE" 2>&1
