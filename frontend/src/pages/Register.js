import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import './Auth.css';

function Register({ onLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const username = formData.username.trim();
    const email = formData.email.trim();
    const fullName = formData.full_name.trim();
    const password = formData.password;
    const confirmPassword = formData.confirmPassword;

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // ✅ HANDLE ALL TYPES OF BACKEND ERRORS
        let message = 'Registration failed';

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
          <h2>Create Account</h2>

          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choose a username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="full_name">Full Name</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Your full name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a strong password"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm your password"
              required
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account? <Link to="/login">Login</Link>
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

export default Register;