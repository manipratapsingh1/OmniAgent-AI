#!/usr/bin/env bash
# OmniAgent Frontend - Complete Setup Script
# Run this to install all dependencies and start the project

set -e

echo "🚀 OmniAgent Frontend - Complete Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend" || exit 1

echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo ""
echo "1. Make sure the backend is running on port 8000:"
echo "   cd backend"
echo "   pip install -e ."
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Start the frontend:"
echo "   npm run dev"
echo ""
echo "3. Open your browser to:"
echo "   http://localhost:5173"
echo ""
echo "✨ That's it! Your 3D frontend is ready to use."
echo ""
