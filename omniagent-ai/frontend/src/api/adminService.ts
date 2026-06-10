import { api, getErrorMessage } from "./client";
import type { QuotaInfo, AnalyticsDashboard, User } from "./types";

/**
 * Quota Management Service
 */
export const quotaService = {
  /**
   * Get user's quota status
   */
  async getQuota(): Promise<QuotaInfo> {
    try {
      const response = await api.get<QuotaInfo>("/quota");
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};

/**
 * Admin Service
 */
export const adminService = {
  /**
   * Get full dashboard with all analytics
   */
  async getDashboard(): Promise<AnalyticsDashboard> {
    try {
      const response = await api.get<AnalyticsDashboard>("/admin/dashboard");
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get user analytics
   */
  async getUserAnalytics(): Promise<Record<string, unknown>> {
    try {
      const response = await api.get<Record<string, unknown>>("/admin/analytics/users");
      return response.data || {};
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get document analytics
   */
  async getDocumentAnalytics(): Promise<Record<string, unknown>> {
    try {
      const response = await api.get<Record<string, unknown>>("/admin/analytics/documents");
      return response.data || {};
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get message analytics
   */
  async getMessageAnalytics(): Promise<Record<string, unknown>> {
    try {
      const response = await api.get<Record<string, unknown>>("/admin/analytics/messages");
      return response.data || {};
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get agent analytics
   */
  async getAgentAnalytics(): Promise<Record<string, unknown>> {
    try {
      const response = await api.get<Record<string, unknown>>("/admin/analytics/agents");
      return response.data || {};
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * List all users
   */
  async listUsers(skip: number = 0, limit: number = 50): Promise<User[]> {
    try {
      const response = await api.get<User[]>("/admin/users", {
        params: { skip, limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Change user role
   */
  async changeUserRole(userId: number, role: 'user' | 'moderator' | 'admin'): Promise<User> {
    try {
      const response = await api.put<User>(`/admin/users/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Update user quota
   */
  async updateUserQuota(userId: number, quota: number): Promise<User> {
    try {
      const response = await api.put<User>(`/admin/users/${userId}/quota`, { quota });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Toggle user active status
   */
  async toggleUserActive(userId: number, isActive?: boolean): Promise<User> {
    try {
      const response = await api.put<User>(`/admin/users/${userId}/toggle-active`, isActive !== undefined ? { is_active: isActive } : {});
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};

/**
 * Search Service
 */
export const searchService = {
  /**
   * Search conversations
   */
  async searchConversations(query: string, limit: number = 20): Promise<unknown[]> {
    try {
      const response = await api.get<unknown[]>("/search/conversations", {
        params: { q: query, limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Search messages
   */
  async searchMessages(query: string, limit: number = 50): Promise<unknown[]> {
    try {
      const response = await api.get<unknown[]>("/search/messages", {
        params: { q: query, limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
