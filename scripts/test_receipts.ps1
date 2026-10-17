# ==============================================================================
# Shree Shanishwara Swamy Temple Website — PDF Receipt Regression Test Runner
# ==============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"
$PytestExe = Join-Path $BackendDir "venv\Scripts\pytest.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Running Receipt & Typography Test Suite" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location $BackendDir

Write-Host "[1/2] Running automated unit tests with pytest..." -ForegroundColor Cyan
& $PytestExe -v tests/test_receipt_generator.py

Write-Host ""
Write-Host "[2/2] Running visual receipt inspection generator..." -ForegroundColor Cyan
& $PythonExe tests/test_receipt_inspection.py

Write-Host ""
Write-Host "[OK] All receipt tests completed successfully!" -ForegroundColor Green

