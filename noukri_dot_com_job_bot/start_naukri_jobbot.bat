@echo off
setlocal EnableExtensions
TITLE JobBots - Naukri Job Bot

REM Use same Chrome debugger startup as the working start_linkedin_fastapi.bat
set "PROJECT_ROOT=D:\ird-projects\sahil_projects\my_jobbots_automation"
set "CHROME_PORT=9222"
set "CHROME_PROFILE=C:\chromedebug"
set "PROJECT_OPENED=0"

ECHO ==============================================================
ECHO    JobBots - Naukri Job Bot
ECHO ==============================================================
ECHO.

ECHO [1/4] Opening project directory...
if not exist "%PROJECT_ROOT%\noukri_dot_com_job_bot\main.py" (
    ECHO ERROR: Naukri bot module not found:
    ECHO   "%PROJECT_ROOT%\noukri_dot_com_job_bot\main.py"
    goto :FAILED
)
pushd "%PROJECT_ROOT%"
if errorlevel 1 (
    ECHO ERROR: Cannot open "%PROJECT_ROOT%".
    goto :FAILED
)
set "PROJECT_OPENED=1"
set "PYTHONPATH=%PROJECT_ROOT%"
ECHO Project: %CD%
ECHO.

ECHO [2/4] Checking Chrome debugger on port %CHROME_PORT%...
call :ENSURE_CHROME_DEBUGGER
if errorlevel 1 goto :FAILED
ECHO.

ECHO [3/4] Activating Python virtual environment...
if not exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    ECHO ERROR: Missing virtual environment: .venv\Scripts\activate.bat
    goto :FAILED
)
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
if errorlevel 1 (
    ECHO ERROR: Virtual environment activation failed.
    goto :FAILED
)
ECHO Virtual environment ready.
ECHO.

ECHO [4/4] Running Naukri job search and apply bot...

python noukri_dot_com_job_bot/main.py

set "BOT_EXIT=%ERRORLEVEL%"
ECHO.
if not "%BOT_EXIT%"=="0" (
    ECHO Naukri bot finished with ERROR code %BOT_EXIT%.
) else (
    ECHO Naukri bot completed successfully.
)
goto :DONE

REM ============================================================== 
REM Helper routines -- same tested pattern as LinkedIn FastAPI BAT
REM ============================================================== 
:ENSURE_CHROME_DEBUGGER
call :IS_DEVTOOLS_READY
if not errorlevel 1 (
    ECHO Chrome debugger already ready on port %CHROME_PORT%. Reusing it.
    exit /b 0
)

set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_EXE%" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_EXE%" set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_EXE%" (
    ECHO ERROR: Chrome executable not found in standard locations.
    exit /b 1
)

ECHO Starting Chrome with remote debugging on port %CHROME_PORT%...
ECHO Chrome profile: %CHROME_PROFILE%
start "" "%CHROME_EXE%" --remote-debugging-port=%CHROME_PORT% --remote-debugging-address=127.0.0.1 --user-data-dir="%CHROME_PROFILE%" --no-first-run "about:blank"

set /a CHROME_WAIT_COUNT=0
:WAIT_FOR_DEBUGGER
call :IS_DEVTOOLS_READY
if not errorlevel 1 (
    ECHO Chrome debugger is ready.
    exit /b 0
)
set /a CHROME_WAIT_COUNT+=1 >nul
if %CHROME_WAIT_COUNT% GEQ 30 (
    ECHO ERROR: Chrome debugger did not respond within about 60 seconds.
    ECHO Check whether another Chrome instance is using "%CHROME_PROFILE%".
    ECHO Also check whether port %CHROME_PORT% is occupied.
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto :WAIT_FOR_DEBUGGER

:IS_DEVTOOLS_READY
REM Check DevTools HTTP JSON endpoint, not just whether TCP port is open.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:%CHROME_PORT%/json/version' -TimeoutSec 2 -ErrorAction Stop; if ($r.Browser -and $r.webSocketDebuggerUrl) { exit 0 } } catch {} ; exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:FAILED
set "BOT_EXIT=1"
ECHO.
ECHO ERROR: Naukri Job Bot startup failed.

:DONE
ECHO.
ECHO Press any key to close this window. Chrome will remain open.
pause >nul
if "%PROJECT_OPENED%"=="1" popd
exit /b %BOT_EXIT%
