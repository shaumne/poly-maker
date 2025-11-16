# ============================================================
# 🎯 Polymarket Trading Bot - Enhanced Development Startup
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   🎯 POLYMARKET TRADING BOT - BAŞLATILIYOR" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check .env file
$envFile = ".\backend\.env"
$rootEnvFile = ".\.env"

if (-Not (Test-Path $envFile) -and -Not (Test-Path $rootEnvFile)) {
    Write-Host "⚠️  .env dosyası bulunamadı!" -ForegroundColor Yellow
    Write-Host "   .env.example'dan oluşturuluyor..." -ForegroundColor Gray
    
    if (Test-Path ".\.env.example") {
        Copy-Item ".\.env.example" $rootEnvFile
        Write-Host "✅ .env dosyası oluşturuldu" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔑 Lütfen .env dosyasını düzenleyin:" -ForegroundColor Yellow
        Write-Host "   - PK: Polymarket private key" -ForegroundColor Gray
        Write-Host "   - BROWSER_ADDRESS: Wallet adresi" -ForegroundColor Gray
        Write-Host "   - DRY_RUN: true (test) veya false (canlı)" -ForegroundColor Gray
        Write-Host ""
        
        notepad $rootEnvFile
        Read-Host "Düzenlemeden sonra Enter'a basın"
    } else {
        Write-Host "❌ .env.example bulunamadı!" -ForegroundColor Red
        exit 1
    }
}

# Check Python virtual environment
$venvPath = ".\backend\venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "📦 Python virtual environment oluşturuluyor..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "✅ Virtual environment oluşturuldu" -ForegroundColor Green
}

# Check backend dependencies
$requirementsFile = ".\backend\requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "📦 Backend dependencies kontrol ediliyor..." -ForegroundColor Yellow
    & "$venvPath\Scripts\python.exe" -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📥 Backend dependencies yükleniyor..." -ForegroundColor Yellow
        & "$venvPath\Scripts\pip.exe" install -r $requirementsFile
        Write-Host "✅ Backend dependencies yüklendi" -ForegroundColor Green
    } else {
        Write-Host "✅ Backend dependencies hazır" -ForegroundColor Green
    }
}

# Check frontend dependencies
$frontendPath = ".\frontend"
if (Test-Path "$frontendPath\package.json") {
    if (-Not (Test-Path "$frontendPath\node_modules")) {
        Write-Host "📦 Frontend dependencies yükleniyor..." -ForegroundColor Yellow
        Set-Location $frontendPath
        npm install
        Set-Location ..
        Write-Host "✅ Frontend dependencies yüklendi" -ForegroundColor Green
    } else {
        Write-Host "✅ Frontend dependencies hazır" -ForegroundColor Green
    }
}

# Initialize database
Write-Host "🗄️  Database kontrol ediliyor..." -ForegroundColor Yellow
Set-Location .\backend
& ".\venv\Scripts\python.exe" database.py
Set-Location ..
Write-Host "✅ Database hazır" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   🚀 SERVİSLER BAŞLATILIYOR" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Start Backend
Write-Host "📡 Backend başlatılıyor..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '   📡 BACKEND API SERVER' -ForegroundColor White
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''
    cd '$PSScriptRoot\backend'
    .\venv\Scripts\Activate.ps1
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
"@

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🌐 Frontend başlatılıyor..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '   🌐 FRONTEND WEB UI' -ForegroundColor White
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''
    cd '$PSScriptRoot\frontend'
    npm run serve
"@

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   ✅ HER İKİ SERVİS DE BAŞLATILDI!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend API:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host "📖 API Docs:     " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "🌐 Frontend UI:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8080" -ForegroundColor Yellow
Write-Host ""

# Check DRY_RUN status
$dryRunStatus = "UNKNOWN"
if (Test-Path $rootEnvFile) {
    $envContent = Get-Content $rootEnvFile -Raw
    if ($envContent -match "DRY_RUN\s*=\s*true") {
        Write-Host "🔵 MOD: " -NoNewline -ForegroundColor White
        Write-Host "DRY RUN (Simülasyon - Güvenli)" -ForegroundColor Cyan
        Write-Host "   → Gerçek order göndermez, test amaçlıdır" -ForegroundColor Gray
    } elseif ($envContent -match "DRY_RUN\s*=\s*false") {
        Write-Host "🔴 MOD: " -NoNewline -ForegroundColor White
        Write-Host "LIVE TRADING (Gerçek Para - DİKKAT!)" -ForegroundColor Red
        Write-Host "   → Gerçek order gönderir, para riski var!" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  DRY_RUN ayarı bulunamadı (.env)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env dosyası bulunamadı!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Gray
Write-Host "   📖 Kullanım Kılavuzu: KULLANIM_KILAVUZU.md" -ForegroundColor Gray
Write-Host "   🆘 Sorun mu var?: QUICKSTART.md" -ForegroundColor Gray
Write-Host "   🚀 Production: DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""
Write-Host "İpucu: Servisleri kapatmak için açılan PowerShell" -ForegroundColor Yellow
Write-Host "         pencerelerini kapatın veya Ctrl+C yapın" -ForegroundColor Yellow
Write-Host ""
Write-Host "Devam etmek için Enter'a basın..." -ForegroundColor Gray
Read-Host

