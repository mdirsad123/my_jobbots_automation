@echo off
title JobBots Email Sender Automation

echo ============================================
echo     JobBots Email Sender Automation
echo ============================================
echo.

:: -------------------------------------------------
:: 1. Navigate to project root
:: -------------------------------------------------

cd /d "D:\ird-projects\sahil_projects\my_jobbots_automation"

if errorlevel 1 (
    echo.
    echo ERROR: Could not navigate to project folder.
    echo.
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

echo PYTHONPATH set successfully.
echo.

:: -------------------------------------------------
:: 3. Activate virtual environment
:: -------------------------------------------------

echo Activating virtual environment...

call "D:\ird-projects\sahil_projects\my_jobbots_automation\.venv\Scripts\activate.bat"

if errorlevel 1 (
    echo.
    echo ============================================
    echo   ERROR: VIRTUAL ENV ACTIVATION FAILED
    echo ============================================
    echo.
    pause
    exit /b 1
)

echo Virtual environment activated.
echo.

:: -------------------------------------------------
:: 4. Run email automation script
:: -------------------------------------------------

echo ============================================
echo   Starting Email Automation...
echo ============================================
echo.

python -m linkedin.services.manual_email_sender

:: Save Python exit code immediately
set "EXIT_CODE=%ERRORLEVEL%"

:: -------------------------------------------------
:: 5. Check result
:: -------------------------------------------------

if not "%EXIT_CODE%"=="0" (
    echo.
    echo ============================================
    echo   EMAIL AUTOMATION FAILED
    echo ============================================
    echo.
    echo Exit Code: %EXIT_CODE%
) else (
    echo.
    echo ============================================
    echo   EMAIL AUTOMATION COMPLETED SUCCESSFULLY
    echo ============================================
)

echo.
echo ============================================
echo   Process Finished
echo ============================================
echo.

pause