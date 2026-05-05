// frontend/src/pages/ChatInterface.js
import React, { useState, useRef, useEffect } from 'react';
import '../styles/ChatInterface.css';

export default function ChatInterface({ userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useRAG, setUseRAG] = useState(true);
  const [useMemory, setUseMemory] = useState(true);
  const messagesEndRef = useRef(null);
  const conversationId = useRef(`conv_${Date.now()}`);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId.current,
          message: input,
          use_rag: useRAG,
          use_memory: useMemory
        })
      });

      const data = await response.json();
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        executionTime: data.execution_time
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Error occurred. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>🤖 Chat with OmniAgent AI</h1>
        <div className="feature-toggles">
          <label>
            <input
              type="checkbox"
              checked={useRAG}
              onChange={(e) => setUseRAG(e.target.checked)}
            />
            📚 Use Knowledge Base
          </label>
          <label>
            <input
              type="checkbox"
              checked={useMemory}
              onChange={(e) => setUseMemory(e.target.checked)}
            />
            🧠 Use Memory
          </label>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h2>Welcome to OmniAgent AI! 👋</h2>
            <p>I can help you with:</p>
            <ul>
              <li>💬 General questions and conversation</li>
              <li>🔍 Web search and information retrieval</li>
              <li>📚 Knowledge-based answers from your documents</li>
              <li>🧮 Calculations and unit conversions</li>
              <li>💻 Code analysis and suggestions</li>
              <li>📅 Task management and reminders</li>
              <li>🌤️ Real-time information (weather, APIs)</li>
            </ul>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  {msg.sources.map((src, i) => (
                    <div key={i} className="source">
                      📄 {src.document}
                    </div>
                  ))}
                </div>
              )}
              {msg.executionTime && (
                <div className="execution-time">
                  ⏱️ {msg.executionTime.toFixed(2)}s
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything... 🎯"
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading} className="send-btn">
          {loading ? '⏳' : '📤 Send'}
        </button>
      </form>
    </div>
  );
}
