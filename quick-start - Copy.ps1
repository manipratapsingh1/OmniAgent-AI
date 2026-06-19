#!/usr/bin/env pwsh
<#
.SYNOPSIS
    OmniAgent Quick Setup Script for Windows
.DESCRIPTION
    Sets up and starts the OmniAgent application with automatic service detection
.EXAMPLE
    .\quick-start.ps1
#>

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

$ErrorActionPreference = "Continue"

Write-Host "`n$('='*60)" -ForegroundColor Cyan
Write-Host "  OmniAgent Quick Start - Windows" -ForegroundColor Cyan
Write-Host "$('='*60)`n" -ForegroundColor Cyan

# Colors
$Success = 'Green'
$Error = 'Red'
$Warning = 'Yellow'
$Info = 'Cyan'

function Write-Success { Write-Host "  ✓ $args" -ForegroundColor $Success }
function Write-Error { Write-Host "  ✗ $args" -ForegroundColor $Error }
function Write-Warning { Write-Host "  ⚠ $args" -ForegroundColor $Warning }
function Write-Info { Write-Host "  ℹ $args" -ForegroundColor $Info }

# Step 1: Check Python
Write-Host "`n[1] Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found in PATH"
    Write-Info "Install Python from: https://www.python.org"
    exit 1
}

# Step 2: Check PostgreSQL
Write-Host "`n[2] Checking PostgreSQL..." -ForegroundColor Cyan
try {
    $pgVersion = psql --version 2>&1
    Write-Success "PostgreSQL found: $pgVersion"
    
    # Check if service is running
    $pgService = Get-Service PostgreSQL* -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }
    if ($pgService) {
        Write-Success "PostgreSQL service is running"
    } else {
        Write-Warning "PostgreSQL is installed but service not running"
        Write-Info "To start: Start-Service PostgreSQL15"
    }
} catch {
    Write-Error "PostgreSQL not found in PATH or not installed"
    Write-Info "Install from: https://www.postgresql.org/download/windows/"
    Write-Info "After installation, restart PowerShell and try again"
    exit 1
}

# Step 3: Check .env file
Write-Host "`n[3] Checking Configuration..." -ForegroundColor Cyan
if (Test-Path "omniagent-ai/backend/.env") {
    Write-Success ".env file found"
} else {
    Write-Error ".env file not found"
    exit 1
}

# Step 4: Virtual Environment
Write-Host "`n[4] Setting up Python Environment..." -ForegroundColor Cyan
if (Test-Path ".venv") {
    Write-Success "Virtual environment found"
} else {
    Write-Warning "Creating virtual environment..."
    python -m venv .venv
    Write-Success "Virtual environment created"
}

# Step 5: Activate venv
Write-Host "`n[5] Activating Virtual Environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1
Write-Success "Virtual environment activated"

# Step 6: Check services
Write-Host "`n[6] Checking Optional Services..." -ForegroundColor Cyan

# Check Redis
$redisCheck = $false
try {
    $redisTest = Invoke-WebRequest -Uri "http://localhost:6379" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Success "Redis is running (optional)"
    $redisCheck = $true
} catch {
    Write-Warning "Redis not running (optional service)"
}

# Check Ollama
$ollamaCheck = $false
try {
    $ollamaTest = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Success "Ollama is running (optional)"
    $ollamaCheck = $true
} catch {
    Write-Warning "Ollama not running (optional service)"
}

# Check Chroma
$chromaCheck = $false
try {
    $chromaTest = Invoke-WebRequest -Uri "http://localhost:8001/api/v2/tenants/default_tenant" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Success "Chroma is running (optional)"
    $chromaCheck = $true
} catch {
    Write-Warning "Chroma not running (optional service)"
}

# Step 7: Test Database
Write-Host "`n[7] Testing Database Connection..." -ForegroundColor Cyan
try {
    $testDb = psql -U postgres -d omniagent -c "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database connection successful"
    } else {
        Write-Warning "Database 'omniagent' not found or connection failed"
        Write-Info "Creating database..."
        psql -U postgres -c "CREATE DATABASE omniagent"
        Write-Success "Database created"
    }
} catch {
    Write-Warning "Could not test database: $_"
}

# Step 8: Display startup instructions
Write-Host "`n$('='*60)" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE" -ForegroundColor Green
Write-Host "$('='*60)`n" -ForegroundColor Cyan

Write-Host "NEXT STEPS:" -ForegroundColor Green

Write-Host "`n1️⃣  Terminal 1 - Start Backend:" -ForegroundColor Yellow
Write-Host "   cd omniagent-ai\backend"
Write-Host "   .venv\Scripts\activate"
Write-Host "   python init_and_run.py"
Write-Host "   (wait for 'Application startup complete')"
Write-Host "   Then: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "`n2️⃣  Terminal 2 - Start Frontend:" -ForegroundColor Yellow
Write-Host "   cd omniagent-ai\frontend"
Write-Host "   npm install  (if not done)"
Write-Host "   npm run dev"

Write-Host "`n3️⃣  Open in Browser:" -ForegroundColor Yellow
Write-Host "   http://localhost:5173"

Write-Host "`n4️⃣  Test System Health:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000/api/v1/health/readyz"

Write-Host "`n5️⃣  Check Status in App:" -ForegroundColor Yellow
Write-Host "   Look at bottom-left for System Status indicator`n"

# Summary
Write-Host "$('='*60)" -ForegroundColor Cyan
Write-Host "  SERVICE STATUS SUMMARY" -ForegroundColor Cyan
Write-Host "$('='*60)" -ForegroundColor Cyan

Write-Host "Required:" -ForegroundColor Yellow
Write-Host "  [$(if ($true) {'✓'} else {'✗'})] Python" -ForegroundColor Green
Write-Host "  [$(if ($true) {'✓'} else {'✗'})] PostgreSQL" -ForegroundColor Green
Write-Host "  [✓] Backend .env configured" -ForegroundColor Green

Write-Host "`nOptional:" -ForegroundColor Yellow
Write-Host "  [$(if ($redisCheck) {'✓'} else {'✗'})] Redis" 
Write-Host "  [$(if ($ollamaCheck) {'✓'} else {'✗'})] Ollama (LLM)" 
Write-Host "  [$(if ($chromaCheck) {'✓'} else {'✗'})] Chroma (Vector DB)" 

Write-Host "`n" -ForegroundColor Cyan
