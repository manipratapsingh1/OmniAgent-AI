#!/bin/bash
# Frontend build and deployment script

set -e

echo "================================================"
echo "OmniAgent Frontend Build & Deployment"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Check prerequisites
echo -e "${YELLOW}[1/4] Checking prerequisites...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is not installed${NC}"
    exit 1
fi
echo "Node $(node --version)"
echo "npm $(npm --version)"
echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# 2. Install dependencies
echo -e "${YELLOW}[2/4] Installing dependencies...${NC}"
npm ci  # Use ci instead of install for reproducible builds
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# 3. Build
echo -e "${YELLOW}[3/4] Building for production...${NC}"
npm run build
BUILD_SIZE=$(du -sh dist | cut -f1)
echo "Build size: $BUILD_SIZE"
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# 4. Verification
echo -e "${YELLOW}[4/4] Verifying build...${NC}"
if [ -f "dist/index.html" ]; then
    echo -e "${GREEN}✓ index.html found${NC}"
else
    echo -e "${RED}ERROR: index.html not found in dist/${NC}"
    exit 1
fi

FILE_COUNT=$(find dist -type f | wc -l)
echo "Built $FILE_COUNT files"
echo -e "${GREEN}✓ Build verified${NC}"
echo ""

echo "================================================"
echo "Build Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Upload dist/ folder to your web server"
echo "2. Configure nginx/apache to serve dist/index.html"
echo "3. Set API proxy to backend: http://localhost:8000"
echo ""
echo "For Docker:"
echo "  docker build -t omniagent-frontend . -f Dockerfile"
echo ""
