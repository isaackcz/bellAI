@echo off
setlocal
cd /d %~dp0

set "IMAGE_NAME=pepperai"
set "IMAGE_TAG=%1"
if "%IMAGE_TAG%"=="" set "IMAGE_TAG=latest"

REM Optional: allow overriding container port via PORT env (defaults to 5000)
if "%PORT%"=="" set "PORT=5000"

REM Enable BuildKit for faster builds and better caching
set "DOCKER_BUILDKIT=1"

REM Check Docker availability
where docker >nul 2>&1 || (
    echo [ERROR] Docker is not installed or not in PATH. Install Docker Desktop and retry.
    exit /b 1
)

REM Ensure Docker daemon is running
docker info >nul 2>&1 || (
    echo [ERROR] Docker daemon is not running. Start Docker Desktop and retry.
    exit /b 1
)

REM Ensure Dockerfile exists
if not exist Dockerfile (
    echo [ERROR] Dockerfile not found in %cd%.
    exit /b 1
)

REM Support optional --no-cache as second arg
set "BUILD_EXTRA_OPTS="
if /I "%2"=="--no-cache" set "BUILD_EXTRA_OPTS=--no-cache"

REM Always build the image (replace existing tag if present)
echo [INFO] Building %IMAGE_NAME%:%IMAGE_TAG%...
    docker buildx version >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        docker buildx build --load -t %IMAGE_NAME%:%IMAGE_TAG% %BUILD_EXTRA_OPTS% -f Dockerfile . || (
            echo [ERROR] Docker buildx build failed.
            exit /b 1
        )
    ) else (
        docker build -t %IMAGE_NAME%:%IMAGE_TAG% %BUILD_EXTRA_OPTS% -f Dockerfile . || (
            echo [ERROR] Docker build failed.
            exit /b 1
        )
)

echo [INFO] Running container on port %PORT%...
docker run --rm -p %PORT%:%PORT% %IMAGE_NAME%:%IMAGE_TAG%
endlocal