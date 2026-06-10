import { useEffect, useState } from "react";
import { api, getErrorMessage } from "../api/client";
import { useNotificationStore } from "../store/notificationStore";
import { FiPlus, FiLoader, FiTrash2 } from "react-icons/fi";
import { motion } from "framer-motion";
import type { TaskItem } from "../api/types";

export default function TaskDashboard() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [addingTask, setAddingTask] = useState(false);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const load = async () => {
    try {
      setLoading(true);
      const r = await api.get<TaskItem[]>("/tasks/");
      setTasks(r.data || []);
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to load tasks: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!title.trim()) {
      addNotification({ type: "warning", message: "Task title cannot be empty" });
      return;
    }
    try {
      setAddingTask(true);
      await api.post("/tasks/", { title, priority: 3 });
      setTitle("");
      addNotification({ type: "success", message: "Task created successfully" });
      await load();
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to create task: ${msg}` });
    } finally {
      setAddingTask(false);
    }
  };

  const setStatus = async (id: number, status: string) => {
    try {
      await api.patch(`/tasks/${id}/status?status=${status}`);
      addNotification({ type: "success", message: "Task status updated" });
      await load();
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to update task: ${msg}` });
    }
  };

  const deleteTask = async (id: number) => {
    try {
      await api.delete(`/tasks/${id}`);
      addNotification({ type: "success", message: "Task deleted successfully" });
      await load();
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to delete task: ${msg}` });
    }
  };

  const statusColors = {
    pending: "bg-yellow-500/20 text-yellow-300",
    in_progress: "bg-blue-500/20 text-blue-300",
    done: "bg-green-500/20 text-green-300",
    failed: "bg-red-500/20 text-red-300",
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && add()}
          placeholder="New task…"
          className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={add}
          disabled={addingTask}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white flex items-center gap-2 transition"
        >
          {addingTask ? <FiLoader className="animate-spin" /> : <FiPlus />}
          Add
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-8 text-zinc-400">
          <FiLoader className="animate-spin mr-2" /> Loading tasks...
        </div>
      ) : tasks.length === 0 ? (
        <div className="p-8 text-center text-zinc-500">No tasks yet. Create one to get started!</div>
      ) : (
        <ul className="space-y-2">
          {tasks.map((t, idx) => (
            <li key={t.id}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center justify-between bg-slate-800/50 backdrop-blur border border-slate-700 rounded p-3 hover:bg-slate-800 transition"
              >
              <div className="flex-1">
                <div className="font-medium text-white">{t.title}</div>
                <div className="flex gap-2 items-center mt-1">
                  <span className="text-xs bg-slate-700 px-2 py-1 rounded">
                    Priority: {t.priority}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${statusColors[t.status as keyof typeof statusColors] || "bg-slate-700"}`}>
                    {t.status}
                  </span>
                </div>
              </div>
              <select
                title="Change task status"
                value={t.status}
                onChange={(e) => setStatus(t.id, e.target.value)}
                className="bg-slate-700 rounded px-2 py-1 text-sm text-white border border-slate-600 focus:outline-none focus:border-blue-500 mr-2"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
                <option value="failed">Failed</option>
              </select>
              <button
                title="Delete task"
                onClick={() => deleteTask(t.id)}
                className="p-2 rounded hover:bg-red-500/20 transition text-red-400"
              >
                <FiTrash2 size={18} />
              </button>
            </motion.div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}