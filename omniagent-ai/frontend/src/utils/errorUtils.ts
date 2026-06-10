import axios from "axios";

/**
 * Extract error message from various error types
 */
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    return (
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "An error occurred"
    );
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
};

/**
 * Check if error is a network error
 */
export const isNetworkError = (error: unknown): boolean => {
  if (axios.isAxiosError(error)) {
    return !error.response;
  }
  return false;
};

/**
 * Check if error is a client error (4xx)
 */
export const isClientError = (error: unknown): boolean => {
  if (axios.isAxiosError(error)) {
    return error.response ? error.response.status >= 400 && error.response.status < 500 : false;
  }
  return false;
};

/**
 * Check if error is a server error (5xx)
 */
export const isServerError = (error: unknown): boolean => {
  if (axios.isAxiosError(error)) {
    return error.response ? error.response.status >= 500 : false;
  }
  return false;
};
