@echo off
REM PepperAI Docker Reset Script for Windows
echo WARNING: This will remove ALL PepperAI data including:
echo - Database
echo - Uploaded files
echo - Results
echo - Redis cache
echo.
set /p confirm="Are you sure you want to continue? (y/N): "

if /i not "%confirm%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo Stopping and removing all PepperAI containers and data...
docker-compose down -v

echo.
echo Removing unused Docker images...
docker image prune -f

echo.
echo ✅ PepperAI has been completely reset.
echo Run docker-start.bat to start fresh.
echo.
pause
