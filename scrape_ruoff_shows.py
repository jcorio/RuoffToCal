import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import re
from dateutil import parser as dateutil_parser
from dateutil import tz
import google_calendar_service
import shutil
import os

URL = "https://www.livenation.com/venue/KovZpvEk7A/ruoff-music-center-events"
SHOWS_CSV_FILE = "ruoff_shows.csv"
LAST_KNOWN_SHOWS_FILE = "last_known_shows.txt"
DEFAULT_EVENT_TIMEZONE = "America/New_York"

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

def scrape_shows():
    """Scrapes show information from the Live Nation website."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    shows_data = []
    
    # The structure of the event cards seems to be within divs with class "css-1ce5vyp", "css-10r2c5p", etc.
    # Let's try a more general approach to find event containers.
    # Based on the provided HTML, event items are in `div` elements with a role='group' and a class like `css-xxxxxx`
    # Inside these, the show title is an `h2` with class `chakra-heading css-1es4gst`
    # The date is a `time` tag within a `span` with class `chakra-badge css-z4b87k`
    # The full date/time is in a `time` tag within a `span` with class `chakra-badge css-52t1jy`
    
    event_cards = soup.find_all('div', role='group', class_ = lambda x: x and x.startswith('css-'))

    if not event_cards:
        print("No event cards found. The website structure might have changed.")
        # Fallback: try to find sections that look like event listings
        # This is a very generic fallback and might need adjustment
        possible_event_sections = soup.find_all('div', class_=lambda x: x and 'event' in x.lower())
        if not possible_event_sections:
            print("Fallback also failed to find event sections.")
            return None
        # If fallback finds something, you'd need more specific parsing logic here
        # For now, let's assume the primary method should work or be adjusted

    for card in event_cards:
        title_element = card.find('h2', class_='css-1es4gst')
        
        # Try to get the short date (e.g., "Tue Jun 10")
        date_badge_short = card.find('span', class_='css-z4b87k')
        date_short_text = None
        if date_badge_short:
            time_tag_short = date_badge_short.find('time')
            if time_tag_short and time_tag_short.has_attr('datetime'):
                 date_short_text = time_tag_short.get_text(strip=True)


        # Try to get the full date and time (e.g., "Tue Jun 10, 2025 ▪︎ 7PM")
        date_badge_full = card.find('span', class_='css-52t1jy')
        date_full_text = None
        if date_badge_full:
            time_tag_full = date_badge_full.find('time')
            if time_tag_full and time_tag_full.has_attr('datetime'):
                date_full_text = time_tag_full.get_text(strip=True)

        title = title_element.get_text(strip=True) if title_element else "N/A"
        
        # Prefer full date/time if available, otherwise use short date
        display_date_str = date_full_text if date_full_text else date_short_text

        if title != "N/A" and display_date_str:
            shows_data.append({
                "title": title,
                "date_time_str": display_date_str
            })
        elif title_element : # If we found a title but no date, it might be a non-event item, or structure changed
            print(f"Found title '{title}' but no date information. Skipping.")


    if not shows_data and event_cards:
         print("Found event cards, but could not extract details. Check selectors for title and date.")
    elif not shows_data and not event_cards:
        print("No shows found. The website might be structured differently than expected or there are no events listed.")


    return shows_data

def save_shows_to_csv(shows_data):
    """Saves show data to a CSV file."""
    if not shows_data:
        print("No show data to save.")
        return
    
    # Ensure all dicts have the same keys, use a common set of keys
    # For CSV, we'll store the original date_time_str
    field_keys = ["title", "date_time_str"]
    # if shows_data and isinstance(shows_data[0], dict):
    # field_keys = list(shows_data[0].keys())


    with open(SHOWS_CSV_FILE, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=field_keys)
        dict_writer.writeheader()
        # Write only the relevant fields for CSV to keep it simple
        rows_to_write = []
        for show in shows_data:
            rows_to_write.append({k: show.get(k) for k in field_keys})
        dict_writer.writerows(rows_to_write)

    print(f"Saved {len(shows_data)} shows to {SHOWS_CSV_FILE}")

def get_last_known_shows():
    """Reads the last known shows from a file."""
    try:
        with open(LAST_KNOWN_SHOWS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_current_shows_as_known(shows_data):
    """Saves the current shows to a file for future comparison."""
    if not shows_data:
        return
    with open(LAST_KNOWN_SHOWS_FILE, 'w', encoding='utf-8') as f:
        for show in shows_data:
            # Use the original date_time_str for consistency in last_known_shows
            f.write(f"{show['title']}|{show['date_time_str']}\n")

def compare_and_notify(current_shows_data):
    """Compares current shows with last known shows and prints new/removed shows."""
    if not current_shows_data:
        print("No current shows to compare.")
        return

    last_shows_set = get_last_known_shows()
    current_shows_set = set()
    for show in current_shows_data:
        current_shows_set.add(f"{show['title']}|{show['date_time_str']}")

    new_shows = current_shows_set - last_shows_set
    removed_shows = last_shows_set - current_shows_set

    if new_shows:
        print("\n--- New Shows Added ---")
        for show_str in new_shows:
            title, date_time = show_str.split('|', 1)
            print(f"- {title} ({date_time})")
    
    if removed_shows:
        print("\n--- Shows Removed ---")
        for show_str in removed_shows:
            title, date_time = show_str.split('|', 1)
            print(f"- {title} ({date_time})")

    if not new_shows and not removed_shows:
        print("\nNo changes in shows since last check.")

    save_current_shows_as_known(current_shows_data)

def generate_html_report(shows_data, new_shows_set):
    """Generates a print-friendly HTML report of all shows, highlighting new shows."""
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    # Timezone conversion for display
    utc_now = datetime.utcnow().replace(tzinfo=tz.UTC)
    est_tz = tz.gettz(DEFAULT_EVENT_TIMEZONE)
    est_now = utc_now.astimezone(est_tz)
    generated_time_str = est_now.strftime("%Y-%m-%d %I:%M %p %Z")

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Ruoff Music Center Shows</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 0; }}
            .container {{ max-width: 900px; margin: 30px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 32px 40px 40px 40px; }}
            h1 {{ text-align: center; margin-bottom: 0.5em; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 1.5em; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #e9ecef; }}
            th {{ background-color: #f8f9fa; font-weight: 600; }}
            tr.new-show td {{ background-color: #e6ffed; }}
            .badge {{ font-size: 0.8em; padding: 4px 8px; border-radius: 12px; color: #fff; background-color: #007bff; }}
            .badge-new {{ background-color: #28a745; }}
            .footer {{ text-align: center; margin-top: 2em; font-size: 0.9em; color: #777; }}
             @media print {{
                body {{ background: #fff; }}
                .container {{ box-shadow: none; border: 1px solid #ccc; }}
                .badge, .badge-new {{ color: #fff !important; background: #28a745 !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ruoff Music Center Shows</h1>
            <p class="footer">Generated on: {generated_time_str}</p>
            <table>
                <thead>
                    <tr>
                        <th>Date & Time</th>
                        <th>Show</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <div class="footer">
                <p>Generated on: {generated_time_str}</p>
                <p>Source: <a href="{URL}" target="_blank">Live Nation</a></p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    html_rows = []
    if shows_data:
        # Sort shows by parsed date
        current_year = datetime.now().year
        for show in shows_data:
            show['parsed_date'] = parse_show_datetime(show['date_time_str'], current_year, DEFAULT_EVENT_TIMEZONE)
        
        # Filter out shows that couldn't be parsed before sorting
        valid_shows = [s for s in shows_data if s['parsed_date']]
        sorted_shows = sorted(valid_shows, key=lambda x: x['parsed_date'])

        for show in sorted_shows:
            show_key = f"{show['title']}|{show['date_time_str']}"
            is_new = show_key in new_shows_set
            new_show_class = ' class="new-show"' if is_new else ''
            new_badge = ' <span class="badge badge-new">New!</span>' if is_new else ''
            
            # Format the parsed date for display
            date_display = show['parsed_date'].strftime('%a, %b %d, %Y ▪︎ %I:%M %p %Z')
            
            html_rows.append(f'<tr{new_show_class}><td>{date_display}</td><td>{show["title"]}{new_badge}</td></tr>')
    
    table_rows_str = "\n".join(html_rows) if html_rows else "<tr><td colspan='2'>No shows found.</td></tr>"

    html_content = html_template.format(
        generated_time_str=generated_time_str,
        table_rows=table_rows_str,
        URL=URL
    )
    
    # Save the report
    report_path = os.path.join('docs', 'index.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Also save a copy to the root for easier access in some environments
    shutil.copy(report_path, 'ruoff_shows.html')
    
    print(f"Saved HTML report to {report_path}")

def filter_shows(shows_data):
    """Omit shows with the title '2025 Premium Season Ticket Priority List' (case-insensitive, ignore spaces)."""
    return [show for show in shows_data if show['title'].strip().lower() != '2025 premium season ticket priority list']

if __name__ == "__main__":
    print(f"Scraping shows from {URL}...")
    scraped_shows = scrape_shows()
    if scraped_shows:
        scraped_shows = filter_shows(scraped_shows)
    processed_shows_for_calendar = [] # For shows successfully parsed for calendar
    current_year = datetime.now().year

    if scraped_shows:
        print("\n--- All Scraped Shows (Raw Dates) ---")
        for i, show in enumerate(scraped_shows):
            print(f"{i+1}. {show['title']} - {show['date_time_str']}")
            
            # Parse date/time for calendar
            start_datetime_obj = parse_show_datetime(show['date_time_str'], current_year, DEFAULT_EVENT_TIMEZONE)
            show['parsed_start_datetime'] = start_datetime_obj # Store for potential use
            
            if start_datetime_obj:
                processed_shows_for_calendar.append({
                    "title": show['title'],
                    "start_datetime": start_datetime_obj,
                    "end_datetime": start_datetime_obj + timedelta(hours=3), # 3-hour duration
                    "description": f"Show: {show['title']}\nSource: {URL}\nScraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                })
            else:
                print(f"Could not parse date/time for '{show['title']}' ({show['date_time_str']}). Skipping calendar add.")

        save_shows_to_csv(scraped_shows) # Save raw scraped data
        # --- Compare and get new shows ---
        last_shows_set = get_last_known_shows()
        current_shows_set = set(f"{show['title']}|{show['date_time_str']}" for show in scraped_shows)
        new_shows = current_shows_set - last_shows_set
        compare_and_notify(scraped_shows) # Compare based on raw scraped data
        # --- Generate HTML report ---
        generate_html_report(scraped_shows, new_shows)

        if processed_shows_for_calendar:
            print("\n--- Adding/Checking Shows in Google Calendar ---")
            print("Attempting to get Google Calendar service...")
            try:
                cal_service = google_calendar_service.get_calendar_service()

                if cal_service:
                    print("Successfully obtained Google Calendar service.")
                    for show_details in processed_shows_for_calendar:
                        print(f"Processing for calendar: {show_details['title']} at {show_details['start_datetime'].strftime('%Y-%m-%d %I:%M %p %Z')}")
                        google_calendar_service.add_event_to_calendar(
                            service=cal_service,
                            summary=show_details['title'],
                            start_datetime=show_details['start_datetime'],
                            end_datetime=show_details['end_datetime'],
                            description=show_details['description'],
                            timezone=DEFAULT_EVENT_TIMEZONE 
                        )
                else:
                    print("Failed to obtain Google Calendar service. Calendar operations skipped.")
            except Exception as e:
                print(f"Error during calendar operations: {e}")
                print("Calendar operations skipped due to error.")
        else:
            print("\nNo shows with valid date/time information to process for Google Calendar.")

    else:
        print("Failed to scrape shows.")

    print(f"\nFinished script at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 