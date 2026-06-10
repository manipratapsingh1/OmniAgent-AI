import { api, getErrorMessage } from "./client";
import type { APIKey, CreateAPIKeyResponse } from "./types";

/**
 * API Key Management Service
 */
export const apiKeyService = {
  /**
   * Create a new API key
   */
  async createKey(
    name: string,
    expires_in_days?: number
  ): Promise<CreateAPIKeyResponse> {
    try {
      const response = await api.post<CreateAPIKeyResponse>("/keys", {
        name,
        expires_in_days,
      });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * List all API keys for the current user
   */
  async listKeys(): Promise<APIKey[]> {
    try {
      const response = await api.get<APIKey[]>("/keys");
      return response.data || [];
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  /**
   * Revoke an API key
   */
  async revokeKey(keyId: number): Promise<void> {
    try {
      await api.delete(`/keys/${keyId}`);
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};
