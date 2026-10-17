# ==============================================================================
# Shree Shanishwara Swamy Temple Website — Full-Stack Dev Environment Launcher
# ==============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"
$MongoBin = Join-Path $BackendDir "mongodb\bin\mongod.exe"
$MongoData = Join-Path $BackendDir "mongodb\data"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Shree Shanishwara Swamy Temple — Dev Environment Launcher" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check or launch MongoDB
$MongoRunning = Get-Process -Name "mongod" -ErrorAction SilentlyContinue
if (-not $MongoRunning) {
    if (Test-Path $MongoBin) {
        Write-Host "[+] Starting embedded MongoDB instance..." -ForegroundColor Cyan
        if (-not (Test-Path $MongoData)) { New-Item -ItemType Directory -Force -Path $MongoData | Out-Null }
        Start-Process -FilePath $MongoBin -ArgumentList "--dbpath `"$MongoData`"" -WindowStyle Hidden
        Start-Sleep -Seconds 2
        Write-Host "[✓] MongoDB started successfully." -ForegroundColor Green
    } else {
        Write-Host "[!] Embedded MongoDB not found at '$MongoBin'. Ensure local MongoDB is active on port 27017." -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] MongoDB active (PID: $($MongoRunning.Id))" -ForegroundColor Green
}

# 2. Start Backend with hot reload
Set-Location $BackendDir
Write-Host "[✓] Starting Backend server at http://127.0.0.1:8000..." -ForegroundColor Green
& $PythonExe -m uvicorn app.main:app --reload --port 8000
