import { api, getErrorMessage } from "./client";
import type { FeedbackStats } from "./types";

/**
 * Feedback Management Service
 */
export const feedbackService = {
  /**
   * Submit feedback on a response
   */
  async submitFeedback(
    helpful: boolean,
    rating?: number,
    responseId?: number
  ): Promise<void> {
    try {
      await api.post("/feedback", {
        helpful,
        rating,
        response_id: responseId,
      });
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get feedback statistics
   */
  async getStats(): Promise<FeedbackStats> {
    try {
      const response = await api.get<FeedbackStats>("/feedback/stats");
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
