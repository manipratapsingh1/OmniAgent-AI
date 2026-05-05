// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Navbar from './components/Navbar';
import ChatInterface from './pages/ChatInterface';
import Dashboard from './pages/Dashboard';
import TaskManager from './pages/TaskManager';
import KnowledgeBase from './pages/KnowledgeBase';
import CodeAssistant from './pages/CodeAssistant';
import StudyAssistant from './pages/StudyAssistant';
import Settings from './pages/Settings';
import './App.css';

function App() {
  const [auth, setAuth] = useState({
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      setAuth({
        isAuthenticated: true,
        user: JSON.parse(user),
        token,
        refreshToken: localStorage.getItem('refresh_token')
      });
    }
    setLoading(false);
  }, []);

  const handleLogin = (user, token, refreshToken) => {
    setAuth({
      isAuthenticated: true,
      user,
      token,
      refreshToken
    });
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setAuth({
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null
    });
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Loading OmniAgent AI...</p>
      </div>
    );
  }

  return (
    <Router>
      <AuthContext.Provider value={{ auth, setAuth }}>
        {auth.isAuthenticated ? (
          <div className="app authenticated">
            <Navbar user={auth.user} onLogout={handleLogout} />
            <main className="app-main">
              <Routes>
                <Route path="/" element={<Dashboard user={auth.user} />} />
                <Route path="/chat" element={<ChatInterface user={auth.user} token={auth.token} />} />
                <Route path="/tasks" element={<TaskManager user={auth.user} token={auth.token} />} />
                <Route path="/knowledge" element={<KnowledgeBase user={auth.user} token={auth.token} />} />
                <Route path="/code" element={<CodeAssistant user={auth.user} token={auth.token} />} />
                <Route path="/study" element={<StudyAssistant user={auth.user} token={auth.token} />} />
                <Route path="/settings" element={<Settings user={auth.user} token={auth.token} />} />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </main>
          </div>
        ) : (
          <div className="app unauthenticated">
            <Routes>
              <Route path="/login" element={<Login onLogin={handleLogin} />} />
              <Route path="/register" element={<Register onLogin={handleLogin} />} />
              <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
          </div>
        )}
      </AuthContext.Provider>
    </Router>
  );
}

export default App;
