#!/bin/bash

# Tennis Court Availability Checker - Cron Job Wrapper
# This script is designed to be run by cron every 15 minutes

# Set the date to check (change this as needed)
DATE="2025-10-25"
EXPIRATION_DATE=$DATE

# Project directory
PROJECT_DIR="/Users/mkirzon/Desktop/tennis-availability-checker"

# Set expiration date (format: YYYY-MM-DD)
# Script will stop running after this date

# Check if we've passed the expiration date
CURRENT_DATE=$(date +%Y-%m-%d)
if [[ "$CURRENT_DATE" > "$EXPIRATION_DATE" ]]; then
    echo "$(date): Cron job expired. Expiration date was $EXPIRATION_DATE" >> "$PROJECT_DIR/cron.log"
    exit 0
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment and run the checker
source "$PROJECT_DIR/venv/bin/activate"

# Run the availability checker
python check_availability.py \
  --date "$DATE"

# Log the run (optional)
echo "$(date): Checked availability for $DATE" >> "$PROJECT_DIR/cron.log"
