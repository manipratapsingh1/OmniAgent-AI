# 🤖 OmniAgent AI - Production-Ready AI Agent Platform

**OmniAgent AI** is a state-of-the-art, full-stack enterprise-grade AI system featuring a Multi-Agent Intelligence workflow, Advanced Retrieval-Augmented Generation (RAG) pipelines, secure multi-user authentication, long-term memory, and real-time task automation dashboards.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![React 18+](https://img.shields.io/badge/React-18%2B-blue.svg)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ System Features

### 🔐 Security & Identity Management
* **JWT Session Tokens**: Secure signup, login, and token-based API request authorization.
* **CORS & CSP headers Sync**: Content-Security-Policy (CSP) `connect-src` header values are parsed dynamically from the allowed CORS origins at runtime (no hardcoded origins).
* **Admin Guard Protection**: `/admin` and `/debug` pages are guarded by client-side router checks and backend role-authorization checks (`require_admin` dependency).
* **Rate Limiting**: Integrated client-IP and user-scoped rate limiting (via Redis) to prevent brute-force attacks and throttling.

### 🤖 Multi-Agent Intelligence Orchestration
* **Planner**: Breaks down complex tasks into methodical step-by-step executions.
* **Executor**: Processes each step and runs integrated tools (Calculator, Web Search, Python execution sandbox).
* **Verifier**: Evaluates quality output scoring (0.0-1.0 scoring threshold) for final response correction.
* **Intelligent Retry**: Self-corrects failing actions recursively under a LangGraph-style workflow.

### 📚 Advanced RAG (Retrieval-Augmented Generation)
* **Document Processing**: Uploads PDF, TXT, and Markdown files and performs high-speed chunk indexing with overlap.
* **Semantic Embeddings**: Uses the `nomic-embed-text` model locally (via Ollama) to generate vector embeddings.
* **Vector Search**: Performs fast semantic matches utilizing ChromaDB storage.
* **Interactive Q&A**: Asks context-aware questions directly scoping a single file or the entire database with source citations.

### 🧠 Sharing & Collaboration
* **Public Conversation Sharing**: Generates shareable, dynamic links utilizing settings-configured `FRONTEND_URL`.
* **Anonymous Shared View**: Non-logged users can view a public read-only conversation session directly at `/share/:shareToken` without triggering authentication redirects.

### 📈 Task Automation & Control Center
* **Live Kernel Diagnostics**: Monitor background job processes, memory consumption (short/long-term), CPU/Memory, and cache hits.
* **Task Automation**: CRUD interfaces for prioritizing tasks, recurring job schedules, and status tracking.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│             OmniAgent AI Platform Architecture           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Frontend Client Layer (React 18 + TS + Vite)            │
│  ├─ Pages: Chat, Documents, Settings, Profiles, Admin    │
│  ├─ Public Pages: Anonymous Shared View (/share/:token)  │
│  └─ Router Guards: AdminProtected, AuthProtected         │
│                                 ↓                        │
│  API Gateway (FastAPI Async Layer)                       │
│  ├─ Dynamic CORS & CSP Headers Engine                    │
│  ├─ Rate Limiter Throttling (Redis backend)             │
│  └─ API Token Verification (JWT Authentication)          │
│                                 ↓                        │
│  Core Orchestration Engine                               │
│  ├─ Multi-Agent Workflows (Planner, Executor, Verifier)  │
│  ├─ RAG Pipeline (Document Ingest, Chunker, Embeddings)  │
│  └─ Background Worker Jobs (Syncing & Reindexing)         │
│                                 ↓                        │
│  Data & Engine Storage Layer                             │
│  ├─ PostgreSQL (Primary relational SQLModel DB)          │
│  ├─ Redis (Caching, job telemetry & session rate limits) │
│  ├─ ChromaDB (Vector store database)                     │
│  └─ Ollama (Local LLM & nomic-embed-text embeddings)     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
omniagent-ai-ar/
│
├── omniagent-ai/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/            # API routers & endpoints (v1)
│   │   │   ├── agents/         # Multi-agent system logic
│   │   │   ├── core/           # Security headers, exceptions, middlewares
│   │   │   ├── db/             # Database session, initialization, and seeding
│   │   │   ├── models/         # SQLModel database tables
│   │   │   ├── rag/            # RAG pipelines and embedding generators
│   │   │   ├── services/       # Core business logic
│   │   │   └── utils/          # Performance monitor, rate limiter, db builders
│   │   ├── tests/              # Backend pytest test suite
│   │   ├── pyproject.toml      # Dependency & package config
│   │   └── init_and_run.py     # Database seed and runtime runner
│   │
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── api/            # Axios API client services
│   │   │   ├── components/     # Chat panels, message bubbles, sidebar components
│   │   │   ├── pages/          # React route views (Dashboard, Chat, Share, Admin)
│   │   │   ├── store/          # Zustand states (notifications, global stores)
│   │   │   └── hooks/          # Custom auth, polling, and workspace hooks
│   │   ├── package.json        # Node dependencies & build scripts
│   │   └── vite.config.ts      # Vite configuration
│   │
│   └── docker/                 # Deployment container stack configuration
│       └── docker-compose.yml  # Docker multi-container deployment
│
└── docs/                       # Internal API and architecture guides
```

---

## 🚀 Setup & Installation

### Prerequisite Dependencies
Make sure you have the following installed on your machine:
* **Python 3.11+**
* **Node.js 18+**
* **PostgreSQL 14+** (Install and verify it is running locally)
* **Redis** (Used for rate-limiting, caching, and celery worker telemetry)
* **Ollama** (Running with the `nomic-embed-text` and `llama3.2`/`phi3:mini` models)

---

### Step 1: Set Up Backend

1. Navigate to the backend directory:
   ```bash
   cd omniagent-ai/backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Mac/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` settings:
   Create a `.env` file under `omniagent-ai/backend/.env` with your credentials:
   ```env
   SECRET_KEY=change-me-to-a-very-long-safe-secret-key-32-chars
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/omniagent
   REDIS_URL=redis://localhost:6379/0
   OLLAMA_BASE_URL=http://localhost:11434
   CORS_ORIGINS=http://localhost:5173
   FRONTEND_URL=http://localhost:5173
   ```

5. Initialize the database and run the server:
   ```bash
   python init_and_run.py
   ```
   This will bootstrap database migrations, seed initial records, and start the FastAPI webserver at `http://localhost:8000`.

---

### Step 2: Set Up Frontend

1. Navigate to the frontend directory:
   ```bash
   cd omniagent-ai/frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Launch the hot-reloading development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser to interact with the application.

---

### Step 3: Run the Docker Stack (Alternative)
To spin up the entire system (Backend, Frontend, Postgres, Redis, Chroma) containerized:
```bash
cd omniagent-ai/docker
docker-compose up -d
```

---

## 🧪 Testing & Verification

### Run Backend Test Suite
The backend contains a suite of 428 unit and integration tests. Run tests from the `backend/` directory:
```bash
python -m pytest tests/ -vv
```

### Build Frontend for Production
Verify that the frontend compiles cleanly and passes all static type checks:
```bash
cd omniagent-ai/frontend
npm run build
```
The optimized bundle files will be generated in `frontend/dist/` and are ready to serve via a production server or CDN.

---

## 🔑 Primary API Endpoints

### 🔐 Authentication
* `POST /api/v1/auth/signup` — Create user profile
* `POST /api/v1/auth/login` — Sign in and retrieve JWT access token
* `POST /api/v1/auth/change-password` — Update password

### 💬 Conversations & Sharing
* `POST /api/v1/conversations/` — Start a chat thread
* `GET /api/v1/conversations/` — Get user conversation history
* `POST /api/v1/tools/share-conversation` — Generate public share token for a chat thread
* `GET /api/v1/tools/shared-conversation/{share_token}` — Retrieve shared conversation payload (Public)

### 📚 Documents & RAG
* `POST /api/v1/documents/upload` — Upload PDF/TXT/MD files to vector store
* `GET /api/v1/documents/` — Retrieve inventory of uploaded documents
* `POST /api/v1/documents/qa` — Generate synthesized answers with source citations
* `GET /api/v1/documents/rag-search` — Query vector matches directly

### ⚙️ System Admin & Debugging
* `GET /api/v1/admin/dashboard` — View system overview analytics (Admin only)
* `GET /api/v1/debug/status` — Live diagnostics on performance, cache, jobs, and memory stats (Admin only)

---

**Made with ❤️ by the OmniAgent AI Team**