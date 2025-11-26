from gcalender.calendar_utils import get_client
from gcalender.list_events import list_events


def delete_event(
    event_id: str,
    confirm: bool,
) -> dict:
    """
    Delete an event from Google Calendar.

    Args:
        event_id (str): The unique ID of the event to delete
        confirm (bool): Confirmation flag (must be set to True to delete)

    Returns:
        dict: Operation status and details
    """
    # Safety check - require explicit confirmation
    if not confirm:
        return {
            "status": "error",
            "message": "Please confirm deletion by setting confirm=True",
        }

    try:
        # Get calendar service
        service = get_client()
        if not service:
            return {
                "status": "error",
                "message": "Failed to authenticate with Google Calendar. Please check credentials.",
            }

        # Always use primary calendar
        calendar_id = "primary"

        # Call the Calendar API to delete the event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

        return {
            "status": "success",
            "message": f"Event {event_id} has been deleted successfully",
            "event_id": event_id,
        }

    except Exception as e:
        return {"status": "error", "message": f"Error deleting event: {str(e)}"}
    
def delete_events_by_criteria(date=None, confirm=False):
    # List events (today, date, all, etc.)
    events = list_events(startdate=date, days=1 if date else 30)["events"]
    if confirm:
        for event in events:
            delete_event(eventid=event["id"], confirm=True)
        return f"Deleted {len(events)} events."
    else:
        return "Please confirm batch deletion."


def delete_event_by_name_and_date(event_name, event_date:str | None):
    """
    Delete a Google Calendar event by name (summary) and date.
    event_name: str, name/summary of the event (case-insensitive match).
    event_date: str, date in 'YYYY-MM-DD' format.
    """
    # List events for the given date
    result = list_events(startdate=event_date, days=1)
    events = result.get("events", [])
    if not events:
        return {"status": "error", "message": "No events found for the specified date."}

    # Find the event by name (summary)
    for event in events:
        if event_name.lower() in event.get("summary", "").lower():
            event_id = event.get("id")
            # Call the existing delete function
            return delete_event(eventid=event_id, confirm=True)

    return {"status": "error", "message": f"Event '{event_name}' not found on {event_date}."}