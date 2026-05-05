// frontend/src/pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import '../styles/Dashboard.css';

export default function Dashboard({ userId }) {
  const [stats, setStats] = useState({
    totalChats: 0,
    tasksCompleted: 0,
    documentsUploaded: 0,
    remindersSet: 0
  });
  const [recentTasks, setRecentTasks] = useState([]);
  const [upcomingReminders, setUpcomingReminders] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, [userId]);

  const loadDashboardData = async () => {
    try {
      // Load tasks
      const tasksRes = await fetch(`http://localhost:8000/tasks/${userId}`);
      const tasksData = await tasksRes.json();
      setRecentTasks(tasksData.tasks?.slice(0, 5) || []);

      // Load reminders
      const remindersRes = await fetch(`http://localhost:8000/reminders/${userId}`);
      const remindersData = await remindersRes.json();
      setUpcomingReminders(remindersData.reminders?.slice(0, 5) || []);

      // Load knowledge base
      const kbRes = await fetch(`http://localhost:8000/knowledge-base/${userId}`);
      const kbData = await kbRes.json();

      setStats({
        totalChats: parseInt(localStorage.getItem('chatCount') || '0'),
        tasksCompleted: tasksData.tasks?.filter(t => t.status === 'completed').length || 0,
        documentsUploaded: kbData.documents?.length || 0,
        remindersSet: remindersData.reminders?.length || 0
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  return (
    <div className="dashboard">
      <h1>📊 Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">💬</div>
          <div className="stat-content">
            <h3>Total Chats</h3>
            <p className="stat-value">{stats.totalChats}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <h3>Tasks Completed</h3>
            <p className="stat-value">{stats.tasksCompleted}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📚</div>
          <div className="stat-content">
            <h3>Documents Uploaded</h3>
            <p className="stat-value">{stats.documentsUploaded}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔔</div>
          <div className="stat-content">
            <h3>Reminders Set</h3>
            <p className="stat-value">{stats.remindersSet}</p>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>📅 Recent Tasks</h2>
          <div className="task-list">
            {recentTasks.length === 0 ? (
              <p className="empty-state">No tasks yet. Create one! 🎯</p>
            ) : (
              recentTasks.map(task => (
                <div key={task.id} className="task-item">
                  <div className="task-info">
                    <h4>{task.title}</h4>
                    <p>{task.description}</p>
                  </div>
                  <span className={`status ${task.status}`}>{task.status}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="dashboard-section">
          <h2>🔔 Upcoming Reminders</h2>
          <div className="reminders-list">
            {upcomingReminders.length === 0 ? (
              <p className="empty-state">No reminders. Set one! 📬</p>
            ) : (
              upcomingReminders.map(reminder => (
                <div key={reminder.id} className="reminder-item">
                  <p>{reminder.message}</p>
                  <small>{new Date(reminder.trigger_time).toLocaleString()}</small>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="features-overview">
        <h2>✨ OmniAgent Features</h2>
        <div className="features-grid">
          <div className="feature">
            <h3>🤖 Multi-Agent Intelligence</h3>
            <p>Planner, Executor, Verifier working together</p>
          </div>
          <div className="feature">
            <h3>🧠 Long-Term Memory</h3>
            <p>Remembers preferences and past conversations</p>
          </div>
          <div className="feature">
            <h3>📚 RAG Knowledge Base</h3>
            <p>Upload PDFs and get smart answers</p>
          </div>
          <div className="feature">
            <h3>🛠️ Tool Integration</h3>
            <p>Calculator, web search, APIs, weather</p>
          </div>
          <div className="feature">
            <h3>📅 Task Automation</h3>
            <p>Manage tasks, schedules, and reminders</p>
          </div>
          <div className="feature">
            <h3>💻 Code Assistant</h3>
            <p>Analyze, explain, and improve code</p>
          </div>
        </div>
      </div>
    </div>
  );
}
