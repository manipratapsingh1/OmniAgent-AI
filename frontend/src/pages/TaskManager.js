// frontend/src/pages/TaskManager.js
import React, { useState, useEffect } from 'react';
import '../styles/TaskManager.css';

export default function TaskManager({ userId }) {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 3,
    due_date: ''
  });
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasks();
  }, [userId, filter]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const status = filter === 'all' ? null : filter;
      const url = status
        ? `http://localhost:8000/tasks/${userId}?status=${status}`
        : `http://localhost:8000/tasks/${userId}`;

      const res = await fetch(url);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTask = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`http://localhost:8000/tasks/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTask)
      });
      const created = await res.json();
      setTasks([created, ...tasks]);
      setNewTask({ title: '', description: '', priority: 3, due_date: '' });
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const updateTaskStatus = async (taskId, newStatus) => {
    try {
      await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      loadTasks();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'DELETE'
      });
      setTasks(tasks.filter(t => t.id !== taskId));
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  const getPriorityLabel = (priority) => {
    const labels = { 1: '🔴 High', 2: '🟡 Medium', 3: '🟢 Low' };
    return labels[priority] || 'Normal';
  };

  return (
    <div className="task-manager">
      <h1>✓ Task Manager</h1>

      <div className="task-creation">
        <h2>Create New Task</h2>
        <form onSubmit={createTask} className="task-form">
          <input
            type="text"
            placeholder="Task title..."
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            required
          />
          <textarea
            placeholder="Description (optional)"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
          />
          <div className="form-row">
            <select
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: parseInt(e.target.value) })}
            >
              <option value={1}>🔴 High Priority</option>
              <option value={2}>🟡 Medium Priority</option>
              <option value={3}>🟢 Low Priority</option>
            </select>
            <input
              type="date"
              value={newTask.due_date}
              onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
            />
            <button type="submit">+ Add Task</button>
          </div>
        </form>
      </div>

      <div className="task-filters">
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All Tasks
        </button>
        <button
          className={filter === 'pending' ? 'active' : ''}
          onClick={() => setFilter('pending')}
        >
          Pending
        </button>
        <button
          className={filter === 'in_progress' ? 'active' : ''}
          onClick={() => setFilter('in_progress')}
        >
          In Progress
        </button>
        <button
          className={filter === 'completed' ? 'active' : ''}
          onClick={() => setFilter('completed')}
        >
          Completed
        </button>
      </div>

      <div className="tasks-list">
        {loading ? (
          <p>Loading tasks...</p>
        ) : tasks.length === 0 ? (
          <p className="empty-state">No tasks. Create one to get started! 🚀</p>
        ) : (
          tasks.map(task => (
            <div key={task.id} className="task-card">
              <div className="task-header">
                <h3>{task.title}</h3>
                <span className={`priority ${task.priority}`}>
                  {getPriorityLabel(task.priority)}
                </span>
              </div>
              <p className="task-description">{task.description}</p>
              {task.due_date && (
                <p className="task-due">📅 Due: {new Date(task.due_date).toLocaleDateString()}</p>
              )}
              <div className="task-actions">
                <select
                  value={task.status}
                  onChange={(e) => updateTaskStatus(task.id, e.target.value)}
                  className="status-select"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="delete-btn"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
