# add_manual_shows_to_calendar.py
import google_calendar_service
from datetime import datetime, time as dt_time, date, timedelta
from dateutil import tz, parser as dateutil_parser
import re
import time as sleep_time

DEFAULT_EVENT_TIMEZONE = "America/New_York"
TARGET_CALENDAR_ID = google_calendar_service.TARGET_CALENDAR_ID
YEAR = 2024
DEFAULT_SHOW_TIME = dt_time(19, 0, 0) # 7:00 PM

MANUAL_SHOWS_2024 = [
    "May 23: 21 Savage",
    "May 28: Hozier",
    "May 31: Noah Kahan",
    "June 1: HARDY",
    "June 8: Hootie and the Blowfish",
    "June 11: James Taylor",
    "June 14: Dierks Bentley",
    "June 20: Kenny Chesney",
    "June 22: Maroon 5",
    "June 23: Santana and Counting Crows",
    "June 27: Tyler Childers",
    "June 28-29: Dave Matthews Band", # Multi-day
    "July 5: KIDZ BOP Live",
    "July 6: Third Eye Blind",
    "July 10: Train & REO Speedwagon",
    "July 11: Halestorm and I Prevail",
    "July 12: Bret Michaels – Parti Gras 2024",
    "July 13: Niall Horan",
    "July 19: Dan + Shay",
    "July 20: Earth, Wind & Fire and Chicago",
    "July 21: LOSERVILLE 2024 with Limp Bizkit",
    "July 25: Red Hot Chili Peppers",
    "July 26: Styx & Foreigner",
    "July 27: Alanis Morissette",
    "Aug. 2-4: Phish", # Multi-day
    "Aug. 6: Slipknot",
    "Aug. 7: Cage The Elephant",
    "Aug. 9: Thirty Seconds To Mars",
    "Aug. 10: Creed",
    "Aug. 16: Five Finger Death Punch",
    "Aug. 17: The Doobie Brothers",
    "Aug. 20: Imagine Dragons",
    "Aug. 23: Glass Animals",
    "Aug. 25: New Kids On The Block",
    "Aug. 26: Pearl Jam",
    "Aug. 30: Sammy Hagar",
    "Aug. 31: Rob Zombie and Alice Cooper",
    "Sept. 1: Pitbull",
    "Sept. 7: Luke Bryan",
    "Sept. 13: Staind and Breaking Benjamin",
    "Sept. 14: ZZ Top and Lynyrd Skynyrd",
    "Sept. 15: Stone Temple Pilots and LIVE",
    "Sept. 20: Megadeth",
    "Oct. 4: Meghan Trainor"
]

def parse_manual_show_string(show_string, year):
    """
    Parses a string like "Month Day[-Day]: Artist" into date(s) and artist.
    Returns a list of dictionaries, each with 'artist', 'start_date', 'end_date'.
    For single day events, start_date and end_date are the same.
    """
    try:
        date_part, artist_name = show_string.split(':', 1)
        artist_name = artist_name.strip()
        date_part = date_part.strip()

        # Regex to find month and day(s)
        # Handles "Month Day", "Month Day-Day"
        match = re.match(r"([A-Za-z.]+)\s+(\d{1,2})(?:-(\d{1,2}))?", date_part)
        if not match:
            print(f"  Could not parse date part: {date_part}")
            return []

        month_str = match.group(1)
        start_day_str = match.group(2)
        end_day_str = match.group(3) # This will be None for single-day events

        # Convert month string (e.g., "Aug." or "August") to a datetime object to get month number
        # We add a dummy day and year for parsing month.
        try:
            month_dt = dateutil_parser.parse(f"{month_str} 1, {year}")
            month = month_dt.month
        except ValueError:
            print(f"  Could not parse month: {month_str}")
            return []

        start_day = int(start_day_str)
        start_date = date(year, month, start_day)
        
        parsed_events = []

        if end_day_str:
            end_day = int(end_day_str)
            # Iterate for multi-day events
            # If end_day is less than start_day, it implies a month crossover,
            # which this simple parser doesn't handle. Assume same month.
            # For robust parsing, a more complex date range logic would be needed.
            # For Phish Aug 2-4, it creates events for Aug 2, Aug 3, Aug 4.
            current_day = start_day
            while current_day <= end_day:
                event_date = date(year, month, current_day)
                parsed_events.append({
                    "artist": f"{artist_name} (Day {current_day - start_day + 1})" if end_day != start_day else artist_name,
                    "event_date": event_date,
                })
                current_day += 1
            if not parsed_events and start_day == end_day : # e.g. Aug 2-2, treat as single day
                 parsed_events.append({
                    "artist": artist_name,
                    "event_date": start_date,
                })

        else: # Single day event
            parsed_events.append({
                "artist": artist_name,
                "event_date": start_date,
            })
        
        return parsed_events

    except Exception as e:
        print(f"  Error parsing show string '{show_string}': {e}")
        return []

def add_manual_shows_to_gcal(show_list, year, cal_service):
    if not cal_service:
        print("Calendar service not available. Shows will not be added.")
        return
    if not show_list:
        print("No shows to add to calendar.")
        return

    added_count = 0
    skipped_count = 0
    
    print(f"--- Adding {year} Shows to Google Calendar ---")

    for show_entry_str in show_list:
        parsed_shows = parse_manual_show_string(show_entry_str, year)
        
        for show_details in parsed_shows:
            event_date = show_details["event_date"]
            artist = show_details["artist"]
            summary = f"{artist} at Ruoff Music Center" # Assuming venue
            description = f"Manually added show for {year}."

            timezone_info = tz.gettz(DEFAULT_EVENT_TIMEZONE)
            
            start_datetime = datetime.combine(event_date, DEFAULT_SHOW_TIME)
            start_datetime = start_datetime.replace(tzinfo=timezone_info)
            
            # Assume 3-hour duration
            end_datetime = start_datetime + timedelta(hours=3)

            print(f"  Attempting to add: {summary} on {start_datetime.strftime('%Y-%m-%d %I:%M %p %Z')}")
            
            try:
                created_event = google_calendar_service.add_event_to_calendar(
                    cal_service,
                    summary,
                    start_datetime,
                    end_datetime,
                    description=description,
                    timezone=DEFAULT_EVENT_TIMEZONE
                )
                if created_event:
                    print(f"    Successfully added: {summary}")
                    added_count += 1
                else:
                    print(f"    Event might already exist or failed to add (no error, no event returned): {summary}")
                    # Check if event exists (optional, simple check based on summary and start time)
                    # existing_events = google_calendar_service.find_events(cal_service, summary, start_datetime=start_datetime.isoformat(), end_datetime=(start_datetime + timedelta(minutes=1)).isoformat())
                    # if existing_events:
                    #     print(f"    Event '{summary}' on {event_date} likely already exists.")
                    #     skipped_count +=1
                    # else:
                    #     print(f"    Failed to add event for an unknown reason: {summary}")
                    #     skipped_count +=1

                sleep_time.sleep(0.6) # API rate limiting
            except Exception as e:
                print(f"    Error adding event '{summary}' to calendar: {e}")
                skipped_count += 1
        
    print(f"--- Summary ---")
    print(f"Successfully added {added_count} new shows to the calendar for {year}.")
    if skipped_count > 0:
        print(f"Skipped or failed to add {skipped_count} shows for {year}.")

def main():
    print("Attempting to connect to Google Calendar...")
    cal_service = google_calendar_service.get_calendar_service()

    if not cal_service:
        print("Failed to connect to Google Calendar Service. Please check credentials and configuration.")
        print("Make sure 'credentials.json' and 'token.json' are correctly set up for google_calendar_service.py.")
        return

    print("Connected to Google Calendar successfully.")
    
    add_manual_shows_to_gcal(MANUAL_SHOWS_2024, YEAR, cal_service)

    # You can add more years or shows here if needed
    # For example:
    # MANUAL_SHOWS_2023 = ["Oct 10: Artist A", "Nov 5-6: Artist B"]
    # add_manual_shows_to_gcal(MANUAL_SHOWS_2023, 2023, cal_service)

if __name__ == "__main__":
    main() 