# 🚀 OmniAgent Pre-Deployment Checklist

**Use this checklist before publishing to production (Tomorrow!)**

## 📋 Code Quality

- [ ] All Python syntax errors fixed (`python -m py_compile app/**/*.py`)
- [ ] All TypeScript errors resolved (`npm run build` succeeds)
- [ ] No console.log or debug code left
- [ ] All dependencies in pyproject.toml and package.json pinned
- [ ] Requirements.txt updated: `pip freeze > requirements.txt`
- [ ] .gitignore configured properly
- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] Docstrings added to all public functions

## 🔒 Security

- [ ] `SECRET_KEY` is 32+ characters and random
- [ ] `CORS_ORIGINS` set to specific domain (not *)
- [ ] Database password is strong
- [ ] SSL certificates ready (not self-signed)
- [ ] Security headers enabled in app/core/security_headers.py
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using parameterized queries)
- [ ] CSRF protection enabled
- [ ] XSS protection configured

## 🗄️ Database

- [ ] PostgreSQL 14+ running
- [ ] Database created: `omniagent`
- [ ] All migrations run: `alembic upgrade head`
- [ ] Database backed up
- [ ] Connection pooling configured (20/40)
- [ ] Backups scheduled daily
- [ ] Database user has limited permissions (not superuser)
- [ ] Database connection string doesn't use localhost

## 🔧 Backend

- [ ] All environment variables set in .env.production
- [ ] Backend starts without errors: `python start_production.sh`
- [ ] Health endpoint responds: `curl http://localhost:8000/healthz`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] All routers included in main.py
- [ ] Error handlers configured
- [ ] Logging configured for production
- [ ] Metrics enabled (Prometheus)
- [ ] Gunicorn workers configured (2 * CPU cores + 1)
- [ ] WebSocket support verified (if using real-time features)

## 🎨 Frontend

- [ ] Frontend builds successfully: `npm run build`
- [ ] No build warnings
- [ ] dist/ folder created with index.html
- [ ] All environment variables set
- [ ] API base URL correct
- [ ] Login works with test credentials
- [ ] Chat functionality tested
- [ ] Document upload tested
- [ ] Responsive design verified on mobile
- [ ] Minification working (check console)
- [ ] Service worker configured (if using PWA)

## 📦 Dependencies

- [ ] Python dependencies: `pip install -e ".[production]"`
- [ ] Node dependencies: `npm ci` (not npm install)
- [ ] All optional dependencies for production listed
- [ ] Versions pinned in requirements.txt and package-lock.json
- [ ] No deprecated packages used
- [ ] Security vulnerabilities checked: `npm audit`

## 🚀 Deployment Infrastructure

- [ ] Server/VM provisioned
- [ ] Docker/Docker Compose installed (if using containers)
- [ ] Nginx/reverse proxy configured
- [ ] SSL certificates installed
- [ ] Domain/DNS configured
- [ ] Firewall rules configured (allow 80, 443)
- [ ] SSH access verified
- [ ] Monitoring/logging service (e.g., Sentry) configured

## 🧪 Testing

- [ ] Unit tests pass: `pytest tests/`
- [ ] Integration tests pass
- [ ] E2E tests pass (if available)
- [ ] Signup works
- [ ] Login works
- [ ] Chat responds
- [ ] Document upload works
- [ ] Document Q&A works
- [ ] Admin panel works (if present)
- [ ] Load testing completed (if applicable)

## 📊 Monitoring & Observability

- [ ] Logging configured (JSON format for parsing)
- [ ] Error tracking (Sentry) configured
- [ ] Metrics collection (Prometheus) running
- [ ] Health check endpoint working
- [ ] Database health check working
- [ ] Alert rules configured
- [ ] Log aggregation setup (ELK, Datadog, etc.)

## 📱 External Services

- [ ] Ollama running with required models:
  - [ ] llama3.2
  - [ ] phi3:mini
  - [ ] nomic-embed-text
- [ ] Redis running (if not in-memory)
- [ ] PostgreSQL running
- [ ] SMTP configured (if sending emails)

## 🔄 Backup & Recovery

- [ ] Database backup strategy in place
- [ ] Backup tested and verified
- [ ] Recovery procedure documented
- [ ] Backup schedule set (daily minimum)
- [ ] Backup storage secured
- [ ] Retention policy set

## 📝 Documentation

- [ ] README.md updated with production instructions
- [ ] DEPLOYMENT_GUIDE.md completed
- [ ] API documentation generated
- [ ] Troubleshooting guide created
- [ ] Known issues documented
- [ ] Support contact information provided

## 🔐 Final Security Review

- [ ] No hardcoded credentials in code
- [ ] No debug mode enabled in production
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] Weak algorithms disabled (TLS 1.2+ only)
- [ ] CORS headers correct
- [ ] Security headers comprehensive
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Output encoding configured

## ✅ Before Going Live

**24 Hours Before:**
- [ ] Notification to all stakeholders
- [ ] Final backup taken
- [ ] Deployment rollback plan ready
- [ ] On-call support scheduled

**1 Hour Before:**
- [ ] Final health check of all services
- [ ] Monitoring systems verified
- [ ] Communication channels open

**After Deployment:**
- [ ] Smoke tests completed
- [ ] User testing completed
- [ ] Monitor logs for errors
- [ ] Check metrics dashboard
- [ ] Verify API responses
- [ ] Confirm frontend loads
- [ ] Test critical user flows
- [ ] Monitor for 1 hour after deployment
- [ ] Document any issues
- [ ] Plan post-deployment review

## 🆘 Rollback Plan

If deployment fails:
1. [ ] Stop new application: `docker-compose stop`
2. [ ] Revert database: `alembic downgrade -1`
3. [ ] Restart previous version: `docker-compose up -d`
4. [ ] Verify previous version works
5. [ ] Document what failed
6. [ ] Review logs and fix issue
7. [ ] Test fix in staging first

## 📞 Emergency Contacts

- [ ] DBA: _________________
- [ ] DevOps: _________________
- [ ] Product: _________________
- [ ] CEO: _________________

## 📅 Sign-Off

- [ ] **Development Lead**: _________________ Date: _______
- [ ] **QA Lead**: _________________ Date: _______
- [ ] **DevOps**: _________________ Date: _______
- [ ] **Product Manager**: _________________ Date: _______

---

**Status**: ⬜ Not Started | 🟡 In Progress | 🟢 Complete | 🔴 Blocked

Good luck with the deployment! 🚀
