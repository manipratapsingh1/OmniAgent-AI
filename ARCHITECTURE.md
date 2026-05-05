# 🏗️ Architecture Documentation - OmniAgent AI

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React Frontend (3000)                                  │  │
│  │  • Dashboard • Chat • Tasks • Knowledge • Code • Settings│  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI (8000)                                         │  │
│  │  • REST Endpoints • WebSocket • CORS • Auth            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────────┐ ┌──────────┐ ┌────────────┐
    │  Agents     │ │  Memory  │ │ Knowledge  │
    │  System     │ │  System  │ │  Base      │
    └─────────────┘ └──────────┘ └────────────┘
         │               │              │
         ▼               ▼              ▼
    ┌─────────────────────────────────────────────┐
    │  PostgreSQL (5432) - Persistent Storage    │
    └─────────────────────────────────────────────┘
         │               │
         ▼               ▼
    ┌─────────────────────────────────────────────┐
    │  Redis (6379) - Cache & Sessions           │
    └─────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Frontend Layer (React)

**Location**: `frontend/src/`

**Components**:
```
src/
├── App.js                    # Main router & layout
├── pages/
│   ├── Dashboard.js         # Stats & overview
│   ├── ChatInterface.js      # Main chat UI
│   ├── TaskManager.js        # Task CRUD
│   ├── KnowledgeBase.js      # Document upload & search
│   ├── CodeAssistant.js      # Code analysis
│   └── Settings.js           # User preferences
├── components/
│   └── Navbar.js             # Navigation
└── styles/
    ├── *.css                 # Component styles
    └── index.css             # Global styles
```

**Key Libraries**:
- `react-router-dom`: Client-side routing
- `axios`: HTTP client (can use fetch)
- `ws`: WebSocket support

### 2. API Gateway (FastAPI)

**Location**: `Backend/main.py`

**Endpoints**:
```python
# Chat
POST   /chat                          # Main chat endpoint
WS     /ws/chat/{conversation_id}     # Streaming

# Knowledge
POST   /upload-document               # Upload PDF
GET    /knowledge-base/{user_id}      # List docs
POST   /search-knowledge              # Search

# Tasks
POST   /tasks/{user_id}               # Create
GET    /tasks/{user_id}               # List
PUT    /tasks/{task_id}               # Update
DELETE /tasks/{task_id}               # Delete

# Code
POST   /analyze-code                  # Analysis
POST   /explain-code                  # Explanation

# Memory
POST   /preferences/{user_id}         # Save prefs
GET    /preferences/{user_id}         # Get prefs

# Tools
POST   /calculate                     # Calculator
GET    /search                        # Web search
GET    /weather/{location}            # Weather
```

### 3. Agent System (LangGraph)

**Location**: `Backend/app/agents/`

**Architecture**:
```
AgentState
    ↓
[Planner Node] → Creates plan (5-7 steps)
    ↓
[Executor Node] → Executes current step
    ↓
[Verifier Node] → Scores 0.0-1.0
    ↓
[Router Logic]
    ├─ Score ≥ 0.85 + more steps? → Next step
    ├─ Score < 0.85? → Retry
    └─ No more steps? → END
```

**Flow**:
```python
def planner(state) → breaks problem into steps
def executor(state) → solves each step using LLM
def verifier(state) → quality gates solution
def router(state) → decides next action
```

**Key Features**:
- Deterministic routing
- Append-only audit trail
- Quality verification loop
- Fallback handling

### 4. Memory System

**Location**: `Backend/app/memory/memory_manager.py`

**Tables**:
```sql
-- Conversation history
conversation_memory (
    id STRING PRIMARY KEY,
    user_id STRING,
    content JSON,
    created_at TIMESTAMP
)

-- User preferences
user_preferences (
    id STRING PRIMARY KEY,
    user_id STRING UNIQUE,
    preferences JSON,
    updated_at TIMESTAMP
)

-- Knowledge base
knowledge_base (
    id STRING PRIMARY KEY,
    user_id STRING,
    title STRING,
    content TEXT,
    metadata JSON,
    created_at TIMESTAMP
)
```

**Operations**:
- `save_conversation()` - Store chat
- `get_user_conversations()` - Retrieve history
- `save_preferences()` - Personalization
- `get_preferences()` - Load user settings
- `add_knowledge()` - Upload documents
- `search_knowledge()` - Query docs

### 5. Knowledge Base (RAG)

**Location**: `Backend/app/knowledge/rag_system.py`

**Process**:
```
PDF Upload
    ↓
Extract Text (PyPDF2)
    ↓
Chunk Text (1000 tokens, 200 overlap)
    ↓
Generate Embeddings (OpenAI)
    ↓
Store in Chroma VectorDB
    ↓
User Query
    ↓
Retrieve Similar Chunks
    ↓
Generate Answer with Context
```

**Features**:
- PDF parsing
- Text chunking
- Semantic search
- Document summarization
- Source attribution

### 6. Tool Manager

**Location**: `Backend/app/tools/tool_manager.py`

**Available Tools**:
```python
calculator()        # Eval expressions
web_search()        # Google Custom Search
get_weather()       # OpenWeather API
execute_code()      # Restricted Python
convert_units()     # Temperature, distance, weight
api_call()         # Whitelisted APIs
```

**Tool Selection**:
- Intelligent routing based on objective
- Context-aware tool choice
- Safety constraints
- Error handling

### 7. Code Analyzer

**Location**: `Backend/app/knowledge/code_analyzer.py`

**Capabilities**:
- Syntax validation (AST parsing)
- Complexity analysis (cyclomatic)
- PEP8 compliance check
- Dependency extraction
- Code explanation
- Refactoring suggestions

**Supported Languages**:
- Python (full)
- JavaScript (basic)
- Java (basic)
- C++ (basic)
- Go (basic)

### 8. Task Engine

**Location**: `Backend/app/automation/task_engine.py`

**Features**:
- CRUD operations on tasks
- Priority levels (1-3)
- Due dates
- Status tracking (pending, in_progress, completed, overdue)
- Recurring tasks (daily/weekly/monthly)
- Reminder system

**Database Schema**:
```sql
tasks (
    id STRING,
    user_id STRING,
    title STRING,
    description TEXT,
    status STRING,
    priority INT,
    due_date TIMESTAMP,
    reminder_time TIMESTAMP,
    metadata JSON
)

schedules (
    id STRING,
    user_id STRING,
    task_template JSON,
    frequency STRING,
    next_occurrence TIMESTAMP,
    is_active BOOL
)

reminders (
    id STRING,
    user_id STRING,
    task_id STRING,
    message TEXT,
    trigger_time TIMESTAMP,
    sent BOOL
)
```

## Data Flow

### Chat Flow
```
User Input
    ↓
ChatRequest (User ID, Message)
    ↓
Retrieve Memory Context (preferences, history)
    ↓
Get RAG Context (knowledge base search)
    ↓
Create AgentState
    ↓
Run Agent App (Planner → Executor → Verifier)
    ↓
Extract Response
    ↓
Save to Memory
    ↓
Return ChatResponse
```

### Knowledge Upload Flow
```
User Uploads PDF
    ↓
Save Temp File
    ↓
Extract Text
    ↓
Generate Embeddings
    ↓
Store in Vector DB
    ↓
Save Metadata to PostgreSQL
    ↓
Return Success Response
```

### Task Automation Flow
```
User Creates Task
    ↓
Save to Database
    ↓
Set Optional Reminder
    ↓
If Recurring → Create Schedule
    ↓
Return Task ID
    ↓
[Background] Process Recurring Tasks
    ↓
Create New Tasks on Schedule
    ↓
[Background] Check Reminders
    ↓
Trigger Notifications
```

## Deployment Architecture

### Development
```
localhost:3000  (Frontend - npm start)
localhost:8000  (Backend - uvicorn reload)
localhost:5432  (PostgreSQL)
localhost:6379  (Redis)
```

### Docker
```
docker-compose up --build
    ├─ backend:8000 (container)
    ├─ frontend:3000 (container)
    ├─ database:5432 (postgres:15)
    └─ redis:6379 (redis:alpine)
```

### Production
```
Load Balancer (nginx/haproxy)
    ├─ Backend Instances (multiple)
    │   └─ Gunicorn Workers
    ├─ Frontend (CDN/Static)
    ├─ Database (managed PostgreSQL)
    └─ Cache (managed Redis)
```

## Security Architecture

### API Security
- CORS validation
- Input sanitization
- SQL injection prevention (SQLAlchemy)
- Rate limiting
- API key management

### Code Execution
- Restricted globals
- Whitelist of functions
- No file system access
- Timeout protection

### Tool Integration
- Domain whitelisting
- API key encryption
- Request validation
- Response sanitization

## Scaling Considerations

### Horizontal Scaling
- Stateless FastAPI instances
- Load balancer distribution
- Shared PostgreSQL
- Shared Redis cache

### Performance Optimization
- Vector DB indexing
- Query caching
- Connection pooling
- Async operations

### Monitoring
- Prometheus metrics
- ELK stack logging
- APM integration
- Error tracking (Sentry)

---

**Architecture designed for scalability, maintainability, and extensibility.**
