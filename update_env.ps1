# PepperAI - Update .env File Script
# This script updates the .env file with secure configuration

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PepperAI Environment Configuration Updater" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Backup existing .env
if (Test-Path .env) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item .env ".env.backup.$timestamp"
    Write-Host "[OK] Backed up existing .env to .env.backup.$timestamp" -ForegroundColor Green
}

# New .env content with secure configuration
$envContent = @"
# PepperAI Environment Configuration

# Flask Secret Key - Secure production key (DO NOT SHARE)
SECRET_KEY=902d0860f6f01b05a174a49a7ca5dcc54dc9420c845717d4daeeaa10fbfe9372

# Flask Environment
FLASK_ENV=production
FLASK_DEBUG=0

# Database Configuration
DATABASE_URL=sqlite:///instance/pepperai.db

# Upload and Results Settings
UPLOAD_FOLDER=uploads
RESULTS_FOLDER=results
MAX_CONTENT_LENGTH=16777216

# Redis Configuration (used by Docker Compose)
REDIS_URL=redis://redis:6379/0

# Application Settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
"@

# Write new .env file
$envContent | Out-File -FilePath .env -Encoding utf8 -NoNewline

Write-Host "[OK] Created new .env file with secure configuration" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Configuration Summary:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[SECRET_KEY]           Secure 64-character key" -ForegroundColor Green
Write-Host "[FLASK_ENV]            production" -ForegroundColor Green
Write-Host "[DATABASE_URL]         sqlite:///instance/pepperai.db" -ForegroundColor Green
Write-Host "[UPLOAD_FOLDER]        uploads" -ForegroundColor Green
Write-Host "[RESULTS_FOLDER]       results" -ForegroundColor Green
Write-Host "[MAX_CONTENT_LENGTH]   16MB" -ForegroundColor Green
Write-Host "[REDIS_URL]            redis://redis:6379/0" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Environment file updated successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test configuration: python test_env_config.py" -ForegroundColor White
Write-Host "2. Start Docker: docker-start.bat" -ForegroundColor White
Write-Host "3. Check health: curl http://localhost/health" -ForegroundColor White
Write-Host ""
