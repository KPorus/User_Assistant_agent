from gcalender.calendar_utils import get_client, parse_datetime
import uuid

def create_event(summary: str, start_time: str, end_time: str) -> dict:
    """
    Create a new event in Google Calendar with an auto-generated Google Meet link.

    Args:
        summary (str): Event title/summary
        start_time (str): Start time (e.g., "2023-12-31 14:00")
        end_time (str): End time (e.g., "2023-12-31 15:00")

    Returns:
        dict: Information about the created event or error details
    """
    try:
        # Get calendar service
        service = get_client()
        if not service:
            return {
                "status": "error",
                "message": "Failed to authenticate with Google Calendar. Please check credentials.",
            }

        calendar_id = "primary"
        start_dt = parse_datetime(start_time)
        end_dt = parse_datetime(end_time)
        if not start_dt or not end_dt:
            return {
                "status": "error",
                "message": "Invalid date/time format. Please use YYYY-MM-DD HH:MM format.",
            }

        timezone_id = "Asia/Dhaka"
        try:
            settings = service.settings().list().execute()
            for setting in settings.get("items", []):
                if setting.get("id") == "timezone":
                    timezone_id = setting.get("value")
                    break
        except Exception:
            pass  # Use default timezone if unable to fetch

        event_body = {
            "summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone_id},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone_id},
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }

        event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            conferenceDataVersion=1
        ).execute()

        print("=========================meet link=====================", event.get("hangoutLink", ""))
        print("==========================create event=====================", event)

        return {
            "status": "success",
            "message": "Event created successfully",
            "event_id": event["id"],
            "event_link": event.get("htmlLink", ""),
            "meet_link": event.get("hangoutLink", ""),
        }

    except Exception as e:
        return {"status": "error", "message": f"Error creating event: {str(e)}"}




# from gcalender.calendar_utils import get_client, parse_datetime

# def create_event(
#     summary: str,
#     start_time: str,
#     end_time: str,
# ) -> dict:
#     """
#     Create a new event in Google Calendar.

#     Args:
#         summary (str): Event title/summary
#         start_time (str): Start time (e.g., "2023-12-31 14:00")
#         end_time (str): End time (e.g., "2023-12-31 15:00")

#     Returns:
#         dict: Information about the created event or error details
#     """
#     try:
#         # Get calendar service
#         service = get_client()
#         if not service:
#             return {
#                 "status": "error",
#                 "message": "Failed to authenticate with Google Calendar. Please check credentials.",
#             }

#         calendar_id = "primary"

#         # Parse times
#         start_dt = parse_datetime(start_time)
#         end_dt = parse_datetime(end_time)

#         if not start_dt or not end_dt:
#             return {
#                 "status": "error",
#                 "message": "Invalid date/time format. Please use YYYY-MM-DD HH:MM format.",
#             }

#         timezone_id = "Asia/Dhaka"  # Default timezone

#         try:
#             # Try to get the timezone from the calendar settings
#             settings = service.settings().list().execute()
#             for setting in settings.get("items", []):
#                 if setting.get("id") == "timezone":
#                     timezone_id = setting.get("value")
#                     break
#         except Exception:
#             # If we can't get it from settings, we'll use the default
#             pass

#         # Create event body without type annotations
#         event_body = {}

#         # Add summary
#         event_body["summary"] = summary

#         # Add start and end times with the dynamically determined timezone
#         event_body["start"] = {
#             "dateTime": start_dt.isoformat(),
#             "timeZone": timezone_id,
#         }
#         event_body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": timezone_id}

#         # Call the Calendar API to create the event
#         event = (
#             service.events().insert(calendarId=calendar_id, body=event_body,conferenceDataVersion=1).execute()
#         )
#         print("=========================meet link=====================",event.get("hangoutLink", ""))
#         print("==========================create event=====================",event)

#         return {
#             "status": "success",
#             "message": "Event created successfully",
#             "event_id": event["id"],
#             "event_link": event.get("htmlLink", ""),
#             "meet_link": event.get("hangoutLink", ""),
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Error creating event: {str(e)}"}