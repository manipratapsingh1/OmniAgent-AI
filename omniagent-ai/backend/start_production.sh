#!/bin/bash
# Production startup script for OmniAgent
# Handles database migrations, verification, and service startup

set -e  # Exit on error

echo "================================================"
echo "OmniAgent Production Startup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run from backend directory.${NC}"
    exit 1
fi

# 1. Check environment variables
echo -e "${YELLOW}[1/5] Checking environment variables...${NC}"
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not set. Check your .env file.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment variables OK${NC}"
echo ""

# 2. Install dependencies if needed
echo -e "${YELLOW}[2/5] Installing dependencies...${NC}"
if [ -d ".venv" ]; then
    echo "Virtual environment found, activating..."
    source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null
else
    echo "Creating virtual environment..."
    python -m venv .venv
    source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null
fi

pip install -e ".[production]" -q
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# 3. Run database migrations
echo -e "${YELLOW}[3/5] Running database migrations...${NC}"
alembic upgrade head
echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# 4. Run verification
echo -e "${YELLOW}[4/5] Running production verification...${NC}"
python verify_production_ready.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Verification failed. Please fix issues before starting.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Production verification passed${NC}"
echo ""

# 5. Start the application
echo -e "${YELLOW}[5/5] Starting OmniAgent server...${NC}"
echo ""
echo "Server starting on http://0.0.0.0:8000"
echo "API docs:     http://0.0.0.0:8000/docs"
echo "ReDoc:        http://0.0.0.0:8000/redoc"
echo ""
echo "To stop, press Ctrl+C"
echo ""

# Determine number of workers (2 * CPU cores + 1)
WORKERS=$(($(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1) * 2 + 1))

# Start with Gunicorn for production
gunicorn \
    app.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
