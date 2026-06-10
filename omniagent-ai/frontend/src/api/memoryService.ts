import { api, getErrorMessage } from "./client";
import type { MemoryEntry } from "./types";

/**
 * Memory Management Service
 */
export const memoryService = {
  /**
   * Store a short-term memory entry
   */
  async storeShortTerm(content: string, ttl?: number): Promise<MemoryEntry> {
    try {
      const response = await api.post<MemoryEntry>("/memory", {
        type: "short_term",
        content,
        ttl,
      });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Store a long-term memory entry
   */
  async storeLongTerm(content: string, embedding?: number[]): Promise<MemoryEntry> {
    try {
      const response = await api.post<MemoryEntry>("/memory", {
        type: "long_term",
        content,
        embedding,
      });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get short-term memory entries
   */
  async getShortTerm(limit: number = 10): Promise<MemoryEntry[]> {
    try {
      const response = await api.get<MemoryEntry[]>("/memory/short-term", {
        params: { limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Get long-term memory entries
   */
  async getLongTerm(limit: number = 50): Promise<MemoryEntry[]> {
    try {
      const response = await api.get<MemoryEntry[]>("/memory/long-term", {
        params: { limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Search memory entries
   */
  async search(query: string, limit: number = 20): Promise<MemoryEntry[]> {
    try {
      const response = await api.get<MemoryEntry[]>("/memory/search", {
        params: { q: query, limit },
      });
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
