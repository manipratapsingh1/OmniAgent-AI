# ⚡ Quick Reference Guide - OmniAgent AI

Quick lookup for common tasks, commands, and code snippets.

## 🚀 Quick Start

### Start Everything (Docker)
```bash
cd omniai
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Start Backend Only
```bash
cd Backend
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
uvicorn main:app --reload --port 8000
```

### Start Frontend Only
```bash
cd frontend
npm install
npm start  # http://localhost:3000
```

---

## 📋 Common Commands

### Database

```bash
# Reset database (local)
rm Backend/omniai.db
python -c "from app.database import init_db; init_db()"

# Backup PostgreSQL
docker-compose exec -T database pg_dump -U omniai omniai > backup.sql

# Restore PostgreSQL
psql -U omniai -d omniai < backup.sql

# Connect to PostgreSQL
psql -U omniai -h localhost -d omniai
```

### Docker

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down

# Clean everything
docker-compose down -v

# Build from scratch
docker-compose build --no-cache
docker-compose up -d
```

### Testing

```bash
# Backend tests
cd Backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Test specific endpoint
curl -X GET http://localhost:8000/api/health
```

---

## 🔑 API Quick Reference

### Authentication

**Register**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user",
    "email": "user@example.com",
    "password": "password",
    "full_name": "User Name"
  }'
```

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Save TOKEN from response
TOKEN="eyJ0..."
```

**Refresh Token**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
```

### Chat

**Send Message**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "use_memory": true,
    "use_rag": false,
    "streaming": false
  }'
```

**Stream Response**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### Documents

**Upload Document**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

**Search Documents**
```bash
curl -X POST "http://localhost:8000/api/search?query=python" \
  -H "Authorization: Bearer $TOKEN"
```

### Tasks

**Create Task**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn FastAPI",
    "description": "Complete tutorial",
    "priority": 4,
    "due_date": "2025-12-31T23:59:59"
  }'
```

**Get Tasks**
```bash
curl http://localhost:8000/api/tasks?status=pending \
  -H "Authorization: Bearer $TOKEN"
```

**Update Task**
```bash
curl -X PUT http://localhost:8000/api/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

**Delete Task**
```bash
curl -X DELETE http://localhost:8000/api/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
```

### System

**Health Check**
```bash
curl http://localhost:8000/api/health
```

**User Stats**
```bash
curl http://localhost:8000/api/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📁 File Structure Quick Map

```
Backend/
├── main.py                    → All API endpoints (30+)
├── requirements.txt           → Python dependencies
├── app/
│   ├── database.py            → SQLAlchemy models (User, Task, etc.)
│   ├── auth.py                → JWT tokens & password hashing
│   ├── logging_config.py      → Structured logging setup
│   ├── agents/
│   │   ├── nodes.py           → Planner, Executor, Verifier
│   │   ├── graph.py           → LangGraph workflow
│   │   └── state.py           → Agent state schema
│   ├── memory/
│   │   └── memory_manager.py  → Conversation history
│   ├── knowledge/
│   │   ├── rag_system.py      → RAG & embeddings
│   │   └── code_analyzer.py   → Code analysis
│   ├── tools/
│   │   └── tool_manager.py    → Tool integration
│   └── automation/
│       └── task_engine.py     → Task scheduling

frontend/
├── src/
│   ├── App.js                 → Main router
│   ├── config.js              → API configuration
│   ├── context/
│   │   └── AuthContext.js     → Auth state
│   ├── components/
│   │   ├── Navbar.js
│   │   └── Toast.js
│   ├── pages/
│   │   ├── Login.js           → Login form
│   │   ├── Register.js        → Registration form
│   │   ├── ChatInterface.js   → Chat page (pending)
│   │   ├── Dashboard.js       → Stats (pending)
│   │   ├── TaskManager.js     → Tasks (pending)
│   │   ├── KnowledgeBase.js   → Documents (pending)
│   │   ├── CodeAssistant.js   → Code analysis (pending)
│   │   ├── StudyAssistant.js  → UPSC study (complete)
│   │   └── Settings.js        → Preferences (pending)
│   └── styles/
│       ├── Auth.css           → Login/Register styles
│       └── ...                → Page-specific styles
├── Dockerfile
└── package.json

Root/
├── docker-compose.yml         → Service orchestration
├── .env.example               → Configuration template
├── README.md                  → Full documentation
├── SETUP.md                   → Installation guide
├── ARCHITECTURE.md            → System design
├── PROJECT_SUMMARY.md         → Feature checklist
└── IMPLEMENTATION_STATUS.md   → Current status
```

---

## 🐛 Troubleshooting Quick Fix

### Port in Use
```bash
# Find & kill process on port 8000
lsof -i :8000 && kill -9 <PID>

# Or restart Docker
docker-compose restart
```

### Database Error
```bash
# Reset SQLite
rm Backend/omniai.db && python -c "from app.database import init_db; init_db()"

# Check PostgreSQL
psql -U omniai -h localhost -d omniai
```

### Module Not Found
```bash
# Ensure venv activated
source venv/bin/activate

# Reinstall
pip install -r requirements.txt --force-reinstall
```

### Frontend Not Loading
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm start
```

### CORS Error
```env
# Update .env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 💡 Code Snippets

### Add New API Endpoint

```python
# Backend/main.py

@app.post("/api/myfeature")
@limiter.limit("50/minute")
async def my_feature(
    request: MyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint description"""
    api_logger.log_request(request.dict())
    
    try:
        # Your logic here
        result = await process_data(request.data, current_user, db)
        api_logger.log_response(result)
        return result
    except Exception as e:
        api_logger.log_error(str(e))
        raise HTTPException(status_code=500, detail="Error message")
```

### Add New Database Model

```python
# Backend/app/database.py

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="my_models")
```

### Update Authentication Check

```python
# In FastAPI endpoint
@app.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    # current_user is automatically validated
    return {"user_id": current_user.id}
```

### Log Operations

```python
from app.logging_config import api_logger, agent_logger, rag_logger

# API logging
api_logger.log_request({"path": "/api/chat", "method": "POST"})
api_logger.log_response({"status": 200})
api_logger.log_error("Database connection failed")

# Agent logging
agent_logger.log_planning({"steps": 5})
agent_logger.log_execution({"step": 1, "status": "running"})
agent_logger.log_verification({"score": 0.92})

# RAG logging
rag_logger.log_upload({"filename": "doc.pdf", "chunks": 10})
rag_logger.log_retrieval({"query": "python", "results": 5})
```

---

## 📊 Environment Variables

```bash
# Required for LLM
OPENAI_API_KEY=sk_...

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your_secret_key_here

# Database (SQLite default for dev)
DATABASE_URL=sqlite:///./omniai.db
# PostgreSQL: postgresql+psycopg2://omniai:password@localhost:5432/omniai

# Server
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Frontend
CORS_ORIGINS=http://localhost:3000

# Features
ENABLE_RAG=true
ENABLE_STREAMING=true
```

---

## 🔗 Useful Links

- **API Docs**: http://localhost:8000/api/docs
- **Admin UI**: http://localhost:8000/admin (if enabled)
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 📞 Quick Help

**Backend won't start?**
→ Check port 8000 is free, check .env file, check requirements.txt installed

**Frontend won't start?**
→ Check port 3000 is free, check `npm install`, check .env REACT_APP_API_URL

**Can't login?**
→ Make sure user registered first, check database initialized, check SECRET_KEY in .env

**Streaming not working?**
→ Check POST /api/chat/stream endpoint, browser support SSE, check ENABLE_STREAMING=true

**Database issues?**
→ Check PostgreSQL running, verify DATABASE_URL, check credentials in .env

---

**Need more help?** Check README.md, SETUP.md, or ARCHITECTURE.md