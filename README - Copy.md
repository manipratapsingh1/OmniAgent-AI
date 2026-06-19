# 🚀 OmniAgent AI 2.0 - Production-Grade Multi-Agent System

> Advanced AI System with Authentication, RAG, Multi-Agent Intelligence, Task Automation, Study Assistant, and Modern UI/UX

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![React](https://img.shields.io/badge/react-18+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ What's New in v2.0

- ✅ **JWT Authentication** - Secure user login & registration
- ✅ **PostgreSQL/SQLite** - Persistent data storage
- ✅ **Comprehensive Logging** - Structured JSON logging for production
- ✅ **Rate Limiting** - DDoS protection & API throttling
- ✅ **Input Validation** - Pydantic models for all endpoints
- ✅ **Streaming Responses** - Token-by-token real-time chat
- ✅ **Modern Frontend** - ChatGPT-like UI with dark theme
- ✅ **AI Study Assistant** - UPSC/CDS exam prep module
- ✅ **File Upload** - Upload PDFs to RAG knowledge base
- ✅ **Production Ready** - Docker, monitoring, error handling

## 🌟 Core Features

### 🔐 Authentication & Security
- JWT-based token authentication
- Secure password hashing (bcrypt)
- Refresh token mechanism
- Rate limiting (DoS protection)
- Comprehensive audit logging

### 🤖 Multi-Agent Intelligence
- **Planner**: Breaks down complex problems
- **Executor**: Methodical step execution
- **Verifier**: Quality gates (0.0-1.0 scoring)
- LangGraph workflow
- Intelligent retry logic

### 📚 RAG Knowledge Base
- PDF/document upload
- Vector embeddings (OpenAI/Transformers)
- ChromaDB/FAISS storage
- Semantic search
- Document chunking & retrieval

### 💾 Database & Persistence
- PostgreSQL support
- SQLite for development
- User management
- Conversation history
- Document tracking
- API audit logs

### 🧠 Memory & Context
- Persistent conversation memory
- User preferences
- Smart context retrieval
- Personalized responses

### 📅 Task Automation
- CRUD operations
- Priority levels (1-5)
- Due dates & reminders
- Recurring tasks
- Status tracking

### 💻 Developer Assistant
- Code analysis & complexity
- Multi-language support
- Security analysis
- Refactoring suggestions

### 📖 AI Study Assistant
- UPSC/CDS exam prep
- Subject-wise materials
- Practice questions
- Mock tests
- Performance tracking

### 📊 Real-Time Features
- Server-Sent Events streaming
- WebSocket support
- Async endpoints
- Real-time chat

### 🛠️ Tool Integration
- Calculator, Web Search
- Weather API, Code Execution
- Unit Conversion
- API integration

## 🏗️ Architecture

```
OmniAgent AI/
├── Backend/
│   ├── app/
│   │   ├── agents/        # Multi-agent system
│   │   ├── memory/        # Long-term memory
│   │   ├── knowledge/     # RAG system
│   │   ├── tools/         # Tool integration
│   │   ├── automation/    # Task automation
│   │   ├── database.py    # ORM models
│   │   ├── auth.py        # Authentication
│   │   └── logging_config.py
│   ├── main.py            # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/         # React pages
│   │   ├── components/    # Reusable components
│   │   ├── context/       # State management
│   │   ├── config.js
│   │   └── App.js
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## 📋 Requirements

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ (optional)
- Redis (optional, for caching)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone & setup
git clone <repo-url>
cd OmniAgent
cp .env.example .env

# Add API keys
nano .env
# OPENAI_API_KEY=your_openai_api_key

# Start everything
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Docs: http://localhost:8000/api/docs
```

### Option 2: Local Development

#### Backend

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm start  # http://localhost:3000
```

## 🔑 Key Endpoints

### Authentication
```
POST   /api/auth/register      # User registration
POST   /api/auth/login         # User login
POST   /api/auth/refresh       # Refresh token
```

### Chat
```
POST   /api/chat               # Send message
POST   /api/chat/stream        # Stream response
GET    /api/conversations      # Get history
GET    /api/conversations/{id}/messages
```

### Knowledge Base
```
POST   /api/documents/upload   # Upload PDF
GET    /api/documents          # List documents
POST   /api/search             # Search documents
```

### Tasks
```
POST   /api/tasks              # Create task
GET    /api/tasks              # List tasks
PUT    /api/tasks/{id}         # Update task
DELETE /api/tasks/{id}         # Delete task
```

### Code Analysis
```
POST   /api/code/analyze       # Analyze code
```

### System
```
GET    /api/health             # Health check
GET    /api/stats              # User statistics
```

## 📚 Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./omniai.db
# PostgreSQL: postgresql+psycopg2://user:pass@host/db

# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=...
OPENWEATHER_API_KEY=...

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
PORT=8000
WORKERS=4
LOG_LEVEL=INFO
ENVIRONMENT=development

# CORS
CORS_ORIGINS=http://localhost:3000

# Features
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_MEMORY=true
```

## 📖 Usage Examples

### 1. Register & Login

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "password": "secure_password"
  }'
```

### 2. Chat with AI

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "message": "Explain machine learning",
    "use_memory": true,
    "use_rag": true
  }'
```

### 3. Upload Document

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

### 4. Create Task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn FastAPI",
    "description": "Complete FastAPI tutorial",
    "priority": 4,
    "due_date": "2025-12-31T23:59:59"
  }'
```

## 🧪 Testing

```bash
# Backend tests
cd Backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 📦 Deployment

### Heroku
```bash
heroku create omniai-app
heroku addons:create heroku-postgresql:standard-0
heroku config:set OPENAI_API_KEY=your_openai_api_key
git push heroku main
```

### Railway
```bash
railway init
railway add postgres
railway up
```

### AWS/Digital Ocean
```bash
docker build -t omniai .
docker tag omniai:latest your-registry/omniai
docker push your-registry/omniai
```

## 📊 Monitoring

```bash
# View logs
docker logs omniai_backend -f
docker logs omniai_frontend -f

# API metrics
curl http://localhost:8000/api/stats

# Database status
psql -U omniai -d omniai -c "SELECT * FROM users;"
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Error
```bash
# Reset database
rm omniai.db
python -c "from app.database import init_db; init_db()"
```

### Frontend Not Loading
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
npm start
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📚 Documentation

- [API Documentation](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Setup Guide](./SETUP.md)

## 📝 License

MIT License - See [LICENSE](./LICENSE) file

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [ChromaDB](https://trychroma.com/)
- [OpenAI](https://openai.com/)

## 📞 Support

- 📧 Email: support@omniai.dev
- 🐛 [GitHub Issues](https://github.com/omniai/issues)
- 💬 [Discussions](https://github.com/omniai/discussions)

## 🚀 Roadmap

- [ ] Mobile App (React Native)
- [ ] Voice Chat
- [ ] Advanced Analytics
- [ ] Custom LLM Support
- [ ] Multi-language UI
- [ ] Offline Mode
- [ ] Team Collaboration
- [ ] Advanced RAG Features

---

**Made with ❤️ by OmniAgent Team**

*Last Updated: May 2025*