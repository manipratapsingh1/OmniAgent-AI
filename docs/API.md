# 📚 API Documentation - OmniAgent AI v2.0

Complete REST API reference for OmniAgent AI with examples.

**Base URL**: `http://localhost:8000` (local) or `https://api.omniai.dev` (production)

**API Version**: 2.0

**Swagger Docs**: `/api/docs`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Chat Endpoints](#chat-endpoints)
3. [Document Management](#document-management)
4. [Task Management](#task-management)
5. [Code Analysis](#code-analysis)
6. [User Preferences](#user-preferences)
7. [System Endpoints](#system-endpoints)
8. [Error Handling](#error-handling)

---

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require a valid JWT token in the `Authorization` header.

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Response (201)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePassword123"
}
```

**Response (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true
  }
}
```

### Refresh Token

```http
POST /api/auth/refresh
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Chat Endpoints

### Send Message

```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": "conv_abc123",
  "message": "What is machine learning?",
  "use_memory": true,
  "use_rag": true,
  "streaming": false
}
```

**Response (200)**:
```json
{
  "conversation_id": "conv_abc123",
  "message_id": "msg_xyz789",
  "response": "Machine learning is a subset of AI...",
  "tokens_used": 150,
  "sources": [
    {
      "type": "knowledge_base",
      "document": "machine_learning_guide.pdf",
      "page": 5
    }
  ]
}
```

**Parameters**:
- `conversation_id` (string, optional): Existing conversation ID. If not provided, creates new.
- `message` (string, required): User message
- `use_memory` (boolean, default: true): Use conversation history
- `use_rag` (boolean, default: false): Search knowledge base
- `streaming` (boolean, default: false): Stream response

### Stream Response

```http
POST /api/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Explain quantum computing",
  "use_memory": true,
  "use_rag": false,
  "streaming": true
}
```

**Response (200)**: Server-Sent Events stream

```
data: {"token": "Quantum"}
data: {"token": " computing"}
data: {"token": " is"}
...
data: {"done": true, "tokens": 245}
```

### Get Conversations

```http
GET /api/conversations?limit=10&skip=0
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "conversations": [
    {
      "id": "conv_abc123",
      "title": "Machine Learning Discussion",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T14:22:00Z",
      "message_count": 12,
      "total_tokens": 2450
    }
  ],
  "total": 5
}
```

### Get Conversation Messages

```http
GET /api/conversations/conv_abc123/messages?limit=50&skip=0
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "conversation_id": "conv_abc123",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Machine learning is...",
      "timestamp": "2025-01-15T10:31:00Z",
      "sources": []
    }
  ],
  "total": 12
}
```

---

## Document Management

### Upload Document

```http
POST /api/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

[File: document.pdf]
```

**Response (201)**:
```json
{
  "document_id": "doc_123",
  "filename": "document.pdf",
  "size_bytes": 1024000,
  "chunks": 15,
  "upload_time": "2025-01-15T10:30:00Z",
  "status": "processed"
}
```

### List Documents

```http
GET /api/documents?limit=20&skip=0
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "machine_learning.pdf",
      "upload_date": "2025-01-15T10:30:00Z",
      "size_bytes": 1024000,
      "chunks": 15,
      "status": "processed"
    }
  ],
  "total": 3
}
```

### Search Knowledge Base

```http
POST /api/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "supervised learning",
  "limit": 5,
  "threshold": 0.7
}
```

**Response (200)**:
```json
{
  "query": "supervised learning",
  "results": [
    {
      "score": 0.95,
      "content": "Supervised learning is a type of machine learning where...",
      "source_document": "machine_learning.pdf",
      "page": 3,
      "chunk_id": "chunk_42"
    }
  ]
}
```

### Delete Document

```http
DELETE /api/documents/doc_123
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_123"
}
```

---

## Task Management

### Create Task

```http
POST /api/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Learn FastAPI",
  "description": "Complete FastAPI tutorial and build a project",
  "priority": 4,
  "due_date": "2025-02-28T23:59:59Z",
  "recurrence": "none"
}
```

**Response (201)**:
```json
{
  "id": "task_123",
  "title": "Learn FastAPI",
  "description": "Complete FastAPI tutorial and build a project",
  "priority": 4,
  "status": "pending",
  "due_date": "2025-02-28T23:59:59Z",
  "created_at": "2025-01-15T10:30:00Z",
  "recurrence": "none"
}
```

**Parameters**:
- `priority`: 1 (low) to 5 (critical)
- `status`: "pending", "in_progress", "completed", "cancelled"
- `recurrence`: "none", "daily", "weekly", "monthly"

### Get Tasks

```http
GET /api/tasks?status=pending&priority=4&limit=20
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "Learn FastAPI",
      "priority": 4,
      "status": "pending",
      "due_date": "2025-02-28T23:59:59Z",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 7
}
```

### Update Task

```http
PUT /api/tasks/task_123
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "in_progress",
  "priority": 5
}
```

**Response (200)**:
```json
{
  "id": "task_123",
  "title": "Learn FastAPI",
  "status": "in_progress",
  "priority": 5,
  "updated_at": "2025-01-15T11:15:00Z"
}
```

### Delete Task

```http
DELETE /api/tasks/task_123
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "message": "Task deleted successfully",
  "task_id": "task_123"
}
```

---

## Code Analysis

### Analyze Code

```http
POST /api/code/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "language": "python",
  "analysis_type": "full"
}
```

**Response (200)**:
```json
{
  "language": "python",
  "analysis": {
    "syntax_valid": true,
    "complexity": "exponential",
    "issues": [
      {
        "type": "performance",
        "severity": "high",
        "message": "Inefficient recursive implementation - use memoization",
        "line": 1
      }
    ],
    "suggestions": [
      "Consider using iterative approach or memoization",
      "Add input validation for negative numbers"
    ],
    "explanation": "This is a recursive Fibonacci implementation with O(2^n) time complexity..."
  }
}
```

**Supported Languages**: Python, JavaScript, Java, C++, Go, C#, TypeScript, Rust

---

## User Preferences

### Get Preferences

```http
GET /api/preferences
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "user_id": "user_123",
  "tone": "professional",
  "expertise_level": "intermediate",
  "preferred_tools": ["calculator", "web_search"],
  "custom_instructions": "Always provide code examples",
  "dark_mode": true,
  "notifications_enabled": true
}
```

### Update Preferences

```http
POST /api/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "tone": "casual",
  "expertise_level": "advanced",
  "dark_mode": true,
  "notifications_enabled": false
}
```

**Response (200)**:
```json
{
  "message": "Preferences updated successfully",
  "preferences": {
    "tone": "casual",
    "expertise_level": "advanced",
    "dark_mode": true,
    "notifications_enabled": false
  }
}
```

**Options**:
- `tone`: "professional", "casual", "technical"
- `expertise_level`: "beginner", "intermediate", "advanced", "expert"
- `dark_mode`: boolean

---

## System Endpoints

### Health Check

```http
GET /api/health
```

**Response (200)**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "features": {
    "rag": true,
    "streaming": true,
    "memory": true,
    "tools": true,
    "tasks": true,
    "code_analysis": true
  },
  "database": "connected",
  "redis": "connected",
  "vector_db": "connected"
}
```

### User Statistics

```http
GET /api/stats
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "user_id": "user_123",
  "statistics": {
    "total_conversations": 5,
    "total_messages": 47,
    "total_documents": 3,
    "total_tasks": 12,
    "tokens_used": 15420,
    "api_calls": 234,
    "last_active": "2025-01-15T10:30:00Z"
  }
}
```

### Root Endpoint

```http
GET /
```

**Response (200)**:
```json
{
  "name": "OmniAgent AI",
  "version": "2.0.0",
  "status": "running",
  "docs_url": "/api/docs",
  "redoc_url": "/api/redoc"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Common Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |

### Error Examples

**401 Unauthorized**:
```json
{
  "detail": "Invalid or expired token",
  "status_code": 401
}
```

**429 Rate Limited**:
```json
{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "status_code": 429,
  "retry_after": 45
}
```

**404 Not Found**:
```json
{
  "detail": "Conversation not found",
  "status_code": 404
}
```

---

## Rate Limiting

**Default Limits** (per minute):
- `/api/chat`: 100 requests
- `/api/chat/stream`: 50 requests
- `/api/documents/upload`: 20 requests
- `/api/code/analyze`: 100 requests
- `/api/auth/login`: 10 requests
- `/api/auth/register`: 5 requests

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705318800
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/conversations?limit=10&skip=20
```

**Parameters**:
- `limit`: Number of results (default: 10, max: 100)
- `skip`: Number of results to skip (default: 0)

**Response Includes**:
```json
{
  "items": [...],
  "total": 42,
  "limit": 10,
  "skip": 20,
  "hasMore": true
}
```

---

## Best Practices

1. **Token Management**
   - Store tokens securely (not in localStorage)
   - Refresh before expiration
   - Invalidate on logout

2. **Error Handling**
   - Always check status code
   - Implement retry logic for 5xx errors
   - Show user-friendly error messages

3. **Performance**
   - Use streaming for large responses
   - Implement pagination
   - Cache responses appropriately

4. **Security**
   - Use HTTPS in production
   - Never log sensitive data
   - Validate all inputs
   - Use strong passwords

---

## Examples

### cURL Examples

**Login**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123"
  }'
```

**Send Chat Message**:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "use_memory": true
  }'
```

**Upload Document**:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "john_doe",
    "password": "SecurePassword123"
})
token = response.json()["access_token"]

# Send message
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/api/chat", 
    headers=headers,
    json={"message": "Hello!"}
)
print(response.json())
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000";

// Login
const loginResponse = await fetch(`${BASE_URL}/api/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "john_doe",
    password: "SecurePassword123"
  })
});
const { access_token } = await loginResponse.json();

// Send message
const chatResponse = await fetch(`${BASE_URL}/api/chat`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${access_token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: "Hello!"
  })
});
console.log(await chatResponse.json());
```

---

**Last Updated**: January 2025

**For More**: See [README.md](../README.md) or [API Docs Swagger](http://localhost:8000/api/docs)