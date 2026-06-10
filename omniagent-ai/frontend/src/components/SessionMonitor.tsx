import { useEffect, useState } from "react";
import { useStore } from "../store";
import { useNotificationStore } from "../store/notificationStore";
import { FiAlertTriangle } from "react-icons/fi";

/**
 * Component that monitors user activity and warns about session expiration
 * Default timeout: 60 minutes
 */
export default function SessionMonitor() {
  const { token, setToken } = useStore();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [warned, setWarned] = useState(false);
  
  const IDLE_TIMEOUT = 60 * 60 * 1000; // 60 minutes
  const WARNING_BEFORE = 5 * 60 * 1000; // Warn 5 minutes before

  useEffect(() => {
    if (!token) return;

    let timeoutId: ReturnType<typeof setTimeout>;
    let warningId: ReturnType<typeof setTimeout>;
    
    const resetTimers = () => {
      setWarned(false);
      clearTimeout(timeoutId);
      clearTimeout(warningId);
      
      // Warn 55 minutes in
      warningId = setTimeout(() => {
        if (!warned) {
          setWarned(true);
          addNotification({
            type: "warning",
            message: "Your session will expire in 5 minutes. Please save your work.",
            duration: 10000
          });
        }
      }, IDLE_TIMEOUT - WARNING_BEFORE);

      // Logout at 60 minutes
      timeoutId = setTimeout(() => {
        setToken(null);
        localStorage.removeItem("token");
        addNotification({
          type: "error",
          message: "Session expired. Please log in again."
        });
        window.location.href = "/login";
      }, IDLE_TIMEOUT);
    };

    resetTimers();

    // Reset timers on user activity
    const events = ["mousedown", "keydown", "scroll", "touchstart"];
    const handlers = events.map((event) =>
      document.addEventListener(event, resetTimers, true)
    );

    return () => {
      clearTimeout(timeoutId);
      clearTimeout(warningId);
      events.forEach((event) => document.removeEventListener(event, resetTimers, true));
    };
  }, [token, warned, setToken, addNotification]);

  return null;
}
