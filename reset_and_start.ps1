# Quick Reset Database Script
# Usage: .\reset_and_start.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  DATABASE RESET & SERVER RESTART" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if database exists
if (Test-Path "data\dedup_store.db") {
    Write-Host "[1/3] " -NoNewline -ForegroundColor Green
    Write-Host "Deleting old database..."
    Remove-Item "data\dedup_store.db" -Force
    Write-Host "      ✅ Database deleted!" -ForegroundColor Green
} else {
    Write-Host "[1/3] " -NoNewline -ForegroundColor Yellow
    Write-Host "Database not found (will be created on startup)"
}

Write-Host ""

# Step 2: Confirm
Write-Host "[2/3] " -NoNewline -ForegroundColor Green
Write-Host "Database reset complete!"

Write-Host ""

# Step 3: Start server
Write-Host "[3/3] " -NoNewline -ForegroundColor Green
Write-Host "Starting server with fresh database..."
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Start uvicorn server
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080
