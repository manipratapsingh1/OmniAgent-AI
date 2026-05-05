// frontend/src/pages/Settings.js
import React, { useState, useEffect } from 'react';
import '../styles/Settings.css';

export default function Settings({ userId }) {
  const [preferences, setPreferences] = useState({
    tone: 'professional',
    expertise_level: 'intermediate',
    preferred_tools: ['web_search', 'calculator'],
    custom_instructions: ''
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, [userId]);

  const loadPreferences = async () => {
    try {
      const res = await fetch(`http://localhost:8000/preferences/${userId}`);
      const data = await res.json();
      if (data.preferences) {
        setPreferences(data.preferences);
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const savePreferences = async () => {
    try {
      setLoading(true);
      setSaved(false);

      const res = await fetch(`http://localhost:8000/preferences/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
      });

      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Error saving preferences');
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = (tool) => {
    setPreferences(prev => ({
      ...prev,
      preferred_tools: prev.preferred_tools.includes(tool)
        ? prev.preferred_tools.filter(t => t !== tool)
        : [...prev.preferred_tools, tool]
    }));
  };

  return (
    <div className="settings">
      <h1>⚙️ Settings</h1>

      <div className="settings-card">
        <h2>Personalization</h2>

        <div className="setting-group">
          <label>🎯 Conversation Tone</label>
          <select
            value={preferences.tone}
            onChange={(e) => setPreferences({ ...preferences, tone: e.target.value })}
          >
            <option value="casual">Casual & Friendly</option>
            <option value="professional">Professional</option>
            <option value="technical">Technical</option>
            <option value="educational">Educational</option>
          </select>
          <p className="help-text">How you'd like the AI to respond</p>
        </div>

        <div className="setting-group">
          <label>📚 Expertise Level</label>
          <select
            value={preferences.expertise_level}
            onChange={(e) => setPreferences({ ...preferences, expertise_level: e.target.value })}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert</option>
          </select>
          <p className="help-text">Adjusts complexity of explanations</p>
        </div>

        <div className="setting-group">
          <label>🛠️ Preferred Tools</label>
          <div className="tools-grid">
            {[
              { id: 'web_search', label: '🔍 Web Search' },
              { id: 'calculator', label: '🧮 Calculator' },
              { id: 'weather', label: '🌤️ Weather' },
              { id: 'code_execution', label: '💻 Code Execution' },
              { id: 'unit_conversion', label: '📏 Unit Conversion' },
              { id: 'api_calls', label: '🔗 API Calls' }
            ].map(tool => (
              <label key={tool.id} className="tool-checkbox">
                <input
                  type="checkbox"
                  checked={preferences.preferred_tools.includes(tool.id)}
                  onChange={() => toggleTool(tool.id)}
                />
                {tool.label}
              </label>
            ))}
          </div>
        </div>

        <div className="setting-group">
          <label>📝 Custom Instructions</label>
          <textarea
            value={preferences.custom_instructions}
            onChange={(e) => setPreferences({ ...preferences, custom_instructions: e.target.value })}
            placeholder="Add any custom instructions or preferences..."
            rows="4"
          />
          <p className="help-text">Special instructions for the AI to follow</p>
        </div>

        <div className="settings-actions">
          <button onClick={savePreferences} disabled={loading} className="save-btn">
            {loading ? '💾 Saving...' : '💾 Save Preferences'}
          </button>
          {saved && <span className="save-indicator">✅ Preferences saved!</span>}
        </div>
      </div>

      <div className="settings-card">
        <h2>Account Information</h2>
        <div className="info-group">
          <label>User ID:</label>
          <code>{userId}</code>
        </div>
        <div className="info-group">
          <label>Theme:</label>
          <select defaultValue="light">
            <option value="light">Light Mode</option>
            <option value="dark">Dark Mode</option>
          </select>
        </div>
        <div className="info-group">
          <label>Notifications:</label>
          <input type="checkbox" defaultChecked /> Enable notifications
        </div>
      </div>

      <div className="settings-card">
        <h2>About OmniAgent</h2>
        <div className="about">
          <h3>Version 1.0.0</h3>
          <p>Advanced AI system with:</p>
          <ul>
            <li>🤖 Multi-Agent Intelligence</li>
            <li>🧠 Long-Term Memory System</li>
            <li>📚 RAG Knowledge Base</li>
            <li>🛠️ Tool Integration</li>
            <li>📅 Task Automation</li>
            <li>💻 Developer Assistant</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
