import requests
from bs4 import BeautifulSoup

def scrape_shows(url):
    """Scrapes show information from the Live Nation website."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

import re

def scrape_shows(url):
    """Scrapes show information from the Live Nation website."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    content = response.text
    shows_data = []

    # LiveNation now embeds event data as escaped JSON within streaming script tags.
    # We use regex to extract the show name and date, filtering for Ruoff Music Center.
    name_pattern = r'\\"name\\":\\"(.*?)\\"'
    date_pattern = r'\\"start_date_local\\":\\"(.*?)\\"'
    venue_pattern = r'\\"venue_name\\":\\"(.*?)\\"'

    # Find all occurrences of start_date_local and look back for name and venue.
    for m in re.finditer(date_pattern, content):
        start = m.start()
        # Look back 1000 characters for the corresponding name and venue keys.
        lookback = content[max(0, start-1000):start]
        name_match = re.findall(name_pattern, lookback)
        venue_match = re.findall(venue_pattern, lookback)

        if name_match:
            name = name_match[-1] # The most recent name before the date is the show name.
            date_str = m.group(1)
            venue = venue_match[-1] if venue_match else "Unknown"

            if "Ruoff" in venue:
                # Clean up name if it contains escaped characters.
                name = name.replace('\\"', '"').replace("\\'", "'")
                shows_data.append({
                    "title": name,
                    "date_time_str": date_str
                })

    if not shows_data:
        print("No shows found. The website structure might have changed significantly.")

    return shows_data

def filter_shows(shows_data):
    """Omit shows with the title '2025 Premium Season Ticket Priority List' (case-insensitive, ignore spaces)."""
    return [show for show in shows_data if show['title'].strip().lower() != '2025 premium season ticket priority list'] 