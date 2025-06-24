import re
from datetime import datetime
from dateutil import parser as dateutil_parser
from dateutil import tz

def parse_show_datetime(date_str, current_year, default_timezone_str):
    """
    Parses a variety of date/time string formats into a timezone-aware datetime object.
    Examples: "Tue Jun 10", "Tue Jun 10, 2025 ▪︎ 7PM", "Jul 4 ▪︎ 8:00 PM"
    """
    if not date_str:
        return None

    try:
        # Normalize separators and remove extra spaces
        date_str = date_str.replace("▪︎", "").replace("•", "").strip()
        date_str = re.sub(r'\s+', ' ', date_str) # Replace multiple spaces with one

        # Attempt to parse with dateutil.parser
        # If the year is missing, dateutil might assume current year, which is usually correct for upcoming events.
        # However, we need to ensure it handles cases like "Dec 10" (current year) vs "Jan 5" (next year if current month is Dec)
        
        # Try to extract time first if present
        time_match = re.search(r'(\d{1,2}(:\d{2})?\s*(AM|PM))', date_str, re.IGNORECASE)
        event_time_str = None
        date_part_str = date_str

        if time_match:
            event_time_str = time_match.group(1)
            # Remove the time part to avoid confusion for dateutil.parser if it's just a date
            date_part_str = date_str.replace(event_time_str, "").strip()
            # Clean up common artifacts like trailing commas or hyphens after removing time
            date_part_str = re.sub(r'[,-]$', '', date_part_str).strip()

        # If date_part_str becomes empty or is just a day of week, it's problematic
        if not date_part_str or date_part_str.lower() in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
             # This might happen if the original string was just "7PM" or "Mon 7PM", which is unlikely for this scraper
             print(f"Warning: Could not reliably parse date from '{date_str}'. Date part is '{date_part_str}'.")
             return None


        # Add current year if year is likely missing
        if not re.search(r'\b(20\d{2})\b', date_part_str): # if no 4-digit year found
            date_part_str += f", {current_year}"

        full_datetime_str_to_parse = date_part_str
        if event_time_str:
            full_datetime_str_to_parse += " " + event_time_str
        
        parsed_dt = dateutil_parser.parse(full_datetime_str_to_parse)

        # If the parsed date is in the past (e.g. "Jan 5" parsed for current year, but it's Dec 2024, so Jan 5 means Jan 5, 2025)
        # and the original string didn't explicitly state the year.
        if not re.search(r'\b(20\d{2})\b', date_str) and parsed_dt < datetime.now().replace(tzinfo=None):
            parsed_dt = parsed_dt.replace(year=parsed_dt.year + 1)

        # Make the datetime timezone-aware
        target_tz = tz.gettz(default_timezone_str)
        if target_tz is None: # Fallback if tz.gettz returns None
            print(f"Warning: Timezone '{default_timezone_str}' not found. Using system local time as naive.")
            return parsed_dt # Returns naive, or could raise error

        aware_dt = parsed_dt.replace(tzinfo=target_tz)
        
        # Heuristic: if the time is exactly 12:00 AM and original string didn't specify AM/PM explicitly
        # it *might* be a date-only event. LiveNation usually has times.
        # For now, we assume any parsed time is intentional.
        
        return aware_dt

    except Exception as e:
        print(f"Error parsing date string '{date_str}': {e}")
        return None 