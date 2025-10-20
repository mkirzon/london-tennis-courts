"""Notification handling for tennis checker."""

import requests


class PushoverNotifier:
    """Send notifications via Pushover API."""

    def __init__(self, user_key: str, api_token: str):
        """
        Initialize Pushover notifier.

        Args:
            user_key: Pushover user key
            api_token: Pushover API token
        """
        self.user_key = user_key
        self.api_token = api_token
        self.api_url = "https://api.pushover.net/1/messages.json"

    def send(self, message: str, title: str = "Tennis Court Availability") -> bool:
        """
        Send a notification via Pushover API.

        Args:
            message: Notification message
            title: Notification title

        Returns:
            True if successful, False otherwise
        """
        if not self.user_key or not self.api_token:
            print("Warning: Pushover credentials not set. Skipping notification.")
            return False

        try:
            response = requests.post(
                self.api_url,
                data={
                    "token": self.api_token,
                    "user": self.user_key,
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
