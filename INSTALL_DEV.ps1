# Development Environment Setup Script for Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Polymarket Trading Bot" -ForegroundColor Cyan
Write-Host "Development Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Backend Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

cd backend

# Create virtual environment
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python packages..." -ForegroundColor Yellow
pip install -r requirements.txt

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python database.py

Write-Host "✓ Backend setup complete!" -ForegroundColor Green

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Frontend Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

cd frontend

# Install npm packages
Write-Host "Installing npm packages (this may take a few minutes)..." -ForegroundColor Yellow
npm install

Write-Host "✓ Frontend setup complete!" -ForegroundColor Green

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your Polymarket credentials" -ForegroundColor White
Write-Host "2. Run: .\START_DEV.ps1" -ForegroundColor White
Write-Host ""

# Create .env if not exists
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env template..." -ForegroundColor Yellow
    @"
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here
DATABASE_URL=sqlite:///./polymarket_bot.db
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:8080
"@ | Out-File -FilePath .env -Encoding UTF8
    
    Write-Host ""
    Write-Host "Opening .env file for editing..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    notepad .env
}

