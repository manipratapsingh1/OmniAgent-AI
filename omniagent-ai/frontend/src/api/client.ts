import axios, { AxiosError, AxiosRequestConfig } from "axios";

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // ms

export const api = axios.create({ 
  baseURL: "/api/v1",
  timeout: 60000, // Increased from 30s to 60s to handle slower connections and database queries
});

// Request interceptor
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number;
}

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Initialize retry count in config as any to bypass strict Axios types if needed
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (config as any).retryCount = (config as any).retryCount || 0;
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with retry logic
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const config = error.config as any;
    
    // Check if we should retry (for idempotent methods only)
    // Also retry on 410 (Gone) as it may be a transient proxy issue
    const shouldRetry = 
      config &&
      (config.retryCount || 0) < MAX_RETRIES &&
      (error.response?.status === 429 || 
       error.response?.status === 503 || 
       error.response?.status === 410 ||
       !error.response) &&
      (config.method === "get" || config.method === "head");

    if (shouldRetry) {
      config.retryCount = (config.retryCount || 0) + 1;
      const delay = RETRY_DELAY * Math.pow(2, config.retryCount - 1); // Exponential backoff
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(api(config));
        }, delay);
      });
    }

    // Handle 401 - Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

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