import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import './Auth.css';

function Login({ onLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        // ✅ HANDLE ALL TYPES OF BACKEND ERRORS
        let message = 'Login failed';

        if (typeof data === 'string') {
          message = data;
        } else if (data.error) {
          message = data.error;
        } else if (data.detail) {
          if (Array.isArray(data.detail)) {
            message = data.detail[0]?.msg || 'Invalid input';
          } else if (typeof data.detail === 'string') {
            message = data.detail;
          } else {
            message = JSON.stringify(data.detail);
          }
        } else {
          message = JSON.stringify(data);
        }

        throw new Error(message);
      }

      // ✅ SUCCESS
      onLogin(data.user, data.access_token, data.refresh_token);
      navigate('/');

    } catch (err) {
      // ✅ FORCE STRING (fixes [object Object])
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>🚀 OmniAgent AI</h1>
          <p>Advanced Multi-Agent AI System</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2>Welcome Back</h2>

          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Enter your username"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
        </div>
      </div>

      <div className="auth-features">
        <div className="feature-item">
          <span className="feature-icon">🤖</span>
          <span>Multi-Agent AI</span>
        </div>
        <div className="feature-item">
          <span className="feature-icon">📚</span>
          <span>RAG System</span>
        </div>
        <div className="feature-item">
          <span className="feature-icon">🧠</span>
          <span>Long-Term Memory</span>
        </div>
        <div className="feature-item">
          <span className="feature-icon">🛠️</span>
          <span>Tool Integration</span>
        </div>
      </div>
    </div>
  );
}

export default Login;