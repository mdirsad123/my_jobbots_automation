@echo off

:: Step 1: Activate Poetry Environment (no need to activate manually if using `poetry run`)
cd /d "D:\ird-projects\my_pyautomation"

:: Step 2: Start Chrome with remote debugger
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chromedebug"

:: Step 3: Run your automation script via poetry
call poetry run python noukrigulf_job_bot/main.py

pause
