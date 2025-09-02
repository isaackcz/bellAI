@echo off
setlocal

REM Change to the directory of this script
cd /d %~dp0

REM Ensure virtual environment exists (optional safety)
if not exist "env\Scripts\python.exe" (
    echo [INFO] Python virtual environment not found. Creating one...
    py -3 -m venv env || (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

REM Activate the virtual environment
call "env\Scripts\activate.bat" || (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)

REM Upgrade pip quietly (optional but helpful)
python -m pip install --upgrade pip -q

REM Install dependencies if requirements.txt is present
if exist requirements.txt (
    echo [INFO] Installing dependencies...
    python -m pip install -r requirements.txt || (
        echo [ERROR] Dependency installation failed.
        exit /b 1
    )
)

REM Set Flask-related environment variables (harmless even if app runs via python app.py)
set "FLASK_APP=app.py"
set "FLASK_ENV=development"

REM Start the application
echo [INFO] Launching application...
python app.py

endlocal

