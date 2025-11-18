# Activate Virtual Environment for Smart Attendance System
# Usage: . .\activate_venv.ps1

$VenvPath = Join-Path $PSScriptRoot "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $ActivateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $ActivateScript
    
    Write-Host "`n✓ Virtual environment activated!" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor Cyan
    Write-Host "  python -m streamlit run app.py" -ForegroundColor Yellow
    Write-Host "`nTo deactivate, run:" -ForegroundColor Cyan
    Write-Host "  deactivate" -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_venv.bat to create it first." -ForegroundColor Yellow
}
