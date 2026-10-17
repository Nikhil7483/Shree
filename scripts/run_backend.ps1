# ==============================================================================
# Shree Shanishwara Swamy Temple Website — Backend Server Launcher
# ==============================================================================
param (
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$Reload = $true
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Shree Shanishwara Swamy Temple — FastAPI Backend Server" -ForegroundColor Yellow
Write-Host "  ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at '$PythonExe'. Please run setup first."
}

# Verify local MongoDB connectivity
$MongoRunning = Get-Process -Name "mongod" -ErrorAction SilentlyContinue
if ($MongoRunning) {
    Write-Host "[✓] MongoDB service is running (PID: $($MongoRunning.Id))" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: 'mongod' process not detected. Ensure MongoDB is running on port 27017." -ForegroundColor Yellow
}

Set-Location $BackendDir

$ReloadFlag = if ($Reload) { "--reload" } else { "" }
Write-Host "[✓] Launching Uvicorn server on http://$BindHost`:$Port..." -ForegroundColor Green
& $PythonExe -m uvicorn app.main:app --host $BindHost --port $Port $ReloadFlag
