# OmniAgent Citation Validation Report

This report summarizes how citations are parsed, validated, and enriched in OmniAgent to ensure data integrity and prevent hallucination.

## Citation Processing Flow

```
LLM Response (with [doc:X#Y] syntax)
                ↓
       Regex Parsing Engine
                ↓
    Source Verification Filter (cross-check against retrieved chunks)
                ↓
   Enrichment Layer (load file metadata: name, page, section from DB)
                ↓
     Structured Citation Payload
```

## Extraction and Fallback Mechanics

1. **Structured Parsing**: The system extracts citations matching `[doc:(\d+)#(\d+)]` regex, identifying the document ID and the chunk index.
2. **Metadata Enrichment**: Using the document ID, the system queries the SQL database to fetch:
   - **Document Name / Filename**
   - **Page Number** (calculated from text offsets in PDFs)
   - **Section Header** (extracted from semantic header lines)
   - **Confidence Score** (cosine similarity score)
3. **Graceful Fallback**: Small models or streaming responses sometimes omit explicit citations even when answering from documents. To ensure every document answer has sources, `citations.py` now implements a fallback:
   - If no citations are found in the response, but document chunks were retrieved, it automatically attaches the **top-ranked source chunk** as the citation.
   - If unverified/hallucinated document IDs are cited, it discards them and attaches the actual retrieved source.

## Validation Example

Here is a verified citation output from our end-to-end integration test:

* **Source Filename**: `test_ml_guide.txt`
* **Document ID**: `105`
* **Chunk Index**: `0`
* **Page Number**: `1`
* **Section**: `Introduction`
* **Confidence**: `80.0%`
* **Excerpt Excerpt**: *"Machine learning is a subset of artificial intelligence. It enables systems..."*
