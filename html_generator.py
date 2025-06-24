import os
import shutil
from datetime import datetime
from dateutil import tz
from dateutil import parser as dateutil_parser

from date_parser import parse_show_datetime

def generate_html_report(shows_data, new_shows_set, show_add_times, default_timezone, url):
    """Generates a print-friendly HTML report of all shows, highlighting new shows and showing add date."""
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    # Timezone conversion for display
    utc_now = datetime.utcnow().replace(tzinfo=tz.UTC)
    est_tz = tz.gettz(default_timezone)
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
                        <th style="font-size: 0.9em; color: #555;">Added On</th>
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
            show['parsed_date'] = parse_show_datetime(show['date_time_str'], current_year, default_timezone)
        
        # Filter out shows that couldn't be parsed before sorting
        valid_shows = [s for s in shows_data if s['parsed_date']]
        sorted_shows = sorted(valid_shows, key=lambda x: x['parsed_date'])

        for show in sorted_shows:
            show_key = f"{show['title']}|{show['date_time_str']}"
            is_new = show_key in new_shows_set
            new_show_class = ' class="new-show"' if is_new else ''
            new_badge = ' <span class="badge badge-new">New!</span>' if is_new else ''
            
            # Format the parsed date for display
            date_display = show['parsed_date'].strftime('%a, %b %d, %Y | %I:%M %p %Z')
            
            # Get and format the "added on" timestamp
            added_on_str = ""
            added_timestamp_iso = show_add_times.get(show_key)
            if added_timestamp_iso:
                try:
                    # Parse the ISO format string and format it to a simple M/D/YYYY
                    added_dt = dateutil_parser.isoparse(added_timestamp_iso)
                    added_on_str = f"{added_dt.month}/{added_dt.day}/{added_dt.year}"
                except (ValueError, TypeError):
                    added_on_str = "N/A"

            html_rows.append(f'<tr{new_show_class}><td>{date_display}</td><td>{show["title"]}{new_badge}</td><td style="font-size: 0.9em; color: #555;">{added_on_str}</td></tr>')
    
    table_rows_str = "\n".join(html_rows) if html_rows else "<tr><td colspan='3'>No shows found.</td></tr>"

    html_content = html_template.format(
        generated_time_str=generated_time_str,
        table_rows=table_rows_str,
        URL=url
    )
    
    # Save the report
    report_path = os.path.join('docs', 'index.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Also save a copy to the root for easier access in some environments
    shutil.copy(report_path, 'ruoff_shows.html')
    
    print(f"Saved HTML report to {report_path}") 