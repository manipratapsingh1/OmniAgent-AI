# 🤖 OmniAgent - Production-Ready AI Agent Platform

**A full-stack, enterprise-grade AI platform with Multi-Agent Orchestration, RAG, Memory Management, and Real-time Task Automation.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com)
[![React 18+](https://img.shields.io/badge/React-18%2B-blue)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Quick Start

### System Requirements
- **Python 3.10+**
- **PostgreSQL 14+** ⚠️ **REQUIRED** - Install from https://www.postgresql.org/download/
- **Node.js 18+**
- Windows, Mac, or Linux

### 30-Second Setup

```bash
# 1. Windows Users: Follow this first (CRITICAL)
# https://www.postgresql.org/download/windows/
# Install PostgreSQL and create 'omniagent' database

# 2. Backend (Terminal 1)
cd omniagent-ai/backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
python init_and_run.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (Terminal 2)
cd omniagent-ai/frontend
npm install
npm run dev

# 4. Open browser
# http://localhost:5173
```

---

## 📋 Complete Guides

| Document | Purpose |
|----------|---------|
| **[COMPLETE_SETUP_GUIDE.md](./COMPLETE_SETUP_GUIDE.md)** | **START HERE** - Full setup with troubleshooting |
| **[WINDOWS_SETUP_GUIDE.md](./WINDOWS_SETUP_GUIDE.md)** | Windows-specific installation & setup |
| **[omniagent-ai/README_FRONTEND.md](./omniagent-ai/README_FRONTEND.md)** | Frontend architecture & development |
| **[omniagent-ai/backend/DATABASE_SETUP_GUIDE.md](./omniagent-ai/backend/DATABASE_SETUP_GUIDE.md)** | Database configuration details |
| **[omniagent-ai/PRODUCTION_DEPLOYMENT.md](./omniagent-ai/PRODUCTION_DEPLOYMENT.md)** | Production deployment guide |

---

## ✨ Features

### 🧠 Multi-Agent Orchestration
- **Router Agent** - Intelligent request routing
- **Research Agent** - Web search & information gathering
- **Memory Agent** - Long-term memory management
- **Planner Agent** - Task planning & execution
- **Critic Agent** - Response evaluation & refinement
- **Task Executor** - Asynchronous task handling

### 📚 Advanced RAG (Retrieval-Augmented Generation)
- Multi-format document support (PDF, TXT, Markdown)
- Intelligent chunking with overlap
- Vector similarity search
- Semantic document retrieval
- Chroma integration for vector storage

### 💾 Memory Management
- Short-term conversation memory
- Long-term persistent storage
- Memory cleanup & optimization
- User-scoped memory isolation

### 🔐 Enterprise Security
- JWT-based authentication
- Role-based access control (Admin/User)
- Encrypted API keys
- Rate limiting & DDoS protection
- CORS configuration

### 📊 Real-Time Capabilities
- WebSocket support for live updates
- Asynchronous chat streaming
- Background job processing
- Real-time notifications

### 🎨 Modern Frontend
- React 18 with TypeScript
- 3D animated UI components
- Dark theme with gradient design
- Real-time system status monitoring
- Responsive mobile design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│        OmniAgent Platform Architecture           │
├─────────────────────────────────────────────────┤
│                                                 │
│  Frontend Layer (React/Vite)                   │
│  ├─ Components: Chat, Documents, Tasks, Admin  │
│  ├─ 3D Canvas & Animations                     │
│  └─ Real-time Status Monitoring                │
│                                 ↓               │
│  API Gateway (FastAPI)                         │
│  ├─ REST Endpoints                             │
│  ├─ WebSocket Connections                      │
│  └─ Rate Limiting & Auth                       │
│                                 ↓               │
│  Core Services Layer                           │
│  ├─ Multi-Agent System                         │
│  │  ├─ Router → Research → Memory              │
│  │  ├─ Planner → Critic → Executor             │
│  │  └─ Summarizer & Tools                      │
│  ├─ RAG Pipeline                               │
│  │  ├─ Document Ingestion                      │
│  │  ├─ Vector Embeddings                       │
│  │  └─ Semantic Search                         │
│  ├─ Chat Management                            │
│  └─ Task Management                            │
│                                 ↓               │
│  Data Layer                                    │
│  ├─ PostgreSQL (Primary DB)                    │
│  ├─ Redis (Caching & Sessions)                 │
│  ├─ Chroma (Vector DB)                         │
│  └─ Ollama (Local LLM)                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend
- **FastAPI** - High-performance async framework
- **SQLModel** - SQLAlchemy + Pydantic ORM
- **LangChain** - LLM orchestration
- **Chroma** - Vector database
- **Redis** - Caching & message queue
- **Ollama** - Local LLM support

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Lightning-fast bundler
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **Three.js** - 3D graphics
- **Framer Motion** - Animations

### Infrastructure
- **PostgreSQL** - Relational database
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## 📂 Project Structure

```
omniagent-ai-ar/
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── agents/       # Multi-agent system
│   │   ├── models/       # SQLModel definitions
│   │   ├── services/     # Business logic
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── rag/          # RAG pipeline
│   │   ├── db/           # Database layer
│   │   └── utils/        # Utilities
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   ├── .env              # Configuration
│   ├── init_and_run.py   # Initialization script
│   └── pyproject.toml    # Dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── store/        # Zustand stores
│   │   └── utils/        # Utilities
│   ├── vite.config.ts    # Vite configuration
│   ├── package.json      # Dependencies
│   └── index.html        # Entry HTML
│
├── docker/
│   ├── docker-compose.yml
│   └── nginx.conf
│
└── docs/
    ├── API.md            # API documentation
    ├── ARCHITECTURE.md   # System architecture
    └── ROADMAP.md        # Feature roadmap
```

---

## 🚦 Current Status

### ✅ Completed
- [x] Multi-agent orchestration system
- [x] RAG pipeline with document processing
- [x] User authentication & authorization
- [x] Chat conversation management
- [x] Real-time notifications
- [x] Frontend UI with 3D animations
- [x] Docker containerization
- [x] Database migrations
- [x] Production-ready API

### 🔧 Configuration Fixed
- [x] Database connection (.env created)
- [x] Health check endpoint (syntax fixed)
- [x] Document upload tracking
- [x] System status monitoring

### 📋 Guides Available
- [x] Windows setup guide
- [x] Complete setup guide with troubleshooting
- [x] Quick start PowerShell script
- [x] Database setup guide

---

## 🐛 Known Issues & Solutions

### Database Not Connected
**Status:** ✅ **FIXED**
- **Issue:** Database showed as disconnected
- **Cause:** Missing `.env` file with DATABASE_URL
- **Solution:** `.env` file created with PostgreSQL configuration
- **Action:** Install PostgreSQL and create database

### Document Upload Status
**Status:** ✅ **FIXED**
- **Issue:** Upload showed success but status was failed
- **Cause:** Database not storing status
- **Solution:** Database connection fixed, status now properly tracked

### Health Check Errors
**Status:** ✅ **FIXED**
- **Issue:** Health endpoint had syntax errors
- **Cause:** Orphaned code in health.py
- **Solution:** Code cleaned up

---

## 📖 Usage Examples

### 1. Create a Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat"}'
```

### 2. Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

### 3. Search Documents

```bash
curl -X GET "http://localhost:8000/api/v1/documents/rag-search?q=search+term&k=5" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "content": "Hello, AI!"}'
```

---

## 🔐 Environment Configuration

### Required Variables (in `backend/.env`)
```env
# Application
SECRET_KEY=your-secret-key-min-32-chars

# Database
DATABASE_URL=your_database_url

# Optional Services
REDIS_URL=redis://localhost:6379
CHROMA_HOST=localhost
CHROMA_PORT=8001
OLLAMA_BASE_URL=http://localhost:11434
```

See [WINDOWS_SETUP_GUIDE.md](./WINDOWS_SETUP_GUIDE.md) for detailed configuration.

---

## 📦 Installation & Deployment

### Local Development
See [COMPLETE_SETUP_GUIDE.md](./COMPLETE_SETUP_GUIDE.md)

### Production Deployment
See [omniagent-ai/PRODUCTION_DEPLOYMENT.md](./omniagent-ai/PRODUCTION_DEPLOYMENT.md)

### Docker
```bash
cd docker
docker-compose up -d
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
npm run e2e
```

---

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Architecture:** See `docs/ARCHITECTURE.md`
- **API Reference:** See `docs/API.md`

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🆘 Support & Troubleshooting

### Getting Help
1. **Read the Guides First:**
   - [COMPLETE_SETUP_GUIDE.md](./COMPLETE_SETUP_GUIDE.md) - Start here
   - [WINDOWS_SETUP_GUIDE.md](./WINDOWS_SETUP_GUIDE.md) - Windows users
   - [Database Setup](./omniagent-ai/backend/DATABASE_SETUP_GUIDE.md) - Database issues

2. **Check Logs:**
   - Backend: Terminal where `uvicorn` is running
   - Frontend: Browser console (F12)
   - Database: PostgreSQL logs

3. **Test Health:**
   - http://localhost:8000/api/v1/health/readyz
   - System Status in app (bottom-left)

4. **Common Issues:**
   - PostgreSQL not installed → Install from postgresql.org
   - Port in use → Change port in .env
   - Module errors → `pip install -r requirements.txt`

---

## 🎯 Roadmap

- [ ] Advanced Analytics Dashboard
- [ ] Multi-language Support
- [ ] Mobile App
- [ ] Voice Integration
- [ ] Advanced Prompt Engineering
- [ ] Custom Model Training
- [ ] Enterprise SSO
- [ ] API Rate Limiting Dashboard

---

## ⭐ Star History

If you find this project helpful, please consider starring it! ⭐

---

**Version:** 2.0.0  
**Last Updated:** May 21, 2026  
**Status:** ✅ Ready for Production Use  
**PostgreSQL:** ⚠️ Required - Please Install First
