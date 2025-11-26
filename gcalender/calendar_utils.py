import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pathlib

KEYFILE_PATH = os.getcwd() + "/gcalender/credentials/oauth.keys.json"
CALENDER_CREDENTIALS_PATH = os.getcwd() + "/gcalender/credentials/.calender-server-credentials.json"

CALENDER_SCOPES = [
   "https://www.googleapis.com/auth/calendar",
]

PORT = 8080


# -----------------------------------------
# AUTHENTICATION
# -----------------------------------------
def authenticate_and_save():
    """Authenticate Gmail and save credentials."""
    
    # Already authenticated?
    if os.path.exists(CALENDER_CREDENTIALS_PATH):
        return

    creds = None

    # Try refresh if creds exist
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(CALENDER_CREDENTIALS_PATH, "w") as f:
                f.write(creds.to_json())
            return
        except:
            creds = None

    # Fresh login
    flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, CALENDER_SCOPES)
    creds = flow.run_local_server(port=PORT, access_type="offline", prompt="consent")

    pathlib.Path(os.path.dirname(CALENDER_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)

    with open(CALENDER_CREDENTIALS_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Credentials saved to {CALENDER_CREDENTIALS_PATH}")


def get_client():
    """Return a Gmail API client."""
    authenticate_and_save()
    creds = Credentials.from_authorized_user_file(CALENDER_CREDENTIALS_PATH, CALENDER_SCOPES)
    return build("calendar", "v3", credentials=creds)


def format_event_time(event_time):
    """
    Format an event time into a human-readable string.

    Args:
        event_time (dict): The event time dictionary from Google Calendar API

    Returns:
        str: A human-readable time string
    """
    if "dateTime" in event_time:
        # This is a datetime event
        dt = datetime.fromisoformat(event_time["dateTime"].replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %I:%M %p")
    elif "date" in event_time:
        # This is an all-day event
        return f"{event_time['date']} (All day)"
    return "Unknown time format"


def parse_datetime(datetime_str):
    """
    Parse a datetime string into a datetime object.

    Args:
        datetime_str (str): A string representing a date and time

    Returns:
        datetime: A datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y",
        "%B %d, %Y %H:%M",
        "%B %d, %Y %I:%M %p",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue

    return None


def get_current_time() -> dict:
    """
    Get the current time and date
    """
    now = datetime.now()

    # Format date as MM-DD-YYYY
    formatted_date = now.strftime("%m-%d-%Y")

    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "formatted_date": formatted_date,
    }