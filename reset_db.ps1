# Quick Reset Database Only
# Usage: .\reset_db.ps1

Write-Host ""
Write-Host "RESET DATABASE" -ForegroundColor Yellow
Write-Host ("=" * 50) -ForegroundColor Cyan

if (Test-Path "data\dedup_store.db") {
    $size = (Get-Item "data\dedup_store.db").Length
    $sizeKB = [math]::Round($size / 1KB, 2)
    
    Write-Host "Current database: $sizeKB KB" -ForegroundColor Gray
    
    Remove-Item "data\dedup_store.db" -Force
    
    Write-Host "Database deleted successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Restart server untuk create database baru" -ForegroundColor White
    Write-Host "   2. Atau run: .\reset_and_start.ps1" -ForegroundColor White
} else {
    Write-Host "Database not found" -ForegroundColor Yellow
    Write-Host "   Path: data\dedup_store.db" -ForegroundColor Gray
    Write-Host "   Database akan dibuat otomatis saat server start" -ForegroundColor White
}

Write-Host ("=" * 50) -ForegroundColor Cyan
Write-Host ""
