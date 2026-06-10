import { api, getErrorMessage } from "./client";
import type { Notification } from "./types";

/**
 * Notification Management Service
 */
export const notificationService = {
  /**
   * Get unread notifications
   */
  async getUnread(): Promise<Notification[]> {
    try {
      const response = await api.get<Notification[]>("/notifications");
      return response.data || [];
    } catch (error: any) {
      // Log full error details for debugging
      const errorMsg = getErrorMessage(error);
      const statusCode = error.response?.status;
      const errorDetail = error.response?.data?.detail;
      
      console.warn("Notification API error:", { 
        statusCode, 
        errorDetail, 
        errorMsg,
        url: error.response?.config?.url 
      });
      
      // Return empty list instead of throwing - notifications are nice-to-have, not critical
      if (statusCode === 401 || statusCode === 403 || statusCode === 410) {
        console.debug("Notifications unavailable (auth/permission issue)");
        return [];
      }
      
      throw new Error(errorMsg);
    }
  },

  /**
   * Mark a notification as read
   */
  async markAsRead(notificationId: number): Promise<void> {
    try {
      await api.put(`/notifications/${notificationId}/read`);
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    try {
      await api.put("/notifications/read-all");
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
