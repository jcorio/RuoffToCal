@echo off
echo Installing/updating dependencies...
pip install -r requirements.txt

echo Running Ruoff Shows scraper...
python scrape_ruoff_shows.py

echo Done!
pause 