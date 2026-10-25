@echo off
setlocal EnableExtensions

title JobBots - ChatGPT CV Generator

rem =============================================================
rem SETTINGS: match your existing working Chrome debug profile
rem =============================================================
set "PROJECT_ROOT=D:\ird-projects\sahil_projects\my_jobbots_automation"
set "VENV_ACTIVATE=%PROJECT_ROOT%\.venv\Scripts\activate.bat"
set "CHROME_PROFILE=C:\chromedebug"
set "DEBUG_PORT=9222"
set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"

rem Give a newly launched Chrome up to 80 seconds to expose DevTools.
set "MAX_ATTEMPTS=40"

echo ============================================================
echo   JobBots - ChatGPT CV Generator
echo ============================================================
echo.

rem 0. Validate project and enter its root.
if not exist "%PROJECT_ROOT%\linkedin\runners\chatgpt_cv_generator.py" (
    echo ERROR: ChatGPT CV runner not found:
    echo   %PROJECT_ROOT%\linkedin\runners\chatgpt_cv_generator.py
    goto :FAILED
)
if not exist "%PROJECT_ROOT%\linkedin\services\chatgpt_cvs_generator.py" (
    echo ERROR: ChatGPT CV service not found:
    echo   %PROJECT_ROOT%\linkedin\services\chatgpt_cvs_generator.py
    goto :FAILED
)
cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo ERROR: Cannot enter project directory: %PROJECT_ROOT%
    goto :FAILED
)
set "PYTHONPATH=%PROJECT_ROOT%"
echo Project: %CD%
echo.

rem 1. Reuse Chrome if its DevTools endpoint is already available.
echo [1/3] Checking Chrome DevTools on port %DEBUG_PORT%...
call :IS_DEBUGGER_READY
if not errorlevel 1 (
    echo Existing Chrome debugger is READY. Reusing it.
    goto :DEBUGGER_READY
)

rem Is another process listening on 9222? If so, do not launch another.
call :IS_PORT_LISTENING
if not errorlevel 1 (
    echo Port %DEBUG_PORT% is listening but DevTools is not ready yet.
    echo Waiting for the existing listener...
    goto :WAIT_FOR_DEBUGGER
)

rem Find Chrome in common installation locations.
if not exist "%CHROME_EXE%" (
    if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    ) else (
        if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
            set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        ) else (
            echo ERROR: chrome.exe not found in standard installation paths.
            echo Edit CHROME_EXE at the top of this BAT file.
            goto :FAILED
        )
    )
)

echo Port %DEBUG_PORT% is free. Starting Chrome with remote debugging...
echo Chrome:  %CHROME_EXE%
echo Profile: %CHROME_PROFILE%

rem IMPORTANT: Do NOT test ERRORLEVEL immediately after START.
rem The previous (failed) port check can leave ERRORLEVEL=1 even if
rem START successfully launches Chrome. Probe /json/version instead.
start "" "%CHROME_EXE%" --remote-debugging-port=%DEBUG_PORT% --remote-debugging-address=127.0.0.1 --user-data-dir="%CHROME_PROFILE%" --no-first-run --no-default-browser-check "https://chatgpt.com/"
echo Chrome launch requested; waiting for the debugger endpoint...

:WAIT_FOR_DEBUGGER
set /a WAIT_ATTEMPT=0
:WAIT_LOOP
call :IS_DEBUGGER_READY
if not errorlevel 1 goto :DEBUGGER_READY
set /a WAIT_ATTEMPT+=1
if %WAIT_ATTEMPT% GEQ %MAX_ATTEMPTS% (
    echo.
    echo ERROR: Chrome DevTools did not become ready within 80 seconds.
    echo Check Chrome at http://127.0.0.1:%DEBUG_PORT%/json/version
    echo If Chrome opened without a debugger, close Chrome windows using
    echo the profile %CHROME_PROFILE% and run this BAT again.
    echo If another application is using port %DEBUG_PORT%, close it first.
    goto :FAILED
)
if %WAIT_ATTEMPT% EQU 10 echo Still waiting for Chrome debugger... ^(20 seconds^)
if %WAIT_ATTEMPT% EQU 20 echo Still waiting for Chrome debugger... ^(40 seconds^)
if %WAIT_ATTEMPT% EQU 30 echo Still waiting for Chrome debugger... ^(60 seconds^)
timeout /t 2 /nobreak >nul
goto :WAIT_LOOP

:DEBUGGER_READY
echo Chrome DevTools is READY at http://127.0.0.1:%DEBUG_PORT%/json/version
echo.

rem 2. Activate the existing project virtual environment.
echo [2/3] Activating project virtual environment...
if not exist "%VENV_ACTIVATE%" (
    echo ERROR: Virtual environment activation file not found:
    echo   %VENV_ACTIVATE%
    goto :FAILED
)
call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo ERROR: Virtual environment activation failed.
    goto :FAILED
)
echo Virtual environment activated.
echo.

rem 3. Run the runner: it selects today's date (IST) automatically.
rem Pass through optional arguments, e.g. --dry-run or --force.
echo [3/3] Running ChatGPT CV generator for today's JD folder...
echo.
python -m linkedin.services.chatgpt_job_grouping %*
set "RUN_EXIT_CODE=%ERRORLEVEL%"
if not "%RUN_EXIT_CODE%"=="0" (
    echo.
    echo ERROR: ChatGPT CV runner returned exit code %RUN_EXIT_CODE%.
    goto :FAILED
)

echo.
echo ============================================================
echo   SUCCESS: ChatGPT CV requests processed.
echo   Chrome stays open for ongoing CV generation.
echo ============================================================
echo.
pause
exit /b 0

:FAILED
echo.
echo ============================================================
echo   JobBots - ChatGPT CV automation FAILED.
echo ============================================================
echo.
pause
exit /b 1

:IS_PORT_LISTENING
powershell.exe -NoProfile -NonInteractive -Command "if (Get-NetTCPConnection -LocalPort %DEBUG_PORT% -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>&1
exit /b %ERRORLEVEL%

:IS_DEBUGGER_READY
powershell.exe -NoProfile -NonInteractive -Command "try { $info = Invoke-RestMethod -Uri 'http://127.0.0.1:%DEBUG_PORT%/json/version' -TimeoutSec 2 -ErrorAction Stop; if ($info.Browser -and $info.webSocketDebuggerUrl) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
exit /b %ERRORLEVEL%
