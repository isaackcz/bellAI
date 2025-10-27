@echo off
REM PepperAI Docker Startup Script for Windows
echo Starting PepperAI Docker Environment...
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration before running again.
    pause
    exit /b 1
)

REM Create necessary directories
if not exist backups mkdir backups
if not exist logs mkdir logs

echo Building and starting PepperAI services...
docker-compose up --build -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ PepperAI is starting up!
    echo.
    echo 🌐 Web Interface: http://localhost
    echo 🔍 Health Check: http://localhost/health
    echo.
    echo 📊 To view logs: docker-compose logs -f
    echo 🛑 To stop: docker-compose down
    echo.
    echo Waiting for services to be ready...
    timeout /t 10 /nobreak >nul
    
    REM Check if services are healthy
    curl -s http://localhost/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ PepperAI is ready! Open http://localhost in your browser.
    ) else (
        echo ⚠️  Services are starting up. Please wait a moment and check http://localhost
    )
) else (
    echo ❌ Failed to start PepperAI. Check the logs above for errors.
)

echo.
pause
