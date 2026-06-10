# 🚀 AI Assistant Platform - Quick Start Guide

## Prerequisites

Ensure you have these services running:
- PostgreSQL: `postgresql://postgres:1234@localhost:5432/omniagent`
- Redis: `redis://localhost:6379/0`
- Ollama (optional): `http://localhost:11434` with `llama3.2` model

## Starting the Backend

```bash
cd omniagent-ai/backend

# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Start the FastAPI server
python run_server.py
```

Server will be available at: **http://localhost:8000**
API docs available at: **http://localhost:8000/docs**

## Starting the Frontend

```bash
cd omniagent-ai/frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:5173** (or next available port)

## Testing the System

### 1. Login
Open **http://localhost:5173** → Navigate to login page

**Test Credentials**:
- Email: `testuser@example.com`
- Password: `TestPassword123`

### 2. Use the Chat Interface
1. Click "New Conversation" to start
2. Type your message in the input field
3. Press Enter or click Send
4. Watch responses stream in real-time
5. Use the microphone icon for voice input (requires browser permission)

### 3. Test API Directly

```bash
cd omniagent-ai/backend
python test_assistant_api.py
```

This will:
- Login automatically
- Test non-streaming chat
- Test streaming chat with SSE chunks

## API Endpoints

### Chat Endpoint
```
POST /api/v1/assistant/chat
Authorization: Bearer <token>

Request:
{
  "message": "Hello, what is 2+2?",
  "stream": false  // or true for streaming
}

Response (non-streaming):
{
  "ok": true,
  "response": "2 + 2 = 4"
}

Response (streaming):
data: {"type": "chunk", "data": {"text": "2 + 2 = "}}
data: {"type": "chunk", "data": {"text": "4"}}
data: {"type": "complete", "data": {"text": "4"}}
```

### Transcribe Audio
```
POST /api/v1/assistant/transcribe
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <audio_file>

Response:
{
  "text": "the transcribed text"
}
```

### Text to Speech
```
POST /api/v1/assistant/tts
Authorization: Bearer <token>

Request:
{
  "text": "Hello world"
}

Response:
{
  "audio_url": "https://..."
}
```

## Database Migrations

Migrations are automatically applied on server startup. To manually apply:

```bash
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Common Issues

### "Connection refused: postgresql"
- Ensure PostgreSQL is running on port 5432
- Check DATABASE_URL in .env

### "Connection refused: redis"
- Ensure Redis is running on port 6379
- Used for background jobs, not required for chat

### "Module not found: app"
- Ensure you're running from the backend directory
- Activate the virtual environment

### "Port 8000 already in use"
- Kill the existing process: `lsof -ti:8000 | xargs kill -9` (macOS/Linux)
- Or specify a different port: `python run_server.py --port 8001`

### "TypeError: window.webkitSpeechRecognition is not defined"
- Web Speech API only works in secure contexts (https) or localhost
- Some browsers don't support it - check browser compatibility

## Performance Tips

1. **Streaming**: Use streaming mode for large responses
2. **Batch Requests**: Process multiple queries asynchronously
3. **Caching**: Conversation history is cached in memory (for session)
4. **Database**: Queries are indexed on common fields

## Environment Variables

Create or update `.env` file:

```
# Database
DATABASE_URL=postgresql://postgres:1234@localhost:5432/omniagent

# Redis (for background jobs)
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Features
ASSISTANT_ENABLED=True
```

## Next Steps

1. **Integrate Real LLMs**:
   - Add OpenAI API key: `OPENAI_API_KEY=sk-...`
   - Add Gemini API key: `GEMINI_API_KEY=...`
   - Update provider selection in AIService

2. **Deploy**:
   - Push frontend to CDN (Vercel, Netlify, AWS S3)
   - Deploy backend to cloud (AWS EC2, GCP, Azure, Railway)
   - Set up SSL/TLS certificates
   - Configure CORS for production domain

3. **Advanced Features**:
   - Implement memory persistence
   - Add document Q&A
   - Set up agent mode
   - Enable multimodal input

## Documentation

- [ASSISTANT_IMPLEMENTATION.md](./ASSISTANT_IMPLEMENTATION.md) - Technical details
- [SESSION_STATUS_REPORT.md](./SESSION_STATUS_REPORT.md) - Completion status
- [omniagent-ai/README.md](./omniagent-ai/README.md) - Project README

## Support

For issues or questions:
1. Check the logs: `tail -f <server.log>`
2. Review API docs: http://localhost:8000/docs
3. Run tests: `python test_assistant_api.py`
4. Check database: Use your PostgreSQL client to inspect tables

---

**Happy coding! 🎉**
