@echo off
echo ========================================
echo   PepperAI - Starting Application
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "env\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment found
)

echo.
echo [INFO] Installing/Updating dependencies...
pip install flask-sqlalchemy --quiet

echo.
echo [INFO] Starting PepperAI...
echo [INFO] Access the app at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause

