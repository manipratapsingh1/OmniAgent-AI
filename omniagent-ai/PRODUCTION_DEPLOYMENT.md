# 🚀 OmniAgent Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration
```bash
# Copy production environment file
cp .env.production .env

# Edit with your actual values:
nano .env  # or use your preferred editor

# Required settings:
- SECRET_KEY: Generate a strong 32+ character random key
  python -c "import secrets; print(secrets.token_urlsafe(32))"
- DATABASE_URL: Your production PostgreSQL connection string
- CORS_ORIGINS: Your production domain (e.g., https://yourdomain.com)
- SENTRY_DSN: Your Sentry error tracking URL (optional)
```

### 2. Database Setup
```bash
# Run migrations
cd backend
alembic upgrade head

# Verify database connection
python -c "from app.db.session import engine; print(engine.execute('SELECT 1'))"
```

### 3. Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt  # or from pyproject.toml

# Frontend
cd frontend
npm ci  # Use ci instead of install for production
```

### 4. Build Frontend
```bash
cd frontend
npm run build
# Output will be in frontend/dist/
```

## Deployment Options

### Option 1: Using Docker Compose (Recommended)
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Verify services
docker-compose ps
docker-compose logs backend
```

### Option 2: Manual Deployment (VPS/Server)

#### Backend Setup
```bash
cd omniagent-ai/backend

# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate  # Unix/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[production]"

# Create .env file
cp .env.example .env
# Edit .env with production values

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --access-logfile - --error-logfile -
```

#### Frontend Setup
```bash
cd omniagent-ai/frontend

# Install dependencies
npm ci

# Build
npm run build

# Serve with nginx (see nginx.conf)
# Or use a CDN to serve the dist/ folder
```

#### Nginx Reverse Proxy Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend
    location / {
        root /var/www/omniagent/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Option 3: Cloud Platforms

#### Heroku
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create omniagent-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=postgresql://...

# Deploy
git push heroku main
```

#### AWS ECS
```bash
# Build Docker image
docker build -t omniagent:latest .
docker tag omniagent:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/omniagent:latest

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/omniagent:latest

# Create ECS task definition and service
# See AWS documentation for details
```

## Post-Deployment Verification

### 1. Health Checks
```bash
# Check backend health
curl https://yourdomain.com/api/v1/health

# Check liveness probe
curl https://yourdomain.com/healthz

# Response should be 200 OK with status info
```

### 2. Database Connection
```bash
# SSH into server, then:
curl https://yourdomain.com/api/v1/health/db
# Should return database status
```

### 3. API Documentation
Visit: `https://yourdomain.com/api/docs`
Visit: `https://yourdomain.com/api/redoc`

### 4. Frontend Access
Visit: `https://yourdomain.com`
- Try login with test credentials
- Verify features work

### 5. Logs
```bash
# Docker
docker-compose logs -f backend
docker-compose logs -f frontend

# Manual deployment
tail -f /var/log/gunicorn.log
tail -f /var/log/nginx/access.log
```

## Monitoring & Maintenance

### 1. Enable Monitoring
- Set `ENABLE_SENTRY=true` in .env and provide SENTRY_DSN
- Check `/api/v1/metrics` for Prometheus metrics
- Setup log aggregation (ELK, Datadog, etc.)

### 2. Database Backups
```bash
# PostgreSQL backup
pg_dump omniagent > backup_$(date +%Y%m%d).sql

# Restore from backup
psql omniagent < backup_20240101.sql
```

### 3. Update Model Files
```bash
# If using Ollama, ensure models are pulled:
curl http://localhost:11434/api/pull -d '{"name": "llama3.2"}'
curl http://localhost:11434/api/pull -d '{"name": "phi3:mini"}'
curl http://localhost:11434/api/pull -d '{"name": "nomic-embed-text"}'
```

### 4. Database Migrations
```bash
# When updating code with new migrations:
cd backend
alembic upgrade head
```

## Scaling Considerations

### 1. Load Balancing
- Use Nginx or HAProxy for multiple backend instances
- Use WebSocket-aware load balancer (sticky sessions)

### 2. Caching
- Redis for response caching (already configured)
- Cloudfront/CDN for frontend assets

### 3. Worker Processes
```bash
# Recommended: # of workers = (2 × CPU cores) + 1
# For 4 CPU cores: 9 workers
gunicorn app.main:app --workers 9 --worker-class uvicorn.workers.UvicornWorker
```

### 4. Database Connection Pooling
- Already configured in app/db/session.py
- pool_size=20, max_overflow=40 for production
- Adjust based on expected concurrent users

## Troubleshooting

### Backend Won't Start
1. Check environment variables: `echo $DATABASE_URL`
2. Check database connection: `psql $DATABASE_URL -c "SELECT 1"`
3. Check logs: `docker-compose logs backend`

### Database Connection Errors
1. Verify PostgreSQL is running
2. Check credentials in DATABASE_URL
3. Ensure database exists: `psql -l | grep omniagent`

### Frontend Blank Screen
1. Check browser console (F12) for errors
2. Verify frontend build: `ls frontend/dist/index.html`
3. Check nginx logs: `tail -f /var/log/nginx/error.log`

### API Timeout Issues
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Increase timeouts in .env if needed (OLLAMA_GENERATE_TIMEOUT)
3. Check server logs for slow operations

## Security Checklist

- [ ] SSL certificates installed (not self-signed in production)
- [ ] SECRET_KEY is strong and random
- [ ] CORS_ORIGINS set to exact domain (not *)
- [ ] Database backups scheduled
- [ ] Security headers enabled (automatic)
- [ ] API rate limiting enabled
- [ ] Error tracking (Sentry) configured
- [ ] Firewall rules applied
- [ ] Regular security updates scheduled
- [ ] Access logs monitored

## Support

For issues, check:
1. Server logs: `docker-compose logs backend`
2. Database logs: `tail -f /var/log/postgresql/`
3. Nginx logs: `tail -f /var/log/nginx/error.log`
4. Application documentation: `/docs` endpoint
5. GitHub issues: https://github.com/yourgithub/omniagent-ai

