import { useEffect, useState } from "react";
import { api, getErrorMessage } from "../api/client";
import { useStore } from "../store";
import type { User } from "../api/types";
import { useNotificationStore } from "../store/notificationStore";

interface UseAuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
  logout: () => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
}

export function useAuth(): UseAuthState {
  const { token, setToken } = useStore();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addNotification = useNotificationStore((s) => s.addNotification);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then((r) => {
        setUser(r.data);
        setError(null);
      })
      .catch((err) => {
        const msg = getErrorMessage(err);
        setError(msg);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      const response = await api.post("/auth/login", { email, password });
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem("token", response.data.access_token);
      addNotification({ type: "success", message: "Login successful" });
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
      addNotification({ type: "error", message: msg });
      throw err;
    }
  };

  const signup = async (email: string, password: string, fullName: string) => {
    try {
      setError(null);
      const response = await api.post("/auth/signup", {
        email,
        password,
        full_name: fullName,
      });
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem("token", response.data.access_token);
      addNotification({ type: "success", message: "Signup successful" });
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
      addNotification({ type: "error", message: msg });
      throw err;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    addNotification({ type: "success", message: "Logged out successfully" });
  };

  return { token, user, loading, error, logout, login, signup };
}