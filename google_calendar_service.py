import os.path
import datetime
import sys
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as dateutil_parser
from dateutil import tz

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TARGET_CALENDAR_ID = '18d5d40ddafe357ca7f0dbadc1d0382fca050d83669e262a27287c1e27990062@group.calendar.google.com'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_calendar_service():
    """Gets the Google Calendar service using service account authentication."""
    try:
        logger.info("Attempting to use service account authentication")
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)
        logger.info("Successfully authenticated with service account")
        return service
    except Exception as e:
        logger.error(f"Service account authentication failed: {e}")
        return None

def add_event_to_calendar(service, summary, start_datetime, end_datetime, description=None, timezone='America/New_York'):
    """Adds an event to the primary Google Calendar.

    Args:
        service: Authorized Google Calendar API service instance.
        summary (str): The title of the event.
        start_datetime (datetime.datetime): The start date and time of the event.
        end_datetime (datetime.datetime): The end date and time of the event.
        description (str, optional): A description for the event. Defaults to None.
        timezone (str, optional): The timezone for the event. Defaults to 'America/New_York'.

    Returns:
        dict: The created event object, or None if an error occurred or event already exists.
    """
    if not service:
        print("Calendar service is not available.")
        return None

    # Check if event already exists
    try:
        # To find duplicates, search for events in a time window around the target start time.
        # We'll search +/- 5 minutes and then check for an exact title match in the results.
        # Using a wider window helps catch duplicates if there are minor time discrepancies.
        time_min = start_datetime - datetime.timedelta(minutes=5)
        time_max = start_datetime + datetime.timedelta(minutes=5)

        events_result = service.events().list(
            calendarId=TARGET_CALENDAR_ID,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            # q=summary,  # Removing this as it's a broad search. We'll filter by exact title in the loop.
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # If any event in the window has the same title, we assume it's a duplicate.
        for event_item in events:
            if event_item['summary'] == summary:
                print(f"Event '{summary}' starting around the same time already exists. Skipping.")
                return None

    except HttpError as error:
        print(f"An API error occurred while checking for existing events: {error}")
        # Decide if you want to proceed or not. For now, we'll try to add.

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': timezone,
        },
    }

    try:
        created_event = service.events().insert(calendarId=TARGET_CALENDAR_ID, body=event).execute()
        print(f"Event created in calendar {TARGET_CALENDAR_ID}: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as error:
        print(f'An API error occurred while creating event: {error}')
        return None

if __name__ == '__main__':
    # This is for testing the module directly.
    # You will need to have 'credentials.json' in the same directory.
    # The first time you run it, it will open a browser window for authentication.
    print("Attempting to get Google Calendar service...")
    cal_service = get_calendar_service()
    if cal_service:
        print("Successfully obtained Google Calendar service.")
        # Example: Add a test event
        # Using aware datetime objects for testing
        
        # Example: A show is at 7 PM in New York tomorrow
        # Create a naive datetime first
        event_date = datetime.date.today() + datetime.timedelta(days=1)
        naive_start_dt = datetime.datetime(event_date.year, event_date.month, event_date.day, 19, 0, 0) # 7 PM
        
        # Make it timezone-aware for 'America/New_York'
        ny_tz_info = tz.gettz('America/New_York')
        if ny_tz_info is None: # Should not happen with valid timezone string
            print("Could not get America/New_York timezone info for test. Aborting test event creation.")
            # sys.exit(1) # Or just don't proceed with adding the event in the test
        else:
            aware_start_dt = naive_start_dt.replace(tzinfo=ny_tz_info)
            aware_end_dt = aware_start_dt + datetime.timedelta(hours=1) # 1 hour duration
            
            print(f"Attempting to add a test event: 'Test Event from Script' on {aware_start_dt.strftime('%Y-%m-%d %I:%M %p %Z')}")
            add_event_to_calendar(cal_service,
                                  'Test Event from Script',
                                  aware_start_dt,
                                  aware_end_dt,
                                  description='This is a test event added by the Python script to the target calendar.',
                                  timezone='America/New_York') # Timezone param for event creation
    else:
        print("Failed to obtain Google Calendar service.") 