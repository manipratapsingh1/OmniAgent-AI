# Production startup script for OmniAgent (Windows)
# Handles database migrations, verification, and service startup

param(
    [switch]$SkipVerification = $false
)

Write-Host "================================================"
Write_Host "OmniAgent Production Startup (Windows)"
Write-Host "================================================"
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "Error: pyproject.toml not found. Please run from backend directory." -ForegroundColor Red
    exit 1
}

# 1. Check environment variables
Write-Host "[1/5] Checking environment variables..." -ForegroundColor Yellow
if (-not $env:DATABASE_URL) {
    Write-Host "ERROR: DATABASE_URL not set. Check your .env file." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Environment variables OK" -ForegroundColor Green
Write-Host ""

# 2. Setup/activate virtual environment
Write-Host "[2/5] Setting up Python environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Virtual environment found, activating..."
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
}

# Install dependencies
Write-Host "Installing production dependencies..."
pip install -e ".[production]" -q
Write-Host "✓ Environment ready" -ForegroundColor Green
Write-Host ""

# 3. Run database migrations
Write-Host "[3/5] Running database migrations..." -ForegroundColor Yellow
alembic upgrade head
Write-Host "✓ Migrations complete" -ForegroundColor Green
Write-Host ""

# 4. Run verification (optional)
if (-not $SkipVerification) {
    Write-Host "[4/5] Running production verification..." -ForegroundColor Yellow
    python verify_production_ready.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Verification failed. Please fix issues before starting." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Production verification passed" -ForegroundColor Green
} else {
    Write-Host "[4/5] Skipping verification (use -SkipVerification:$false to enable)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Start the application
Write-Host "[5/5] Starting OmniAgent server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Server starting on http://0.0.0.0:8000"
Write-Host "API docs:     http://0.0.0.0:8000/docs"
Write-Host "ReDoc:        http://0.0.0.0:8000/redoc"
Write-Host ""
Write-Host "IMPORTANT: A background worker is required to process document uploads." -ForegroundColor Yellow
Write-Host "Please start the worker in a separate terminal: python start_rq_worker.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop"
Write-Host ""

# Start with Uvicorn (Windows-friendly)
Write-Host "Starting Uvicorn server..." -ForegroundColor Green
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# Alternative: Use Gunicorn via WSL if available
# Note: For production on Windows, consider using Docker or WSL2
