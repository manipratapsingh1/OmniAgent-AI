import { api, getErrorMessage } from "./client";
import type { BackgroundJob } from "./types";

/**
 * Background Job Management Service
 */
export const jobService = {
  /**
   * Get user's background jobs
   */
  async getJobs(skip: number = 0, limit: number = 50): Promise<BackgroundJob[]> {
    try {
      const response = await api.get<BackgroundJob[]>("/jobs", {
        params: { skip, limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get a specific job
   */
  async getJob(jobId: number): Promise<BackgroundJob> {
    try {
      const response = await api.get<BackgroundJob>(`/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Cancel a job
   */
  async cancelJob(jobId: number): Promise<void> {
    try {
      await api.delete(`/jobs/${jobId}`);
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
