// frontend/src/pages/CodeAssistant.js
import React, { useState } from 'react';
import '../styles/CodeAssistant.css';

export default function CodeAssistant({ userId }) {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisType, setAnalysisType] = useState('full');

  const analyzeCode = async () => {
    if (!code.trim()) {
      alert('Please enter some code first!');
      return;
    }

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/analyze-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
          analysis_type: analysisType
        })
      });

      const data = await res.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Error analyzing code:', error);
      alert('Error analyzing code');
    } finally {
      setLoading(false);
    }
  };

  const explainCode = async () => {
    if (!code.trim()) {
      alert('Please enter some code first!');
      return;
    }

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/explain-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });

      const data = await res.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Error explaining code:', error);
      alert('Error explaining code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="code-assistant">
      <h1>💻 Code Assistant</h1>

      <div className="code-editor-section">
        <div className="editor-header">
          <h2>Code Editor</h2>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="language-select"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="go">Go</option>
          </select>
        </div>

        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste your code here..."
          className="code-textarea"
        />

        <div className="analysis-options">
          <select
            value={analysisType}
            onChange={(e) => setAnalysisType(e.target.value)}
          >
            <option value="full">Full Analysis</option>
            <option value="complexity">Complexity</option>
            <option value="dependencies">Dependencies</option>
            <option value="security">Security</option>
          </select>

          <button onClick={analyzeCode} disabled={loading} className="analyze-btn">
            {loading ? '⏳ Analyzing...' : '🔍 Analyze'}
          </button>
          <button onClick={explainCode} disabled={loading} className="explain-btn">
            {loading ? '⏳ Explaining...' : '📖 Explain'}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="analysis-results">
          <h2>📊 Analysis Results</h2>

          {analysis.analysis && (
            <div className="analysis-card">
              <h3>Code Analysis</h3>
              <p>Syntax Valid: {analysis.analysis.syntax_valid ? '✅' : '❌'}</p>
              {analysis.analysis.complexity && (
                <div>
                  <p>Complexity Rating: <strong>{analysis.analysis.complexity.rating}</strong></p>
                  <p>Cyclomatic Complexity: {analysis.analysis.complexity.cyclomatic_complexity}</p>
                  <p>Lines of Code: {analysis.analysis.complexity.lines_of_code}</p>
                </div>
              )}
            </div>
          )}

          {analysis.suggestions && analysis.suggestions.length > 0 && (
            <div className="suggestions-card">
              <h3>💡 Suggestions</h3>
              {analysis.suggestions.map((suggestion, idx) => (
                <div key={idx} className="suggestion-item">
                  <p>{suggestion}</p>
                </div>
              ))}
            </div>
          )}

          {analysis.explanation && (
            <div className="explanation-card">
              <h3>📖 Code Explanation</h3>
              <p>{analysis.explanation}</p>
            </div>
          )}

          {analysis.refactoring && (
            <div className="refactoring-card">
              <h3>🔄 Refactoring Suggestions</h3>
              {typeof analysis.refactoring === 'string' ? (
                <p>{analysis.refactoring}</p>
              ) : (
                <ul>
                  {(analysis.refactoring.suggestions || []).map((ref, idx) => (
                    <li key={idx}>{ref}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {analysis.external_dependencies && (
            <div className="dependencies-card">
              <h3>📦 External Dependencies</h3>
              {analysis.external_dependencies.length === 0 ? (
                <p>No external dependencies detected</p>
              ) : (
                <ul>
                  {analysis.external_dependencies.map((dep, idx) => (
                    <li key={idx}>{dep}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
