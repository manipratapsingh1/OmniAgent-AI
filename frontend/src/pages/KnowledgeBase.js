// frontend/src/pages/KnowledgeBase.js
import React, { useState, useEffect } from 'react';
import '../styles/KnowledgeBase.css';

export default function KnowledgeBase({ userId }) {
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, [userId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://localhost:8000/knowledge-base/${userId}`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`http://localhost:8000/upload-document?user_id=${userId}`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        alert('✅ Document uploaded successfully!');
        loadDocuments();
      } else {
        alert('❌ Upload failed');
      }
    } catch (error) {
      console.error('Error uploading:', error);
      alert('Error uploading document');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8000/search-knowledge?user_id=${userId}&query=${searchQuery}`
      );
      const data = await res.json();
      setSearchResults(data.rag_results || {});
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  return (
    <div className="knowledge-base">
      <h1>📚 Knowledge Base</h1>

      <div className="kb-upload">
        <h2>Upload Documents</h2>
        <p>Upload PDFs, documents, and notes to create your personal knowledge base</p>
        <div className="upload-area">
          <input
            type="file"
            accept=".pdf,.txt,.doc,.docx"
            onChange={handleFileUpload}
            disabled={uploading}
            id="file-upload"
          />
          <label htmlFor="file-upload" className="upload-label">
            {uploading ? '⏳ Uploading...' : '📤 Click to upload or drag files'}
          </label>
        </div>
      </div>

      <div className="kb-search">
        <form onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search your knowledge base... 🔍"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
      </div>

      {searchResults.answer && (
        <div className="search-results">
          <h3>📖 Search Results</h3>
          <div className="result-answer">
            <p>{searchResults.answer}</p>
          </div>
          {searchResults.sources && searchResults.sources.length > 0 && (
            <div className="result-sources">
              <h4>Sources:</h4>
              {searchResults.sources.map((source, idx) => (
                <div key={idx} className="source-item">
                  <strong>{source.document}</strong>
                  <p>{source.content_snippet}...</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="kb-documents">
        <h2>Your Documents ({documents.length})</h2>
        {loading ? (
          <p>Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="empty-state">
            No documents uploaded yet. Upload one to get started! 📄
          </p>
        ) : (
          <div className="documents-grid">
            {documents.map(doc => (
              <div key={doc.id} className="document-card">
                <div className="doc-icon">📄</div>
                <h4>{doc.title}</h4>
                <p className="doc-meta">
                  Uploaded: {new Date(doc.metadata.upload_date).toLocaleDateString()}
                </p>
                <div className="doc-preview">
                  {doc.content.substring(0, 100)}...
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
