import { useEffect, useState } from "react";
import { api, getErrorMessage } from "../api/client";
import { useNotificationStore } from "../store/notificationStore";

interface UseFetchOptions {
  skip?: boolean;
  refetchInterval?: number;
  showError?: boolean;
}

interface UseFetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useFetch<T>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchState<T> {
  const { skip = false, refetchInterval, showError = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!skip);
  const [error, setError] = useState<string | null>(null);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const fetchData = async () => {
    if (skip) return;
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<T>(url);
      setData(response.data);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      setError(errorMsg);
      if (showError) {
        addNotification({ type: "error", message: errorMsg });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    if (refetchInterval) {
      const interval = setInterval(fetchData, refetchInterval);
      return () => clearInterval(interval);
    }
  }, [url, skip]);

  return { data, loading, error, refetch: fetchData };
}

interface UsePostOptions {
  showSuccess?: boolean;
  showError?: boolean;
}

export function usePost<T, D>(options: UsePostOptions = {}) {
  const { showSuccess = true, showError = true } = options;
  const [loading, setLoading] = useState(false);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const post = async (url: string, data: D): Promise<T | null> => {
    try {
      setLoading(true);
      const response = await api.post<T>(url, data);
      if (showSuccess) {
        addNotification({ type: "success", message: "Operation successful" });
      }
      return response.data;
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      if (showError) {
        addNotification({ type: "error", message: errorMsg });
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { post, loading };
}
