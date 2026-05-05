import React, { useState } from 'react';
import { API_BASE_URL } from '../config';
import './StudyAssistant.css';

function StudyAssistant({ user, token }) {
  const [activeTab, setActiveTab] = useState('subjects');
  const [selectedSubject, setSelectedSubject] = useState('history');
  const [studyMode, setStudyMode] = useState('topics');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const subjects = {
    history: {
      name: 'History',
      topics: ['Ancient India', 'Medieval India', 'Modern India', 'World History'],
      icon: '📚'
    },
    geography: {
      name: 'Geography',
      topics: ['Indian Geography', 'World Geography', 'Physical Geography', 'Economic Geography'],
      icon: '🗺️'
    },
    polity: {
      name: 'Polity & Constitution',
      topics: ['Indian Constitution', 'Government Structure', 'Rights & Duties', 'Parliament'],
      icon: '⚖️'
    },
    economy: {
      name: 'Economy',
      topics: ['Microeconomics', 'Macroeconomics', 'Indian Economy', 'Development'],
      icon: '💰'
    },
    science: {
      name: 'Science & Technology',
      topics: ['Physics', 'Chemistry', 'Biology', 'Biotechnology'],
      icon: '🔬'
    },
    current_affairs: {
      name: 'Current Affairs',
      topics: ['National News', 'International News', 'Business', 'Sports & Culture'],
      icon: '📰'
    }
  };

  const handleStudyQuery = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          conversation_id: `study_${Date.now()}`,
          message: `UPSC/CDS Context: ${selectedSubject.toUpperCase()} - ${question}`,
          use_memory: true,
          use_rag: true
        })
      });

      const data = await response.json();
      setAnswer(data.response);
    } catch (error) {
      setAnswer(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="study-assistant">
      <div className="study-header">
        <h1>🎓 AI Study Assistant</h1>
        <p>Master UPSC & CDS Exam Preparation</p>
      </div>

      <div className="study-tabs">
        <button 
          className={`tab-btn ${activeTab === 'subjects' ? 'active' : ''}`}
          onClick={() => setActiveTab('subjects')}
        >
          📖 Subjects
        </button>
        <button 
          className={`tab-btn ${activeTab === 'practice' ? 'active' : ''}`}
          onClick={() => setActiveTab('practice')}
        >
          ✏️ Practice Questions
        </button>
        <button 
          className={`tab-btn ${activeTab === 'notes' ? 'active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          📝 Study Notes
        </button>
        <button 
          className={`tab-btn ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => setActiveTab('resources')}
        >
          📚 Resources
        </button>
      </div>

      {activeTab === 'subjects' && (
        <div className="study-content">
          <div className="subjects-grid">
            {Object.entries(subjects).map(([key, subject]) => (
              <div 
                key={key}
                className={`subject-card ${selectedSubject === key ? 'active' : ''}`}
                onClick={() => setSelectedSubject(key)}
              >
                <span className="subject-icon">{subject.icon}</span>
                <h3>{subject.name}</h3>
                <div className="topics-list">
                  {subject.topics.map((topic, idx) => (
                    <span key={idx} className="topic-tag">{topic}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="study-tool">
            <h2>Ask Your Study Question</h2>
            <div className="study-query">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={`Ask about ${subjects[selectedSubject].name}...`}
                rows="4"
              />
              <button 
                className="btn-query"
                onClick={handleStudyQuery}
                disabled={loading}
              >
                {loading ? '🔄 Analyzing...' : '📖 Get Answer'}
              </button>
            </div>

            {answer && (
              <div className="study-answer">
                <h3>📖 Answer</h3>
                <div className="answer-content">{answer}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'practice' && (
        <div className="study-content">
          <h2>Practice Questions</h2>
          <div className="practice-section">
            <div className="difficulty-selector">
              <button className="diff-btn">🟢 Easy</button>
              <button className="diff-btn">🟡 Medium</button>
              <button className="diff-btn">🔴 Hard</button>
            </div>
            <div className="question-counter">
              <span>Question 1 of 10</span>
              <div className="progress-bar">
                <div className="progress" style={{width: '10%'}}></div>
              </div>
            </div>
            <div className="question-content">
              <p>Sample Question: Which of the following is NOT a fundamental right under the Indian Constitution?</p>
              <div className="options">
                <label><input type="radio" name="answer" /> Right to Education</label>
                <label><input type="radio" name="answer" /> Right to Vote</label>
                <label><input type="radio" name="answer" /> Right to Equality</label>
                <label><input type="radio" name="answer" /> Right to Information</label>
              </div>
              <button className="btn-submit">Submit Answer</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'notes' && (
        <div className="study-content">
          <h2>Study Notes</h2>
          <div className="notes-section">
            <div className="note-card">
              <h3>📌 Indian Constitution - Key Points</h3>
              <p>• Adopted on 26 January 1950</p>
              <p>• Longest written constitution in the world</p>
              <p>• 448 Articles and 12 Schedules (as per original)</p>
              <p>• Drafted by Dr. B.R. Ambedkar</p>
            </div>
            <div className="note-card">
              <h3>📌 Fundamental Rights</h3>
              <p>• Right to Equality (Article 14-18)</p>
              <p>• Right to Freedom (Article 19-22)</p>
              <p>• Right against Exploitation (Article 23-24)</p>
              <p>• Right to Freedom of Religion (Article 25-28)</p>
            </div>
            <div className="note-card">
              <h3>📌 Directive Principles</h3>
              <p>• Non-justiciable social welfare policies</p>
              <p>• Guide for the state</p>
              <p>• Aim to create a welfare state</p>
              <p>• Include right to education, health, etc.</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'resources' && (
        <div className="study-content">
          <h2>Learning Resources</h2>
          <div className="resources-grid">
            <div className="resource-card">
              <span className="resource-icon">🎥</span>
              <h3>Video Lectures</h3>
              <p>High-quality video tutorials covering all topics</p>
            </div>
            <div className="resource-card">
              <span className="resource-icon">📖</span>
              <h3>E-Books</h3>
              <p>Comprehensive study materials in PDF format</p>
            </div>
            <div className="resource-card">
              <span className="resource-icon">🧪</span>
              <h3>Mock Tests</h3>
              <p>Real exam patterns with instant feedback</p>
            </div>
            <div className="resource-card">
              <span className="resource-icon">💬</span>
              <h3>Discussion Forum</h3>
              <p>Connect with other aspirants and mentors</p>
            </div>
            <div className="resource-card">
              <span className="resource-icon">📊</span>
              <h3>Progress Tracking</h3>
              <p>Monitor your preparation with detailed analytics</p>
            </div>
            <div className="resource-card">
              <span className="resource-icon">⚡</span>
              <h3>Quick Revisions</h3>
              <p>Last-minute notes and key takeaways</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StudyAssistant;
