# � Complete Setup Guide - OmniAgent AI 2.0

Production-ready AI system with authentication, database persistence, comprehensive logging, and unique study assistant.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Docker Setup](#quick-docker-setup)
3. [Local Development Setup](#local-development-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

- **Python 3.11+** - https://www.python.org/downloads/
- **Node.js 18+** - https://nodejs.org/
- **Git** - https://git-scm.com/
- **Docker & Docker Compose** (recommended) - https://www.docker.com/products/docker-desktop

### API Keys (Required)

1. **OpenAI API Key** (Required for LLM)
   - https://platform.openai.com/
   - Create account → API keys → Create new
   - Copy key: `sk_...`

2. **Google API Key** (Optional, for web search)
   - https://console.cloud.google.com/
   - Enable Custom Search API

3. **OpenWeather API** (Optional, for weather)
   - https://openweathermap.org/api
   - Sign up for free API key

### Verify Installation

```bash
python --version      # Should be 3.11+
node --version        # Should be 18+
npm --version         # Should be 9+
git --version         # Should be 2.30+
docker --version      # Should be 20.10+
docker-compose --version  # Should be 2.0+
```

---

## Quick Docker Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/your-repo/omniai.git
cd omniai
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
OPENAI_API_KEY=sk_your_key_here

# Optional
GOOGLE_API_KEY=your_key
OPENWEATHER_API_KEY=your_key

# Security
SECRET_KEY=super_secret_key_min_32_chars
```

### Step 3: Start Services

```bash
# Build images
docker-compose build

# Start all services (database, redis, backend, frontend)
docker-compose up -d

# Check status
docker-compose ps
```

### Step 4: Initialize Database

```bash
docker-compose exec backend python -c "from app.database import init_db; init_db()"
```

### Step 5: Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

**Test User** (pre-created in dev):
- Username: `admin`
- Password: `admin123`

### Docker Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Stop and remove data
docker-compose down -v

# Rebuild
docker-compose build --no-cache
```

---

## Local Development Setup

### Backend Setup

#### Step 1: Navigate to Backend

```bash
cd Backend
```

#### Step 2: Create Virtual Environment

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```cmd
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Initialize Database

```bash
# Using SQLite (default for local dev)
python -c "from app.database import init_db; init_db()"
```

#### Step 5: Run Backend

```bash
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

Access API docs: http://localhost:8000/api/docs

### Frontend Setup

#### Step 1: Navigate to Frontend

```bash
cd ../frontend
```

#### Step 2: Install Dependencies

```bash
npm install
```

#### Step 3: Create Environment File

```bash
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

#### Step 4: Start Development Server

```bash
npm start
```

Expected output:
```
Compiled successfully!

You can now view omniai in the browser.

Local:            http://localhost:3000
```

---

## Environment Configuration

### .env Template

Create a `.env` file in project root with these variables:

```env
# ============= DATABASE =============
DATABASE_URL=sqlite:///./omniai.db
# For PostgreSQL: postgresql+psycopg2://omniai:password@localhost:5432/omniai

# ============= API KEYS =============
OPENAI_API_KEY=sk_test_...
GOOGLE_API_KEY=
OPENWEATHER_API_KEY=

# ============= SECURITY =============
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============= SERVER =============
PORT=8000
WORKERS=4
LOG_LEVEL=INFO
ENVIRONMENT=development

# ============= FRONTEND =============
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ============= FEATURES =============
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_MEMORY=true
ENABLE_TOOLS=true

# ============= REDIS (Optional) =============
REDIS_URL=redis://localhost:6379/0

# ============= VECTOR DB =============
VECTOR_DB_TYPE=chroma
CHROMA_DB_PATH=./chroma_db
```

### Generate Secure Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Linux/macOS
openssl rand -hex 16

# Or use online: https://www.uuidgenerator.net/
```

#### 2.2 Configure Environment
```bash
# Copy example env
cp .env.example .env

# Edit .env with your keys
nano .env  # or use any editor
```

**Minimal .env** (for testing):
```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_database_url
REDIS_URL=redis://localhost:6379/0
```

### Phase 3: Docker Setup (Recommended)

#### 3.1 Start All Services
```bash
docker-compose up --build
```

Wait for all services to be healthy:
- ✅ Backend running on :8000
- ✅ Frontend running on :3000
- ✅ PostgreSQL running on :5432
- ✅ Redis running on :6379

#### 3.2 Verify Services
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000

# Check API docs
open http://localhost:8000/docs
```

### Phase 4: Manual Setup (Without Docker)

#### 4.1 Database Setup
```bash
# PostgreSQL
docker run \
  -e POSTGRES_PASSWORD=omniai123 \
  -e POSTGRES_DB=omniai \
  -d \
  -p 5432:5432 \
  --name omniai-db \
  postgres:15

# Redis
docker run \
  -d \
  -p 6379:6379 \
  --name omniai-redis \
  redis:alpine
```

#### 4.2 Backend Setup
```bash
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if any)
# python -m alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend ready at: http://localhost:8000

#### 4.3 Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend ready at: http://localhost:3000

### Phase 5: First Run

#### 5.1 Access Application
1. Open http://localhost:3000
2. You'll get an auto-generated User ID
3. Explore the dashboard

#### 5.2 Test Features

**Chat Interface**:
- Go to "💬 Chat"
- Type: "Hello, what can you do?"
- Verify: Response from AI

**Tasks**:
- Go to "✓ Tasks"
- Create a task
- Mark as completed

**Code Assistant**:
- Go to "💻 Code Assistant"
- Paste Python code
- Click "Analyze"
- See analysis results

**Knowledge Base**:
- Go to "📚 Knowledge"
- Upload a PDF
- Search its contents

#### 5.3 Configure Settings
- Go to "⚙ Settings"
- Set your preferences:
  - Tone (professional/casual/technical)
  - Expertise level
  - Preferred tools
  - Custom instructions

### Phase 6: Verify Installation

Run health check:
```bash
# Backend health
curl -s http://localhost:8000/health | python -m json.tool

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-...",
#   "features": [...]
# }
```

### Phase 7: Troubleshooting

#### Connection Issues

**"Cannot connect to backend"**
```bash
# Check if backend is running
curl http://localhost:8000/

# Check logs
docker-compose logs backend

# Restart
docker-compose restart backend
```

**"Database connection failed"**
```bash
# Check PostgreSQL
psql -h localhost -U omniai -d omniai -c "SELECT 1;"

# If fails, check docker
docker-compose ps
docker-compose logs database
```

#### API Key Issues

**"Invalid OpenAI API key"**
- Verify key in .env: `OPENAI_API_KEY=sk_...`
- Key must start with `sk_`
- Check quota at OpenAI dashboard
- Regenerate if expired

**"Search API not working"**
- Ensure GOOGLE_API_KEY is set
- Check Custom Search Engine ID
- Verify API is enabled in Google Cloud Console

#### Performance Issues

**"Slow responses"**
- Check machine specs (min 4GB RAM)
- Verify no other heavy services running
- Check network latency
- Look at docker resource limits

### Phase 8: Development Workflow

#### Backend Development
```bash
cd Backend

# Activate venv
source venv/bin/activate

# Make changes to Python files
# Server auto-reloads with --reload flag

# Run tests
pytest tests/

# Format code
black .

# Lint
pylint app/
```

#### Frontend Development
```bash
cd frontend

# Make changes to React files
# Browser auto-refreshes

# Run tests
npm test

# Build for production
npm run build

# Format code
npx prettier --write src/
```

### Phase 9: Production Deployment

#### Using Docker (Recommended)
```bash
# Build production images
docker-compose -f docker-compose.yml build

# Push to registry (optional)
docker tag omniai-backend:latest your-registry/omniai-backend:latest
docker push your-registry/omniai-backend:latest

# Deploy to server
docker-compose up -d
```

#### Manual Deployment
```bash
# Backend
cd Backend
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Frontend
cd frontend
npm run build
# Serve from nginx or static hosting
```

### Phase 10: Monitoring & Maintenance

#### Logs
```bash
# Docker
docker-compose logs -f backend

# Manually
tail -f /var/log/omniai/backend.log
```

#### Database Backups
```bash
# Backup PostgreSQL
docker-compose exec -T database pg_dump -U omniai omniai > backup.sql

# Restore
psql -U omniai -d omniai < backup.sql
```

---

## Database Setup

### PostgreSQL (Production Recommended)

#### Installation

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu)**:
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows**:
- Download: https://www.postgresql.org/download/windows/
- Run installer, follow prompts
- Note username (default: `postgres`) and password

#### Create Database & User

```bash
# Connect to PostgreSQL
psql -U postgres

-- In PostgreSQL shell:
CREATE USER omniai WITH PASSWORD 'secure_password';
CREATE DATABASE omniai OWNER omniai;
\q
```

#### Update Environment

```env
DATABASE_URL=postgresql+psycopg2://omniai:secure_password@localhost:5432/omniai
```

#### Initialize Schema

```bash
cd Backend
python -c "from app.database import init_db; init_db()"
```

### Redis (Caching)

#### Installation

**Docker** (easiest):
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Linux**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### Update Environment

```env
REDIS_URL=redis://localhost:6379/0
```

---

## Verification & Testing

### Health Checks

#### Backend

```bash
curl -s http://localhost:8000/api/health | python -m json.tool

# Expected:
# {
#   "status": "healthy",
#   "version": "2.0.0"
# }
```

#### Frontend

```bash
# Open in browser
open http://localhost:3000
```

### API Testing

#### 1. Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'
```

#### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'

# Save access_token from response
TOKEN="your_token_here"
```

#### 3. Send Chat Message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "use_memory": true,
    "use_rag": false
  }'
```

### Run Tests

```bash
# Backend
cd Backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# macOS/Linux
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### Database Connection Failed

```bash
# Check PostgreSQL
psql -U omniai -h localhost -d omniai

# Reset SQLite
rm Backend/omniai.db
python -c "from app.database import init_db; init_db()"
```

#### Module Not Found

```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall
pip install -r requirements.txt --force-reinstall
```

#### Frontend Not Loading

```bash
# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm start
```

#### CORS Errors

Update `.env`:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

---

## Production Deployment

### Heroku

```bash
# Create app
heroku create omniai-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Set environment variables
heroku config:set OPENAI_API_KEY=sk_...
heroku config:set ENVIRONMENT=production

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### AWS/Digital Ocean

```bash
# Build Docker image
docker build -t omniai .

# Push to registry
docker tag omniai:latest myregistry/omniai:latest
docker push myregistry/omniai:latest

# On server
docker pull myregistry/omniai:latest
docker run -p 80:8000 -p 3000:3000 myregistry/omniai:latest
```

### Production Checklist

- [ ] PostgreSQL database configured
- [ ] Redis cache enabled
- [ ] HTTPS/SSL enabled
- [ ] Strong SECRET_KEY set
- [ ] LOG_LEVEL=WARNING
- [ ] ENVIRONMENT=production
- [ ] Firewall configured
- [ ] Backups automated
- [ ] Monitoring setup
- [ ] CI/CD pipeline configured

---

## Next Steps

1. ✅ Setup complete
2. 📖 Read [README.md](./README.md)
3. 📚 Explore [API Docs](./docs/API.md)
4. 🧪 Run tests
5. 🚀 Deploy to production

**Questions?** Check [ARCHITECTURE.md](./ARCHITECTURE.md) or open an issue.
```bash
# Backup database
docker exec omniai-db pg_dump -U omniai omniai > backup.sql

# Restore database
docker exec -i omniai-db psql -U omniai omniai < backup.sql

# Backup Redis
docker exec omniai-redis redis-cli BGSAVE
docker cp omniai-redis:/data/dump.rdb ./redis-backup.rdb
```

#### Updates
```bash
# Pull latest changes
git pull

# Rebuild
docker-compose up --build

# Run migrations (if any)
# docker exec omniai-backend alembic upgrade head
```

---

## Quick Checklist ✅

- [ ] Install Docker
- [ ] Get API keys
- [ ] Clone repository
- [ ] Configure .env
- [ ] Run `docker-compose up --build`
- [ ] Verify http://localhost:3000 works
- [ ] Test chat feature
- [ ] Test task creation
- [ ] Read API docs at /docs
- [ ] Explore code at Backend/app/

**You're ready! 🚀**
