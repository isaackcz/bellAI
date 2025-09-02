@echo off
setlocal

REM Change to the directory of this script
cd /d %~dp0

REM Configuration
set "IMAGE_NAME=pepperai"
set "IMAGE_TAG=%1"
if "%IMAGE_TAG%"=="" set "IMAGE_TAG=latest"

REM Check Docker availability
where docker >nul 2>&1 || (
    echo [ERROR] Docker is not installed or not in PATH. Install Docker Desktop and retry.
    exit /b 1
)

echo [INFO] Building Docker image %IMAGE_NAME%:%IMAGE_TAG%

REM Prefer buildx if available
docker buildx version >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Using docker buildx...
    docker buildx build --load -t %IMAGE_NAME%:%IMAGE_TAG% -f Dockerfile . || (
        echo [ERROR] Docker buildx build failed.
        exit /b 1
    )
) else (
    echo [INFO] Using docker build...
    docker build -t %IMAGE_NAME%:%IMAGE_TAG% -f Dockerfile . || (
        echo [ERROR] Docker build failed.
        exit /b 1
    )
)

echo [INFO] Build complete: %IMAGE_NAME%:%IMAGE_TAG%
echo [INFO] Run the image with:
echo    docker run --rm -p 5000:5000 %IMAGE_NAME%:%IMAGE_TAG%

endlocal

