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

def filter_shows(shows_data):
    """Omit shows with the title '2025 Premium Season Ticket Priority List' (case-insensitive, ignore spaces)."""
    return [show for show in shows_data if show['title'].strip().lower() != '2025 premium season ticket priority list'] 