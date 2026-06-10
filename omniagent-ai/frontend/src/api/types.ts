// Core User Models
export interface User { 
  id: number; 
  email: string; 
  full_name?: string; 
  is_admin: boolean;
  is_active?: boolean;
  role?: 'user' | 'moderator' | 'admin';
  api_quota?: number;
  api_used?: number;
  created_at?: string;
  updated_at?: string;
}

// Chat Models
export interface Conversation { 
  id: number; 
  title: string; 
  model?: string; 
  updated_at?: string; 
  is_pinned?: boolean;
  is_shared?: boolean;
  folder_name?: string | null;
}
export interface Message { id: number; role: 'user' | 'assistant'; content: string; sources?: string | Array<string | Citation>; created_at: string; agent?: string; }
export interface Citation { document_id: number; chunk_index: number; snippet: string; filename?: string; }
export interface AgentTrace { agent: string; input: string; output: string; latency_ms: number; }
export interface ChatResponse { conversation_id: number; message_id: number; content: string; sources: Citation[]; trace: AgentTrace[]; }

// Document Management
export interface DocumentItem { id: number; filename: string; mime_type: string; size_bytes: number; status: string; created_at: string; chunk_count?: number; error_message?: string; }

// Task Management
export interface TaskItem { id: number; title: string; description?: string; status: string; priority: number; created_at: string; }

// API Key Management
export interface APIKey {
  id: number;
  user_id: number;
  name: string;
  key_preview?: string; // Last 4 chars masked
  is_active: boolean;
  last_used?: string;
  created_at: string;
  expires_at?: string;
}

export interface CreateAPIKeyResponse {
  key: string; // Raw key, shown only once
  created_at: string;
  expires_at?: string;
}

// Memory Management
export interface MemoryEntry {
  id: number;
  user_id: number;
  memory_type: 'short_term' | 'long_term';
  content: string;
  embedding?: number[];
  created_at: string;
  expires_at?: string;
}

// Notifications
export interface Notification {
  id: number;
  user_id: number;
  notification_type: 'task_update' | 'upload_complete' | 'agent_alert' | 'system';
  title: string;
  message: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

// Background Jobs
export interface BackgroundJob {
  id: number;
  user_id: number;
  job_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  task_id?: string;
  result?: Record<string, unknown>;
  error?: string;
  progress: number;
  created_at: string;
  updated_at: string;
}

// Response Feedback
export interface ResponseFeedback {
  id: number;
  conversation_id: number;
  user_id: number;
  content: string;
  rating?: number;
  helpful?: boolean;
  citations?: string[];
  reasoning_trace?: string;
  created_at: string;
}

export interface FeedbackStats {
  total_responses: number;
  helpful_count: number;
  satisfaction_rate: number;
  average_rating: number;
}

// Quota Information
export interface QuotaInfo {
  quota: number;
  used: number;
  remaining: number;
  usage_percentage: number;
  status: 'ok' | 'warning' | 'exceeded';
}

// Admin Dashboard
export interface AdminOverview {
  total_users?: number;
  active_conversations?: number;
  total_documents?: number;
  total_tasks?: number;
  system_status?: string;
}

export interface AnalyticsDashboard {
  users: { total: number; created_today: number; active: number };
  documents: { total: number; total_size_mb: number; processing: number };
  messages: { total: number; today: number; average_per_conversation: number };
  agents: { total_runs: number; average_latency_ms: number; success_rate: number };
  timestamp: string;
}