# ==============================================================================
# Shree Shanishwara Swamy Temple Website — Font Download Script
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"

Write-Host "Downloading Google Noto Sans Kannada fonts..." -ForegroundColor Cyan
Set-Location $BackendDir
& $PythonExe app/utils/download_fonts.py
Write-Host "[✓] Font download complete!" -ForegroundColor Green
