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

SUPPORTED_CALENDARS = ["Personal", "Work", "Fitness", "Social", "Other"]

def initialize_calendars():
    """Ensure all predefined calendars exist on the CalDAV server."""
    client = get_client()
    for cal_name in SUPPORTED_CALENDARS:
        try:
            _get_or_create_calendar(client, name=cal_name)
        except Exception as e:
            print(f"Warning: Failed to ensure calendar '{cal_name}' exists: {e}")

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

def add_event(summary: str, start_time: datetime, end_time: datetime, calendar_name: str = "Personal"):
    """Adds an event to the specified Calendar in the CalDAV server."""
    print("Get client...")
    client = get_client()
    print("Get calendar...")
    calendar = _get_or_create_calendar(client, name=calendar_name)
    print("Add event...")
    event = calendar.save_event(
        dtstart=start_time,
        dtend=end_time,
        summary=summary,
    )
    return event

def get_existing_events():
    client = get_client()
    events = []
    for calendar in client.principal().calendars():
        for event in calendar.events():
            event.load()
            try:
                v_inst = event.vobject_instance
            except Exception:
                continue
            if not hasattr(v_inst, 'vevent'):
                continue
            vevent = v_inst.vevent
            if hasattr(vevent, 'uid') and hasattr(vevent, 'summary') and hasattr(vevent, 'dtstart'):
                events.append({
                    "uid": getattr(vevent, 'uid').value,
                    "summary": getattr(vevent, 'summary').value,
                    "start": str(getattr(vevent, 'dtstart').value),
                    "calendar_name": calendar.name
                })
    return events

def find_event_by_uid(uid: str):
    client = get_client()
    for calendar in client.principal().calendars():
        try:
            event = calendar.event_by_uid(uid)
            if event:
                return event, calendar
        except Exception:
            pass
    return None, None

def update_event(uid: str, new_summary: str, new_start_time: datetime, new_end_time: datetime, new_calendar_name: str = None):
    event, old_calendar = find_event_by_uid(uid)
    if not event:
        raise ValueError(f"Could not find event with uid '{uid}'")
    
    event.delete()
    
    client = get_client()
    target_calendar_name = new_calendar_name if new_calendar_name else old_calendar.name
    target_calendar = _get_or_create_calendar(client, name=target_calendar_name)
    
    return target_calendar.save_event(dtstart=new_start_time, dtend=new_end_time, summary=new_summary)

def delete_event(uid: str):
    event, _ = find_event_by_uid(uid)
    if not event:
        raise ValueError(f"Could not find event with uid '{uid}'")
    
    event.delete()
    return True
