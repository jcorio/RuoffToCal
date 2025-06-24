@echo off
echo Installing/updating dependencies...
pip install -r requirements.txt

echo Running Ruoff Shows scraper...
python run.py

echo Done!
pause 