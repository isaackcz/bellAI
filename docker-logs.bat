@echo off
REM PepperAI Docker Logs Script for Windows
echo Viewing PepperAI Docker Logs...
echo Press Ctrl+C to exit
echo.

REM Show logs for all services
docker-compose logs -f
