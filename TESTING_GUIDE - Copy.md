# QUICK TESTING GUIDE - RAG Bug Fixes
**Duration**: ~15 minutes  
**Goal**: Verify all 8 bugs are fixed

---

## SETUP (1 minute)

### Prerequisites
- Backend running on `http://localhost:8000`
- Ollama running on `http://localhost:11434`
- Chroma running on `http://localhost:8001`
- PostgreSQL running
- Redis running

### Start Services
```bash
# Terminal 1: Start backend
cd omniagent-ai/backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Ollama (if not running)
ollama serve

# Terminal 3: Start Chroma (if needed)
chroma run --port 8001
```

---

## TEST 1: Citation Extraction (2 min)
**Verifies**: Bug #1, #3 fixed

### Steps
1. Open Python shell in backend directory:
```bash
python
```

2. Test citation extraction:
```python
from app.utils.citations import extract_citations_from_response, filter_sources_by_citations

# Test extraction
response = "According to [doc:123#5] the answer is X. More info in [doc:456#2]."
citations = extract_citations_from_response(response)
print(citations)
# Expected: [{'document_id': 123, 'chunk_index': 5}, {'document_id': 456, 'chunk_index': 2}]

# Test filtering
all_sources = [
    {"document_id": 123, "chunk_index": 5, "text": "The answer is X"},
    {"document_id": 999, "chunk_index": 0, "text": "Unrelated info"},
    {"document_id": 456, "chunk_index": 2, "text": "More info"},
]
filtered = filter_sources_by_citations(all_sources, citations)
print(len(filtered))
# Expected: 2 (only cited sources)
```

**Expected Result**: ✅ Only 2 sources (123#5 and 456#2), not 999#0

---

## TEST 2: Document Upload Pipeline (4 min)
**Verifies**: Bug #1, #2, #6 partially fixed

### Step 1: Create Test Document
```bash
# Create test.txt in backend directory
cat > test_doc.txt << 'EOF'
# Machine Learning Basics

Machine learning is a subset of artificial intelligence. It enables systems to learn from data.

## Key Concepts
1. Supervised Learning: Learning with labeled data
2. Unsupervised Learning: Learning from unlabeled data
3. Reinforcement Learning: Learning through interactions

## Applications
- Computer Vision: Image recognition
- Natural Language Processing: Text analysis
- Recommendation Systems: Product suggestions
EOF
```

### Step 2: Upload via curl
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_doc.txt"
```

### Step 3: Check Response
```json
{
  "id": 1,
  "filename": "test_doc.txt",
  "status": "indexed",
  "embedding_status": "embedded",
  "chunk_count": 3,
  "size_bytes": 245
}
```

**Expected Result**: ✅ status=indexed, embedding_status=embedded, chunk_count>0

---

## TEST 3: Retrieval with Logging (3 min)
**Verifies**: Bug #6 (logging) fixed

### Step 1: Check Logs
```bash
# While running backend, grep for retrieval logs
tail -100 backend.log | grep "retrieve\."
```

### Step 2: Send Query
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "use_rag": true
  }'
```

### Step 3: Verify Logs Show
```
retrieve.start - user_id=X, query_len=24, k=4
retrieve.embedding_query - query_len=24
retrieve.vector_query_complete - results_count=3, elapsed_ms=245
retrieve.result - rank=1, doc_id=1, chunk_idx=0, score=0.92
retrieve.result - rank=2, doc_id=1, chunk_idx=1, score=0.88
retrieve.result - rank=3, doc_id=1, chunk_idx=2, score=0.75
retrieve.success.fallback - results=3, top_score=0.92, elapsed_ms=250
chat_fast.rag_retrieved - duration_ms=250, chunks=3
chat_fast.citations_extracted - citations_in_text=1, verified_sources=1, accuracy_score=1.0
```

**Expected Result**: ✅ Detailed logging at each step

---

## TEST 4: Citation Accuracy (3 min)
**Verifies**: Bug #1, #2 fixed

### Step 1: Get Chat Response
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is supervised learning?",
    "use_rag": true
  }'
```

### Step 2: Examine Response
```json
{
  "content": "Supervised learning is learning with labeled data [doc:1#1]. This approach requires training data where each example has a known answer.",
  "sources": [
    {
      "document_id": 1,
      "chunk_index": 1,
      "snippet": "Supervised Learning: Learning with labeled data"
    }
  ],
  "trace": []
}
```

### Verify:
- [x] Answer contains document content (not generic)
- [x] Answer includes `[doc:X#Y]` citation
- [x] Sources list contains ONLY cited documents
- [x] Sources count = number of citations in answer

**Expected Result**: ✅ Citations match between answer and sources

---

## TEST 5: Document Deletion (2 min)
**Verifies**: Bug #4 fixed

### Step 1: Verify Document Exists
```bash
curl -X GET http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN"
# Shows document with id=1
```

### Step 2: Query Before Deletion
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "machine learning",
    "use_rag": true
  }'
# Returns sources from document 1
```

### Step 3: Delete Document
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
# Returns: true
```

### Step 4: Query After Deletion
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "machine learning",
    "use_rag": true
  }'
# Should NOT return sources from deleted document
# Should return "no relevant documents found" or general knowledge answer
```

**Expected Result**: ✅ No results from deleted document

---

## TEST 6: System Prompt Quality (2 min)
**Verifies**: Bug #2 fixed

### Step 1: Ask Multi-document Question
```bash
# Upload 2 different documents first
# Document A: About Python
# Document B: About JavaScript

# Then ask:
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare Python and JavaScript",
    "use_rag": true
  }'
```

### Step 2: Verify Answer
- [x] Uses both documents
- [x] Has citations: `[doc:A#X]` and `[doc:B#Y]`
- [x] Sources show both documents
- [x] Answer is specific, not generic

**Expected Result**: ✅ Answer grounded in documents, proper citations

---

## TEST 7: Embedding Dimensions (1 min)
**Verifies**: Bug #5 fixed

### Step 1: Check Backend Logs During Upload
```bash
tail -50 backend.log | grep "embed.dimension_detected"
```

### Expected Output
```
embed.dimension_detected - dimension=768, model=nomic-embed-text
```

**Expected Result**: ✅ Detected dimension=768 (correct for nomic-embed-text)

---

## TEST 8: Fast-RAG Endpoint (2 min)
**Verifies**: Bug #7 fixed

### Step 1: Use /fast-rag Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/chat/fast-rag \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?"
  }'
```

### Step 2: Check Response
```json
{
  "content": "[doc:1#0] Machine learning...",
  "sources": [
    {"document_id": 1, "chunk_index": 0, ...}
  ]
}
```

### Verify:
- [x] Sources are filtered (not all retrieved chunks)
- [x] Only cited sources in response
- [x] Fast response time (<5 seconds)

**Expected Result**: ✅ Citation filtering works in /fast-rag

---

## SUMMARY CHECKLIST

After running all 8 tests:

- [ ] Test 1: Citation extraction works ✓
- [ ] Test 2: Upload creates chunks and embeddings ✓
- [ ] Test 3: Detailed logs at each step ✓
- [ ] Test 4: Citations in answer match sources ✓
- [ ] Test 5: Deleted docs not searchable ✓
- [ ] Test 6: Answers grounded in documents ✓
- [ ] Test 7: Embedding dimension detected correctly ✓
- [ ] Test 8: Fast-RAG filters sources correctly ✓

**All 8 Tests Passed** → RAG bugs are FIXED ✅

---

## TROUBLESHOOTING

### "No documents retrieved"
- Check Chroma is running: `curl http://localhost:8001/api/v1/version`
- Check embeddings were created: `grep "vectors_created" backend.log`
- Verify chunk_count > 0 in document upload response

### "Citations not extracted"
- Check model output includes `[doc:X#Y]` format
- Verify system prompt is using RESEARCH_SYSTEM or CHAT_SYSTEM
- Check logs for "citations_extracted" entries

### "Deleted document still appears"
- Verify vector deletion log: `grep "vectors_deleted" backend.log`
- Check Chroma directly: List collection items
- Restart Chroma if needed

### "Wrong embedding dimension"
- Check log for detected dimension
- Should be 768 for nomic-embed-text
- If not 768, re-upload document

---

## ADVANCED TESTING

### Load Testing
```bash
# Test with 100 documents
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@test_doc_$i.txt"
done
```

### Citation Accuracy Metrics
```python
# Count correct/incorrect citations
correct = sum(1 for s in citations if source_exists(s))
accuracy = correct / len(citations) if citations else 1.0
print(f"Citation accuracy: {accuracy:.1%}")
# Expected: 95%+ (some hallucinations acceptable)
```

### Performance Benchmarks
```
Upload PDF: < 5 seconds
Retrieve: < 500ms
Generate answer: < 10 seconds
Total chat latency: < 15 seconds
```

---

## NEXT STEPS

After verification:
1. Deploy to staging environment
2. Run integration test suite
3. Deploy to production
4. Monitor logs for any issues
5. Gather user feedback on answer quality
