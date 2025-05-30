import os.path
import datetime
import sys # Added for sys.exit in test block

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as dateutil_parser
from dateutil import tz

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
TARGET_CALENDAR_ID = '18d5d40ddafe357ca7f0dbadc1d0382fca050d83669e262a27287c1e27990062@group.calendar.google.com'

def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            # Run the flow using a local server that receives the redirect.
            # The port number must match one of the authorized redirect URIs
            # for the OAuth 2.0 client, which you configured in the API Console.
            creds = flow.run_local_server(port=5000) # Or another port if 5000 is used
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An API error occurred: {error}')
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
        # start_datetime is already an aware datetime object.
        # .isoformat() on an aware object includes the timezone offset, which is RFC3339 compliant.
        time_min_str = start_datetime.isoformat()
        # Check for events starting in a very narrow window (e.g., same minute)
        time_max_str = (start_datetime + datetime.timedelta(minutes=1)).isoformat()

        events_result = service.events().list(
            calendarId=TARGET_CALENDAR_ID,
            timeMin=time_min_str, 
            timeMax=time_max_str,
            q=summary, # Filter by summary (title) on the server side if possible
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        for event_item in events: # Renamed to avoid conflict with the 'event' dict being built
            if event_item['summary'] == summary:
                event_item_start_str = event_item['start'].get('dateTime')
                if not event_item_start_str: # Should be a timed event
                    continue
                
                try:
                    event_item_start_dt = dateutil_parser.isoparse(event_item_start_str)
                    # Direct comparison of aware datetime objects handles timezones correctly
                    if event_item_start_dt == start_datetime:
                        print(f"Event '{summary}' starting at {start_datetime.strftime('%Y-%m-%d %I:%M %p %Z')} already exists. Skipping.")
                        return None
                except ValueError as e:
                    print(f"Warning: Could not parse start time '{event_item_start_str}' for existing event '{summary}': {e}. Considering it not a duplicate for safety.")

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