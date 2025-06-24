import csv
import json

def save_shows_to_csv(shows_data, csv_file_path):
    """Saves show data to a CSV file."""
    if not shows_data:
        print("No show data to save.")
        return
    
    field_keys = ["title", "date_time_str"]

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=field_keys)
        dict_writer.writeheader()
        rows_to_write = [{k: show.get(k) for k in field_keys} for show in shows_data]
        dict_writer.writerows(rows_to_write)

    print(f"Saved {len(shows_data)} shows to {csv_file_path}")

def get_last_known_shows(last_known_shows_file_path):
    """Reads the last known shows from a file."""
    try:
        with open(last_known_shows_file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_current_shows_as_known(shows_data, last_known_shows_file_path):
    """Saves the current shows to a file for future comparison."""
    if not shows_data:
        return
    with open(last_known_shows_file_path, 'w', encoding='utf-8') as f:
        for show in shows_data:
            f.write(f"{show['title']}|{show['date_time_str']}\n")

def load_show_add_times(show_add_times_file_path):
    """Loads the timestamp of when each show was first added."""
    try:
        with open(show_add_times_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_show_add_times(add_times, show_add_times_file_path):
    """Saves the show addition timestamps to a file."""
    with open(show_add_times_file_path, 'w', encoding='utf-8') as f:
        json.dump(add_times, f, indent=4) 