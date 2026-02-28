import os
import caldav
from caldav.elements import dav
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CALDAV_URL = os.getenv("CALDAV_URL", "http://radicale:5232/jonamars/")
CALDAV_USERNAME = os.getenv("CALDAV_USERNAME", "jonamars")
CALDAV_PASSWORD = os.getenv("CALDAV_PASSWORD", "skibitoilet")

def get_client():
    return caldav.DAVClient(
        url=CALDAV_URL,
        username=CALDAV_USERNAME,
        password=CALDAV_PASSWORD
    )

def _get_or_create_calendar(client: caldav.DAVClient, name: str = "AI Calendar"):
    principal = client.principal()
    calendars = principal.calendars()
    for cal in calendars:
        if cal.name == name:
            return cal
    # If not found, create it
    try:
        return principal.make_calendar(name=name)
    except Exception as e:
        print(f"Error creating calendar, may already exist: {e}")
        # Radical might have weird caching, fallback to finding it again
        for cal in principal.calendars():
            if cal.name == name:
                return cal
        raise

def add_event(summary: str, start_time: datetime, end_time: datetime):
    """Adds an event to the default AI Calendar in the CalDAV server."""
    print("Get client...")
    client = get_client()
    print("Get calendar...")
    calendar = _get_or_create_calendar(client)
    print("Add event...")
    event = calendar.save_event(
        dtstart=start_time,
        dtend=end_time,
        summary=summary,
    )
    return event
