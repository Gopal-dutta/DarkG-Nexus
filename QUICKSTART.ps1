# DarkG Nexus - Quick Start (Windows PowerShell)

Write-Host "🚀 DarkG Nexus - Quick Start" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Prerequisites:" -ForegroundColor Yellow
Write-Host "1. Python 3.11+ installed"
Write-Host "2. Node.js 14+ installed"
Write-Host "3. Ollama installed (https://ollama.ai)"
Write-Host "4. Llama-3 model (run: ollama pull llama3)"
Write-Host ""

Write-Host "Step 1: Start Ollama" -ForegroundColor Yellow
Write-Host "  Run in a new PowerShell terminal:"
Write-Host "  ollama serve"
Write-Host ""

Write-Host "Step 2: Start Backend" -ForegroundColor Yellow
Write-Host "  Run in a new PowerShell terminal:"
Write-Host "  cd D:\DarkG-Nexus\backend"
Write-Host "  venv\Scripts\activate"
Write-Host "  python -m uvicorn main:app --reload"
Write-Host "  (Backend will run on http://127.0.0.1:8000)"
Write-Host ""

Write-Host "Step 3: Start Desktop App" -ForegroundColor Yellow
Write-Host "  Run in a new PowerShell terminal:"
Write-Host "  cd D:\DarkG-Nexus\desktop-app"
Write-Host "  npm install  (first time only)"
Write-Host "  npm start"
Write-Host ""

Write-Host "All systems ready! Start using DarkG Nexus." -ForegroundColor Green
Write-Host ""
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
