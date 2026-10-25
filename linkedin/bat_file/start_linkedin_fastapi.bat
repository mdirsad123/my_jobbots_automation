@echo off
setlocal EnableExtensions
TITLE JobBots - LinkedIn FastAPI

REM ==============================================================
REM Configuration
REM ==============================================================
set "PROJECT_ROOT=D:\ird-projects\sahil_projects\my_jobbots_automation"
set "CHROME_PORT=9222"
set "CHROME_PROFILE=C:\chromedebug"
set "API_HOST=127.0.0.1"
set "API_PORT=8000"

ECHO ==============================================================
ECHO    JobBots - LinkedIn FastAPI
ECHO ==============================================================
ECHO.

REM 1. Open the project root.
ECHO [1/4] Opening project directory...
if not exist "%PROJECT_ROOT%\linkedin\linkedin_fastapi.py" (
    ECHO ERROR: FastAPI file not found:
    ECHO   "%PROJECT_ROOT%\linkedin\linkedin_fastapi.py"
    GOTO :FAILED
)
pushd "%PROJECT_ROOT%"
if errorlevel 1 (
    ECHO ERROR: Cannot open "%PROJECT_ROOT%".
    GOTO :FAILED
)
set "PYTHONPATH=%PROJECT_ROOT%"
ECHO Project: %CD%
ECHO.

REM 2. Reuse a working DevTools endpoint or launch Chrome and wait.
ECHO [2/4] Checking Chrome debugger on port %CHROME_PORT%...
call :ENSURE_CHROME_DEBUGGER
if errorlevel 1 GOTO :FAILED
ECHO.

REM 3. Activate the existing Python virtual environment.
ECHO [3/4] Activating Python virtual environment...
if not exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    ECHO ERROR: Virtual environment missing: ".venv\Scripts\activate.bat".
    GOTO :FAILED
)
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
if errorlevel 1 (
    ECHO ERROR: Could not activate virtual environment.
    GOTO :FAILED
)
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    ECHO ERROR: Missing FastAPI/Uvicorn. Inside the venv run:
    ECHO   python -m pip install fastapi uvicorn
    GOTO :FAILED
)
ECHO Virtual environment ready.
ECHO.

REM 4. Run Uvicorn in the foreground. Keep this window open.
ECHO [4/4] Starting LinkedIn FastAPI...
ECHO Docs:   http://%API_HOST%:%API_PORT%/docs
ECHO Stop API with Ctrl+C. Chrome stays open.
ECHO.
python -m uvicorn linkedin.linkedin_fastapi:app --host %API_HOST% --port %API_PORT%
set "API_EXIT_CODE=%ERRORLEVEL%"
ECHO.
ECHO FastAPI stopped. Exit code: %API_EXIT_CODE%
ECHO.
pause
popd
exit /b %API_EXIT_CODE%

REM ==============================================================
REM Helpers
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
REM Do not trust START's errorlevel: check Chrome DevTools instead.
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
    ECHO ERROR: Chrome debugger was not ready after about 60 seconds.
    ECHO Check whether another Chrome instance is using "%CHROME_PROFILE%".
    ECHO Also check whether something else is using port %CHROME_PORT%.
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto :WAIT_FOR_DEBUGGER

:IS_DEVTOOLS_READY
REM Probe the actual Chrome DevTools JSON endpoint, not merely an open TCP port.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:%CHROME_PORT%/json/version' -TimeoutSec 2 -ErrorAction Stop; if ($r.Browser -and $r.webSocketDebuggerUrl) { exit 0 } } catch {} ; exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:FAILED
ECHO.
ECHO ==============================================================
ECHO   JobBots LinkedIn FastAPI startup FAILED.
ECHO ==============================================================
ECHO.
pause
popd >nul 2>&1
exit /b 1
