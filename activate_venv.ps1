# Quick script to activate the virtual environment
# Usage: .\activate_venv.ps1

Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
.\envs\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated!" -ForegroundColor Green
Write-Host "📦 Python location: $((Get-Command python).Source)" -ForegroundColor Yellow
Write-Host ""
Write-Host "To run Acquill:" -ForegroundColor Cyan
Write-Host "  python cli.py chat" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate:" -ForegroundColor Cyan
Write-Host "  deactivate" -ForegroundColor White
