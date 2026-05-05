// Frontend Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const API_ENDPOINTS = {
  // Auth
  login: '/api/auth/login',
  register: '/api/auth/register',
  refresh: '/api/auth/refresh',

  // Chat
  chat: '/api/chat',
  chatStream: '/api/chat/stream',
  conversations: '/api/conversations',
  messages: '/api/conversations/{id}/messages',

  // Documents
  uploadDocument: '/api/documents/upload',
  getDocuments: '/api/documents',
  search: '/api/search',

  // Tasks
  tasks: '/api/tasks',
  updateTask: '/api/tasks/{id}',
  deleteTask: '/api/tasks/{id}',

  // Code Analysis
  analyzeCode: '/api/code/analyze',

  // User
  preferences: '/api/preferences',
  stats: '/api/stats',

  // System
  health: '/api/health'
};
