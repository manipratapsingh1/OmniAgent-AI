# Frontend build and deployment script (Windows)

Write-Host "================================================"
Write-Host "OmniAgent Frontend Build & Deployment (Windows)"
Write-Host "================================================"
Write-Host ""

# 1. Check prerequisites
Write-Host "[1/4] Checking prerequisites..." -ForegroundColor Yellow
try {
    $NodeVersion = node --version
    $NpmVersion = npm --version
    Write-Host "Node $NodeVersion"
    Write-Host "npm $NpmVersion"
    Write-Host "✓ Prerequisites OK" -ForegroundColor Green
} catch {
    Write-Host "Node.js or npm not found. Please install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Install dependencies
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
npm ci  # Use ci for reproducible builds
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# 3. Build
Write-Host "[3/4] Building for production..." -ForegroundColor Yellow
npm run build
$BuildSize = (Get-ChildItem -Path "dist" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Build size: ${BuildSize:N2} MB"
Write-Host "✓ Build complete" -ForegroundColor Green
Write-Host ""

# 4. Verification
Write-Host "[4/4] Verifying build..." -ForegroundColor Yellow
if (Test-Path "dist/index.html") {
    Write-Host "✓ index.html found" -ForegroundColor Green
} else {
    Write-Host "ERROR: index.html not found in dist/" -ForegroundColor Red
    exit 1
}

$FileCount = (Get-ChildItem -Path "dist" -Recurse -File | Measure-Object).Count
Write-Host "Built $FileCount files"
Write-Host "✓ Build verified" -ForegroundColor Green
Write-Host ""

Write-Host "================================================"
Write-Host "Build Complete!"
Write-Host "================================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Upload dist/ folder to your web server"
Write-Host "2. Configure nginx/apache to serve dist/index.html"
Write-Host "3. Set API proxy to backend: http://localhost:8000"
Write-Host ""
Write-Host "For Docker:"
Write-Host "  docker build -t omniagent-frontend . -f Dockerfile"
Write-Host ""
