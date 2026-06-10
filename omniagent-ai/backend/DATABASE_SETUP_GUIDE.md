# OmniAgent Database Connection Troubleshooting Guide

## Overview

The database connection issues have been fixed. This guide will help you properly set up and start the application.

## Quick Start

### 1. Ensure PostgreSQL is Running

**Windows (using PostgreSQL installed locally):**
```powershell
# Start PostgreSQL service
net start PostgreSQL

# Or if installed with Homebrew or another package manager:
pg_ctl -D "C:\Program Files\PostgreSQL\data" start
```

**Linux/Mac:**
```bash
# Start PostgreSQL
brew services start postgresql
# or
sudo systemctl start postgresql
```

### 2. Create the Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE omniagent;

# Exit
\q
```

### 3. Verify .env Configuration

Edit `backend/.env` and ensure:
```env
# Database - must match your PostgreSQL setup
DATABASE_URL=postgresql://postgres:1234@localhost:5432/omniagent

# Redis
REDIS_URL=redis://localhost:6379

# Chroma (Vector DB)
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Ollama (LLM)
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Start the Backend

```bash
cd backend

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Run initialization script
python init_and_run.py

# If initialization passes, start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Issue: "connection refused"

**Cause:** PostgreSQL is not running

**Solution:**
```bash
# Check if PostgreSQL is running
# Windows: Services > PostgreSQL

# Start PostgreSQL manually
pg_ctl -D "C:\Program Files\PostgreSQL\data" start

# Or verify it's listening
netstat -an | grep 5432
```

### Issue: "authentication failed"

**Cause:** Wrong credentials in DATABASE_URL

**Solution:**
1. Verify PostgreSQL user/password
2. Update DATABASE_URL in .env
3. Format: `postgresql://username:password@localhost:5432/omniagent`

```bash
# Test connection manually
psql -U postgres -h localhost -d omniagent
```

### Issue: "database does not exist"

**Cause:** Database 'omniagent' not created

**Solution:**
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE omniagent;"

# Verify
psql -U postgres -d omniagent -c "SELECT 1;"
```

### Issue: "Database" status shows red X in UI

**Causes:**
- PostgreSQL not running
- Database not created
- Wrong credentials
- Wrong host/port

**Debug:**
```bash
# Run initialization script with verbose output
python init_and_run.py

# Check health endpoint
curl http://localhost:8000/api/v1/health/readyz

# Check logs for detailed errors
grep "database" app.log
```

## Database Initialization Process

The system now properly initializes the database:

1. **Validates Configuration**
   - Checks DATABASE_URL is set
   - Validates all required settings exist
   - Logs configuration details

2. **Tests Connection**
   - Attempts to connect to PostgreSQL
   - Returns helpful error messages if connection fails
   - Provides diagnostics for common issues

3. **Creates Tables**
   - Uses SQLModel/SQLAlchemy to create all tables
   - Respects foreign key constraints with CASCADE delete
   - Logs table creation status

4. **Validates External Services** (non-critical)
   - Checks Ollama availability (for LLM)
   - Checks Chroma availability (for vector DB)
   - Warnings only if unavailable

## Database Schema

### Key Tables

- **User**: User accounts and authentication
- **Conversation**: Chat conversations
- **Message**: Individual messages in conversations
- **Document**: Uploaded documents for RAG
- **DocumentChunk**: Text chunks from documents (with CASCADE delete)
- **MemoryEntry**: Short-term and long-term memory storage
- **AgentRun**: Agent execution traces
- **ToolCall**: Tool invocation records

### Important Constraints

- **CASCADE Delete**: Deleting a Document automatically removes all related DocumentChunks
- **Foreign Keys**: All relationships properly enforced
- **Indexes**: Optimized for common queries (user_id, conversation_id, etc.)

## Common Database Issues Fixed

### 1. DocumentChunk Orphaning
**Issue:** Deleting documents left orphaned chunks in the database
**Fix:** Added CASCADE delete to document_id foreign key

### 2. Session Management
**Issue:** Database connections not properly closed
**Fix:** Improved session handling in dependencies with proper cleanup

### 3. Health Check Blocking
**Issue:** Health checks were blocking the async event loop
**Fix:** Moved database checks to thread pool executor

### 4. Transaction Consistency
**Issue:** Multiple flush/commit calls causing transaction conflicts
**Fix:** Streamlined database operations to single commit per operation

### 5. Memory Service Cleanup
**Issue:** Cleanup method wasn't actually deleting expired entries
**Fix:** Implemented proper delete statement with transaction handling

## Environment Variables Reference

```env
# Required
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=postgresql://postgres:password@localhost:5432/omniagent

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# Vector Database (Chroma)
CHROMA_HOST=localhost
CHROMA_PORT=8001

# LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text

# Optional Settings
APP_DEBUG=True
APP_ENV=dev
CORS_ORIGINS=http://localhost:5173
```

## Verification Checklist

- [ ] PostgreSQL is running
- [ ] Database 'omniagent' exists
- [ ] .env file is correctly configured
- [ ] init_and_run.py completes successfully
- [ ] Health check endpoint returns `ready: true`
- [ ] Chat endpoint responds with database-backed memories
- [ ] File upload and retrieval works
- [ ] Document retrieval (RAG) returns results

## Getting Help

**Check logs:**
```bash
# View recent logs
tail -f app.log

# Filter for database errors
grep -i "database" app.log

# Filter for initialization
grep "init\|startup" app.log
```

**Run diagnostics:**
```python
from app.utils.db_diagnostics import diagnose_database_connection
result = diagnose_database_connection()
print(result)
```

**Health check endpoint:**
```bash
# Basic health
curl http://localhost:8000/api/v1/health/healthz

# Detailed readiness check
curl http://localhost:8000/api/v1/health/readyz
```
