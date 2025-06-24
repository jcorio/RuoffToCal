# Ruoff Music Center Show Calendar Manager

This project scrapes upcoming shows for Ruoff Music Center from Live Nation, adds them to a Google Calendar, and generates an HTML report. The process is fully automated to run daily via GitHub Actions.

## Features

*   **Daily Scraping**: Automatically scrapes show data from the Live Nation website.
*   **Google Calendar Integration**: Adds new shows to a specified Google Calendar and intelligently skips duplicates.
*   **New/Removed Show Notifications**: Compares the latest scrape against the previous day's list and logs any new or removed shows.
*   **HTML Report**: Generates a clean, print-friendly HTML report (`docs/index.html`) of all current shows, highlighting new ones and noting when they were first added.
*   **Persistent Timestamps**: Tracks when each show was first detected and displays this "Added On" date in the report.

## Project Structure

The project is organized into several modules for clarity and maintainability:

*   `run.py`: The main executable script that orchestrates the entire process.
*   `scraper.py`: Handles all web scraping logic using `requests` and `BeautifulSoup`.
*   `date_parser.py`: Manages complex date and time string parsing.
*   `data_manager.py`: Handles reading from and writing to local data files (`.csv`, `.txt`, `.json`).
*   `html_generator.py`: Contains the logic for creating the HTML report.
*   `google_calendar_service.py`: Manages all interactions with the Google Calendar API.

## Setup

1.  **Google Cloud Project**:
    *   Enable the Google Calendar API in your Google Cloud Console.
    *   Create a **Service Account** and download its JSON key file.
    *   Rename the key file to `credentials.json` and place it in the root directory.
    *   Share your target Google Calendar with the service account's email address (found in `credentials.json`), giving it permission to "Make changes to events".

2.  **GitHub Repository Secrets**:
    *   `GOOGLE_CREDENTIALS_JSON`: The entire content of your `credentials.json` file.
    *   `GOOGLE_TOKEN_JSON`: This is for the deprecated OAuth flow and is no longer needed with a Service Account. You can remove this secret.
    *   `GH_PAT`: A GitHub Personal Access Token with `repo` scope, used by the workflow to push updated data files back to the repository.

3.  **Python Environment**:
    *   It's recommended to use a virtual environment.
    *   Install dependencies: `pip install -r requirements.txt`

4.  **Target Calendar ID**:
    *   Open `google_calendar_service.py`.
    *   Update the `TARGET_CALENDAR_ID` variable with your Google Calendar's ID.

## Usage

*   **Automated**: The GitHub Actions workflow in `.github/workflows/daily-scrape.yml` runs automatically every day.
*   **Manual**: To run the script locally, use the batch file:
    ```powershell
    .\run_scraper.bat
    ```

## Manually Added Shows for 2024

The following shows are currently configured in `add_manual_shows_to_calendar.py` for the year 2024:

```
May 23: 21 Savage
May 28: Hozier
May 31: Noah Kahan
June 1: HARDY
June 8: Hootie and the Blowfish
June 11: James Taylor
June 14: Dierks Bentley
June 20: Kenny Chesney
June 22: Maroon 5
June 23: Santana and Counting Crows
June 27: Tyler Childers
June 28-29: Dave Matthews Band
July 5: KIDZ BOP Live
July 6: Third Eye Blind
July 10: Train & REO Speedwagon
July 11: Halestorm and I Prevail
July 12: Bret Michaels – Parti Gras 2024
July 13: Niall Horan
July 19: Dan + Shay
July 20: Earth, Wind & Fire and Chicago
July 21: LOSERVILLE 2024 with Limp Bizkit
July 25: Red Hot Chili Peppers
July 26: Styx & Foreigner
July 27: Alanis Morissette
Aug. 2-4: Phish
Aug. 6: Slipknot
Aug. 7: Cage The Elephant
Aug. 9: Thirty Seconds To Mars
Aug. 10: Creed
Aug. 16: Five Finger Death Punch
Aug. 17: The Doobie Brothers
Aug. 20: Imagine Dragons
Aug. 23: Glass Animals
Aug. 25: New Kids On The Block
Aug. 26: Pearl Jam
Aug. 30: Sammy Hagar
Aug. 31: Rob Zombie and Alice Cooper
Sept. 1: Pitbull
Sept. 7: Luke Bryan
Sept. 13: Staind and Breaking Benjamin
Sept. 14: ZZ Top and Lynyrd Skynyrd
Sept. 15: Stone Temple Pilots and LIVE
Sept. 20: Megadeth
Oct. 4: Meghan Trainor
```

## Usage

*   To add the manually defined 2024 shows:
    ```powershell
    python.exe .\add_manual_shows_to_calendar.py
    ```
*   To scrape current shows (if `scrape_ruoff_shows.py` is still in use):
    ```powershell
    python.exe .\scrape_ruoff_shows.py
    ``` 