# DEPLOYMENT CHECKLIST - RAG Bug Fixes
**Version**: 1.0  
**Date**: 2026-06-06  
**Status**: Ready for Deployment

---

## PRE-DEPLOYMENT

### [ ] Code Review
- [x] All 8 files reviewed
- [x] No syntax errors (tested with py_compile)
- [x] No breaking changes
- [x] Backward compatible
- [ ] Peer review completed (pending)

### [ ] Testing Completed
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Manual smoke tests completed (use TESTING_GUIDE.md)
- [ ] Performance benchmarks acceptable
- [ ] Load testing completed

### [ ] Dependencies
- [x] No new package dependencies
- [x] All imports exist
- [x] Version compatibility verified
- [ ] Dependency scan (security) completed

### [ ] Documentation
- [x] BUG_FIX_REPORT.md created
- [x] TESTING_GUIDE.md created
- [x] Code comments added
- [x] Logging messages clear

---

## STAGING DEPLOYMENT

### [ ] Environment Setup
- [ ] Staging database ready
- [ ] Staging Chroma instance ready
- [ ] Staging Ollama instance ready
- [ ] Staging Redis instance ready
- [ ] Environment variables configured

### [ ] Database Preparation
- [ ] Database backup taken
- [ ] Migration script (if needed) tested
- [ ] No schema changes needed - skip this
- [ ] Rollback procedure documented

### [ ] Deployment
```bash
# 1. Backup current code
git tag backup-before-rag-fixes
git stash

# 2. Deploy new code
git pull origin main  # or checkout new branch
# or manually replace files:
#   app/utils/citations.py (NEW)
#   app/services/fast_chat_service.py (MODIFIED)
#   app/llm/prompts.py (MODIFIED)
#   app/agents/research_agent.py (MODIFIED)
#   app/services/document_service.py (MODIFIED)
#   app/rag/retriever.py (MODIFIED)
#   app/api/v1/chat.py (MODIFIED)
#   app/repositories/document_repo.py (MODIFIED)
#   app/llm/ollama_client.py (MODIFIED)

# 3. Validate Python syntax
python -m py_compile \
  app/utils/citations.py \
  app/services/fast_chat_service.py \
  app/llm/prompts.py \
  app/agents/research_agent.py \
  app/services/document_service.py \
  app/rag/retriever.py \
  app/api/v1/chat.py \
  app/repositories/document_repo.py \
  app/llm/ollama_client.py

# 4. Restart backend service
systemctl restart backend  # or equivalent
```

### [ ] Staging Smoke Tests
- [ ] Backend starts without errors
- [ ] Database connection successful
- [ ] Chroma connection successful
- [ ] Ollama connection successful
- [ ] Health check: GET /healthz returns 200
- [ ] Can create user account
- [ ] Can upload document
- [ ] Document chunks created
- [ ] Document vectors stored
- [ ] Can query documents
- [ ] Citations extracted correctly
- [ ] Sources filtered correctly

### [ ] Staging Integration Tests
Run TESTING_GUIDE.md tests:
- [ ] Test 1: Citation extraction
- [ ] Test 2: Document upload
- [ ] Test 3: Retrieval logging
- [ ] Test 4: Citation accuracy
- [ ] Test 5: Document deletion
- [ ] Test 6: System prompt quality
- [ ] Test 7: Embedding dimensions
- [ ] Test 8: Fast-RAG endpoint

### [ ] Staging Performance Tests
- [ ] Document upload < 5 seconds
- [ ] Vector retrieval < 500ms
- [ ] Chat response < 15 seconds total
- [ ] Throughput acceptable (100+ req/min)
- [ ] Memory usage stable
- [ ] No memory leaks over 1 hour

### [ ] Staging Security Review
- [ ] No sensitive data in logs
- [ ] File upload size limit enforced
- [ ] Vector store access controlled
- [ ] User isolation verified
- [ ] Citation injection prevention working

---

## PRODUCTION DEPLOYMENT

### [ ] Pre-Production Steps
- [ ] Production database backup
- [ ] Production code repository tagged
- [ ] Rollback plan documented
- [ ] On-call engineer available
- [ ] Monitoring alerts configured

### [ ] Deployment Window
- [ ] Maintenance window scheduled
- [ ] Maintenance page deployed (if needed)
- [ ] Team notified
- [ ] Customer notification sent (if necessary)

### [ ] Production Deployment
```bash
# Follow same steps as staging:
# 1. Backup
# 2. Deploy
# 3. Validate
# 4. Restart
```

### [ ] Post-Deployment Verification
- [ ] Backend service running
- [ ] No error logs in first 5 minutes
- [ ] Database queries working
- [ ] Vector store accessible
- [ ] Sample document upload successful
- [ ] Sample chat query successful

### [ ] Monitoring
- [ ] Application metrics dashboard loaded
- [ ] Error rate normal (< 0.1%)
- [ ] Latency metrics normal
- [ ] Database connections healthy
- [ ] Vector store response times normal
- [ ] Logging system capturing all events
- [ ] Alerts firing correctly

### [ ] User Acceptance Testing
- [ ] Admin verified functionality
- [ ] Test users running scenarios
- [ ] Feedback collected
- [ ] No critical issues reported

---

## ROLLBACK PROCEDURE (if needed)

### [ ] Decision
- Serious bug discovered: YES [ ] NO [ ]
- Performance degradation: YES [ ] NO [ ]
- Data corruption risk: YES [ ] NO [ ]

### [ ] Immediate Actions
```bash
# 1. Stop new deployment (if still in progress)
# 2. Restore previous code
git checkout backup-before-rag-fixes
# or manually restore files

# 3. Validate previous code
python -m py_compile app/**/*.py

# 4. Restart service
systemctl restart backend

# 5. Verify functionality
curl http://localhost:8000/healthz
```

### [ ] Database Recovery
- [x] No schema changes - no database recovery needed
- [ ] If needed: restore database from backup
- [ ] Verify data integrity

### [ ] Notification
- [ ] Team notified of rollback
- [ ] Customer notified (if necessary)
- [ ] Root cause analysis initiated
- [ ] Post-mortem scheduled

### [ ] Post-Rollback
- [ ] Verify old version working
- [ ] Gather logs for analysis
- [ ] Fix issues in development
- [ ] Re-test before next deployment attempt

---

## POST-DEPLOYMENT MONITORING (First 24 Hours)

### [ ] Hourly Checks (First 4 Hours)
- [ ] Error rate normal
- [ ] Latency metrics normal
- [ ] User activity normal
- [ ] No database issues
- [ ] No vector store issues

### [ ] Daily Checks (First 24 Hours)
- [ ] Citation accuracy metrics good
- [ ] Document upload success rate > 95%
- [ ] Search results relevant
- [ ] No memory leaks
- [ ] No unexpected errors
- [ ] User satisfaction feedback positive

### [ ] Metrics to Monitor
```
- Document upload success rate: target > 99%
- Citation extraction accuracy: target > 95%
- Average chat latency: target < 15 seconds
- Vector retrieval latency: target < 500ms
- Error rate: target < 0.1%
- User satisfaction: target > 4.5/5.0
```

### [ ] Logging Review
- [ ] All log types appearing
- [ ] Debug logs helpful
- [ ] Error messages clear
- [ ] Performance metrics recorded
- [ ] No sensitive data leaked

---

## DOCUMENTATION UPDATES

### [ ] After Successful Deployment
- [ ] Update system documentation
- [ ] Add release notes
- [ ] Update API documentation (if needed)
- [ ] Update troubleshooting guide
- [ ] Update FAQ with new features

### [ ] Team Communication
- [ ] Send deployment success notification
- [ ] Share metrics/results
- [ ] Thank team for support
- [ ] Plan next improvements

---

## FILES TO DEPLOY

### New Files
```
backend/app/utils/citations.py
backend/test_e2e_pipeline.py
```

### Modified Files
```
backend/app/services/fast_chat_service.py
backend/app/llm/prompts.py
backend/app/agents/research_agent.py
backend/app/services/document_service.py
backend/app/rag/retriever.py
backend/app/api/v1/chat.py
backend/app/repositories/document_repo.py
backend/app/llm/ollama_client.py
```

### Configuration Files
```
.env (NO CHANGES NEEDED)
requirements.txt (NO CHANGES NEEDED)
pyproject.toml (NO CHANGES NEEDED)
```

### Documentation (Deployment)
```
BUG_FIX_REPORT.md
TESTING_GUIDE.md
DEPLOYMENT_CHECKLIST.md (this file)
```

---

## SIGN-OFF

### [ ] Lead Developer
- Name: _______________
- Date: _______________
- Signature: _______________

### [ ] QA Manager
- Name: _______________
- Date: _______________
- Signature: _______________

### [ ] DevOps/SRE
- Name: _______________
- Date: _______________
- Signature: _______________

### [ ] Product Manager
- Name: _______________
- Date: _______________
- Signature: _______________

---

## NOTES

### What Was Fixed
1. ✅ Citation extraction (new file)
2. ✅ Sources filtering (only show cited ones)
3. ✅ System prompt improvements (7 prompts)
4. ✅ Document deletion vector removal
5. ✅ Embedding dimension detection
6. ✅ Debug logging enhancements
7. ✅ Fast-RAG endpoint fixes
8. ✅ Chat consistency improvements

### Expected Outcomes
- Better answer quality (grounded in documents)
- Accurate source attribution
- Improved user trust
- Better debugging capability
- No data loss on document deletion

### Risk Level
**LOW** - All changes are application logic, no schema changes

### Estimated Downtime
**5-10 minutes** (service restart only)

### Rollback Difficulty
**EASY** - Just revert file changes and restart

---

## FINAL CHECKLIST SUMMARY

Total checkboxes: 80
Required to check: All

Before proceeding to next step, ensure all checkboxes in current section are checked.

**Status**: Ready for deployment ✅
