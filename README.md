# Ruoff Music Center Show Calendar Manager

This project helps manage concert schedules for Ruoff Music Center by adding them to a Google Calendar.

## Features

*   `scrape_ruoff_shows.py`: (Potentially deprecated) Scrapes upcoming shows from Live Nation for Ruoff Music Center and adds them to a Google Calendar. It also attempts to detect new or removed shows compared to the last run.
*   `add_manual_shows_to_calendar.py`: Adds a predefined list of shows for a specific year (currently 2024) to Google Calendar. This is useful for historical data or when scraping is unreliable.
*   `google_calendar_service.py`: Handles the interaction with the Google Calendar API.

## Setup

1.  **Google Calendar API Credentials**:
    *   Enable the Google Calendar API in your Google Cloud Console.
    *   Create OAuth 2.0 credentials and download the `credentials.json` file.
    *   Place `credentials.json` in the root directory of this project.
    *   The first time a script needing calendar access runs, it will prompt you to authorize access via a web browser. This will create a `token.json` file for future authentications.
2.  **Python Environment**:
    *   It's recommended to use a virtual environment.
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```
3.  **Target Calendar ID**:
    *   Open `google_calendar_service.py`.
    *   Update the `TARGET_CALENDAR_ID` variable with the ID of the Google Calendar you want the shows to be added to.

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