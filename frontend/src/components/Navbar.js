// frontend/src/components/Navbar.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar({ userId }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          🧠 OmniAgent AI
        </Link>
        <ul className="nav-menu">
          <li className="nav-item">
            <Link to="/" className="nav-link">Dashboard</Link>
          </li>
          <li className="nav-item">
            <Link to="/chat" className="nav-link">💬 Chat</Link>
          </li>
          <li className="nav-item">
            <Link to="/tasks" className="nav-link">✓ Tasks</Link>
          </li>
          <li className="nav-item">
            <Link to="/knowledge" className="nav-link">📚 Knowledge</Link>
          </li>
          <li className="nav-item">
            <Link to="/code" className="nav-link">💻 Code Assistant</Link>
          </li>
          <li className="nav-item">
            <Link to="/settings" className="nav-link">⚙ Settings</Link>
          </li>
        </ul>
        <div className="user-info">
          <small>User: {userId.slice(0, 8)}...</small>
        </div>
      </div>
    </nav>
  );
}
