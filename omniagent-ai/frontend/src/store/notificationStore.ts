import { create } from "zustand";
import type { ErrorNotification } from "../components/common/NotificationCenter";

interface NotificationStore {
  notifications: ErrorNotification[];
  addNotification: (notification: Omit<ErrorNotification, "id">) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => {
      const id = `${Date.now()}-${Math.random()}`;
      const newNotification = { ...notification, id };
      const timeout = notification.duration || 5000;

      if (timeout > 0) {
        setTimeout(() => {
          set((s) => ({
            notifications: s.notifications.filter((n) => n.id !== id),
          }));
        }, timeout);
      }

      return { notifications: [...state.notifications, newNotification] };
    }),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearAll: () => set({ notifications: [] }),
}));
