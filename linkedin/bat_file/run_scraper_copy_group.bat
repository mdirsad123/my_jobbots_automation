@echo off
title Run Scraper + Group + Copy Specific

echo ============================================
echo   JobBots LinkedIn Scraper Automation
echo ============================================
echo.

:: -------------------------------------------------
:: 1. Navigate to project root
:: -------------------------------------------------
cd /d "D:\ird-projects\sahil_projects\my_jobbots_automation"

if errorlevel 1 (
    echo ERROR: Could not navigate to project folder.
    pause
    exit /b 1
)

echo Project folder:
echo %CD%
echo.

:: -------------------------------------------------
:: 2. Set project root as PYTHONPATH
:: -------------------------------------------------
set "PYTHONPATH=%CD%"

:: -------------------------------------------------
:: 3. Start Chrome with Remote Debugging Port
:: -------------------------------------------------
echo Starting Chrome Debugger on port 9222...

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="C:\chromedebug"

:: Give Chrome a few seconds to start
timeout /t 3 /nobreak >nul

echo Chrome debugger started.
echo.

:: -------------------------------------------------
:: 4. Activate virtual environment
:: -------------------------------------------------
echo Activating virtual environment...

call "D:\ird-projects\sahil_projects\my_jobbots_automation\.venv\Scripts\activate.bat"

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Virtual environment activated.
echo.

:: -------------------------------------------------
:: 5. Run LinkedIn Scraper
::    Scrape -> Group Roles -> Copy Specific Folder
:: -------------------------------------------------
echo Starting LinkedIn scraper...
echo.

python -m linkedin.runners.run_scraper

:: -------------------------------------------------
:: 6. Check result
:: -------------------------------------------------
if errorlevel 1 (
    echo.
    echo ============================================
    echo   SCRAPER FAILED
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   SCRAPER COMPLETED SUCCESSFULLY
    echo ============================================
)

echo.
pause