@echo off
REM ===========================================================================
REM  TeachersAid - start the review dashboard.  Double-click this file to run.
REM
REM  First run: creates a local .venv and installs dependencies (a few minutes)
REM             and seeds the master-library examples into the review queue.
REM  Later runs: start instantly.
REM  Stop the server with Ctrl+C in this window.
REM ===========================================================================
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [setup] Creating virtual environment ^(first run only^)...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if not exist "%PY%" (
        echo [error] Could not create .venv. Install Python 3.11-3.14 from python.org, then retry.
        pause
        exit /b 1
    )
    echo [setup] Installing dependencies ^(this can take a few minutes^)...
    "%PY%" -m pip install -q -U pip
    "%PY%" -m pip install -q -e .
    if errorlevel 1 (
        echo [error] Dependency install failed. See the messages above.
        pause
        exit /b 1
    )
)

if not exist "runs\store" (
    echo [seed] Loading master-library examples into the review queue...
    "%PY%" -m teachersaid seed
)

echo.
echo  TeachersAid dashboard:  http://127.0.0.1:8000
echo  ^(this window runs the server - press Ctrl+C to stop^)
echo.
REM open the browser shortly after the server comes up (detached, best-effort)
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000'"
"%PY%" -m teachersaid

endlocal
