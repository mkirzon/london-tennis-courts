#!/usr/bin/env python3
"""
Command-line interface for tennis court availability checker.

Usage:
    python check_availability.py
"""

import argparse
import os
from datetime import datetime

from tennis_checker.checker import AvailabilityChecker
from tennis_checker.config import Config
from tennis_checker.notifier import PushoverNotifier
from tennis_checker.utils import format_date


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check tennis court availability across multiple venues"
    )
    parser.add_argument(
        "--date",
        type=str,
        nargs="+",
        default=[datetime.now().strftime("%Y-%m-%d")],
        help="Date(s) to check (YYYY-MM-DD format). Can specify multiple dates. Defaults to today.",
    )
    parser.add_argument(
        "--venues",
        type=str,
        nargs="+",
        default=None,
        help="Venue IDs to check. If not specified, checks all enabled venues.",
    )
    parser.add_argument(
        "--notify-always",
        action="store_true",
        help="Always send notifications when courts are available (not just for new slots)",
    )
    parser.add_argument(
        "--pushover-user",
        type=str,
        default=os.environ.get("PUSHOVER_USER"),
        help="Pushover user key (can also be set via PUSHOVER_USER environment variable)",
    )
    parser.add_argument(
        "--pushover-token",
        type=str,
        default=os.environ.get("PUSHOVER_TOKEN"),
        help="Pushover API token (can also be set via PUSHOVER_TOKEN environment variable)",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable notifications (just print results)",
    )

    args = parser.parse_args()

    # Initialize configuration
    config = Config()

    # Initialize notifier (if enabled)
    notifier = None
    if not args.no_notify and args.pushover_user and args.pushover_token:
        notifier = PushoverNotifier(args.pushover_user, args.pushover_token)

    # Initialize checker
    checker = AvailabilityChecker(
        config=config,
        notifier=notifier,
        notify_only_on_changes=not args.notify_always,
    )

    # Check availability for each date
    any_notified = False
    any_available = False
    
    for date in args.date:
        formatted_date = format_date(date)
        print(f"Checking availability for {formatted_date}...")
        result = checker.check_all_venues(date=date, enabled_venue_ids=args.venues)
        
        if result["notified"]:
            any_notified = True
        if any(v["availability"] for v in result["venues"].values()):
            any_available = True

    # Exit with appropriate code
    if any_notified or any_available:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
