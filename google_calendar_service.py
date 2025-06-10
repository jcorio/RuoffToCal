import os.path
import datetime
import sys
import json
import logging
from google.oauth2 import service_account
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
SERVICE_ACCOUNT_FILE = 'service-account.json'
TARGET_CALENDAR_ID = '18d5d40ddafe357ca7f0dbadc1d0382fca050d83669e262a27287c1e27990062@group.calendar.google.com'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_calendar_service():
    """Gets the Google Calendar service using either OAuth2 or service account."""
    # First try service account (for GitHub Actions)
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            logger.info("Attempting to use service account authentication")
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with service account")
            return service
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            # Continue to try OAuth2 if service account fails

    # If no service account or it failed, try OAuth2 (for local development)
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as token:
                token_content = token.read()
                logger.info(f"Token file exists. Content length: {len(token_content)}")
                try:
                    # Validate JSON format
                    json.loads(token_content)
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in token file: {e}")
                    os.remove(TOKEN_FILE)
                    logger.info("Removed corrupted token file")
        except Exception as e:
            logger.error(f"Error reading token file: {e}")
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
                logger.info("Removed problematic token file")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                    logger.info("Removed expired token file")
                creds = None
        else:
            try:
                if not os.path.exists(CREDENTIALS_FILE):
                    logger.error(f"Credentials file {CREDENTIALS_FILE} not found")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=5000)
            except Exception as e:
                logger.error(f"Error in OAuth flow: {e}")
                return None
                
        if creds:
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Successfully saved new token file")
            except Exception as e:
                logger.error(f"Error saving token file: {e}")
                return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        logger.error(f'An API error occurred: {error}')
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