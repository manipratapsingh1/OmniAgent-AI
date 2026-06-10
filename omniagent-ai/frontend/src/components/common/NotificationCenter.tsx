import React, { useState, useEffect, useRef } from "react";
import { FiX, FiAlertCircle, FiCheckCircle, FiBell, FiInfo } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { notificationService } from "../../api/notificationService";
import { useStore } from "../../store";
import type { Notification } from "../../api/types";

export interface ErrorNotification {
  id: string;
  type: "error" | "success" | "warning";
  message: string;
  duration?: number;
}

interface NotificationCenterProps {
  notifications: ErrorNotification[];
  onDismiss: (id: string) => void;
}

export default function NotificationCenter({
  notifications,
  onDismiss,
}: NotificationCenterProps) {
  const [backendNotifications, setBackendNotifications] = useState<Notification[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const { token } = useStore();
  const isFetchingRef = useRef(false);

  // Load backend notifications only when authenticated
  useEffect(() => {
    if (!token) {
      setBackendNotifications([]);
      return;
    }

    const loadNotifications = async () => {
      if (isFetchingRef.current) {
        return; // Skip if already fetching
      }

      isFetchingRef.current = true;
      try {
        const notifs = await notificationService.getUnread();
        setBackendNotifications(notifs || []);
      } catch (err: any) {
        // Log error but don't show it to user - notifications are optional
        console.debug("Failed to load notifications (non-critical):", err.message);
        // Keep showing previously loaded notifications if available
        if (backendNotifications.length === 0) {
          setBackendNotifications([]);
        }
      } finally {
        isFetchingRef.current = false;
      }
    };

    // Initial load
    loadNotifications();

    // Poll every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, [token]);

  const markAsRead = async (notificationId: number) => {
    try {
      await notificationService.markAsRead(notificationId);
      // Trigger a refresh to get the updated list
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      // Trigger a refresh to get the updated list
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const totalCount = notifications.length + backendNotifications.length;

  return (
    <>
      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 space-y-3 pointer-events-none">
        <AnimatePresence>
          {notifications.map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }}
              className={`p-4 rounded-lg flex items-center gap-3 shadow-lg pointer-events-auto ${
                notification.type === "error"
                  ? "bg-red-900/20 border border-red-500 text-red-200"
                  : notification.type === "success"
                  ? "bg-green-900/20 border border-green-500 text-green-200"
                  : "bg-yellow-900/20 border border-yellow-500 text-yellow-200"
              }`}
            >
              {notification.type === "error" && <FiAlertCircle size={20} />}
              {notification.type === "success" && <FiCheckCircle size={20} />}
              {notification.type === "warning" && <FiAlertCircle size={20} />}
              <span className="flex-1">{notification.message}</span>
              <button
                onClick={() => onDismiss(notification.id)}
                className="hover:opacity-70"
                title="Dismiss notification"
              >
                <FiX size={20} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Notification Bell & Panel */}
      <div className="fixed top-4 right-4 z-40">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowPanel(!showPanel)}
          className="relative p-3 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-zinc-300 hover:text-white transition"
          title="Notifications"
        >
          <FiBell size={24} />
          {totalCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold"
            >
              {totalCount > 9 ? "9+" : totalCount}
            </motion.span>
          )}
        </motion.button>

        {/* Notification Panel */}
        <AnimatePresence>
          {showPanel && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-14 right-0 w-80 max-h-96 bg-slate-900 border border-slate-700 rounded-lg shadow-xl overflow-hidden"
            >
              <div className="p-4 border-b border-slate-700 flex items-center justify-between">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <FiBell size={18} />
                  Notifications
                </h3>
                {backendNotifications.length > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    Clear
                  </button>
                )}
              </div>

              <div className="overflow-y-auto max-h-80">
                {backendNotifications.length === 0 ? (
                  <div className="p-8 text-center text-zinc-500">
                    <FiInfo className="mx-auto mb-2 opacity-50" size={32} />
                    <p>No notifications</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-700">
                    {backendNotifications.map((notif) => (
                      <motion.div
                        key={notif.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="p-4 hover:bg-slate-800/50 transition cursor-pointer"
                        onClick={() => markAsRead(notif.id)}
                      >
                        <p className="text-white text-sm font-medium">
                          {notif.title}
                        </p>
                        <p className="text-zinc-400 text-xs mt-1">
                          {notif.message}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
