import { useEffect, useRef, useState } from "react";

interface PollingOptions<T> {
  interval: number;
  enabled?: boolean;
  onError?: (error: unknown) => void;
  initialData?: T;
}

/**
 * Smart polling hook that:
 * 1. Prevents simultaneous duplicate requests
 * 2. Only polls when enabled
 * 3. Handles errors gracefully
 * 4. Manages intervals properly
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  options: PollingOptions<T>
): { data: T | null; loading: boolean; error: unknown | null; refetch: () => Promise<void> } {
  const { interval, enabled = true, onError, initialData } = options;
  const [data, setData] = useState<T | null>(initialData ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown | null>(null);
  const isFetchingRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = async () => {
    // Prevent simultaneous duplicate requests
    if (isFetchingRef.current) {
      return;
    }

    isFetchingRef.current = true;
    setLoading(true);
    try {
      const result = await fetcher();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
      onError?.(err);
    } finally {
      isFetchingRef.current = false;
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Initial fetch
    fetch();

    // Setup polling
    intervalRef.current = setInterval(fetch, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval, enabled]);

  return { data, loading, error, refetch: fetch };
}
