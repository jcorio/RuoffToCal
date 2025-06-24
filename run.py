from datetime import datetime, timedelta

import google_calendar_service
from scraper import scrape_shows, filter_shows
from data_manager import (
    save_shows_to_csv, get_last_known_shows, save_current_shows_as_known,
    load_show_add_times, save_show_add_times
)
from html_generator import generate_html_report
from date_parser import parse_show_datetime

# --- Constants ---
URL = "https://www.livenation.com/venue/KovZpvEk7A/ruoff-music-center-events"
SHOWS_CSV_FILE = "ruoff_shows.csv"
LAST_KNOWN_SHOWS_FILE = "last_known_shows.txt"
SHOW_ADD_TIMES_FILE = "show_add_times.json"
DEFAULT_EVENT_TIMEZONE = "America/New_York"


def compare_and_notify(current_shows_data, last_known_shows_file_path):
    """Compares current shows with last known shows and prints new/removed shows."""
    if not current_shows_data:
        print("No current shows to compare.")
        return

    last_shows_set = get_last_known_shows(last_known_shows_file_path)
    current_shows_set = {f"{show['title']}|{show['date_time_str']}" for show in current_shows_data}

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

    return new_shows

def main():
    """Main function to orchestrate the scraping and processing."""
    print(f"Scraping shows from {URL}...")
    scraped_shows = scrape_shows(URL)
    
    if not scraped_shows:
        print("Failed to scrape shows. Exiting.")
        return

    scraped_shows = filter_shows(scraped_shows)
    
    print("\n--- All Scraped Shows ---")
    for i, show in enumerate(scraped_shows, 1):
        print(f"{i}. {show['title']} - {show['date_time_str']}")
    
    save_shows_to_csv(scraped_shows, SHOWS_CSV_FILE)

    # --- Comparison and Notification ---
    new_shows_set = compare_and_notify(scraped_shows, LAST_KNOWN_SHOWS_FILE)
    save_current_shows_as_known(scraped_shows, LAST_KNOWN_SHOWS_FILE)
    
    # --- Add Times Persistence ---
    show_add_times = load_show_add_times(SHOW_ADD_TIMES_FILE)
    now_iso = datetime.now().isoformat()
    current_shows_set = {f"{show['title']}|{show['date_time_str']}" for show in scraped_shows}
    for show_key in current_shows_set:
        if show_key not in show_add_times:
            show_add_times[show_key] = now_iso
    save_show_add_times(show_add_times, SHOW_ADD_TIMES_FILE)

    # --- Generate HTML Report ---
    generate_html_report(scraped_shows, new_shows_set, show_add_times, DEFAULT_EVENT_TIMEZONE, URL)

    # --- Google Calendar Integration ---
    print("\n--- Processing for Google Calendar ---")
    cal_service = google_calendar_service.get_calendar_service()
    if not cal_service:
        print("Failed to obtain Google Calendar service. Calendar operations skipped.")
        return

    print("Successfully obtained Google Calendar service.")
    current_year = datetime.now().year
    for show in scraped_shows:
        start_datetime_obj = parse_show_datetime(show['date_time_str'], current_year, DEFAULT_EVENT_TIMEZONE)
        
        if start_datetime_obj:
            print(f"Processing for calendar: {show['title']} at {start_datetime_obj.strftime('%Y-%m-%d %I:%M %p %Z')}")
            google_calendar_service.add_event_to_calendar(
                service=cal_service,
                summary=show['title'],
                start_datetime=start_datetime_obj,
                end_datetime=start_datetime_obj + timedelta(hours=3),
                description=f"Show: {show['title']}\nSource: {URL}\nScraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                timezone=DEFAULT_EVENT_TIMEZONE
            )
        else:
            print(f"Could not parse date/time for '{show['title']}' ({show['date_time_str']}). Skipping calendar add.")

if __name__ == "__main__":
    main()
    print(f"\nFinished script at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 