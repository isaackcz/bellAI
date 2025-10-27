@echo off
REM PepperAI Docker Stop Script for Windows
echo Stopping PepperAI Docker Environment...
echo.

REM Stop all services
docker-compose down

if %errorlevel% equ 0 (
    echo ✅ PepperAI services stopped successfully.
) else (
    echo ⚠️  Some services may not have stopped cleanly.
)

echo.
echo To remove all data and start fresh, run: docker-compose down -v
echo.
pause
