import { useState } from "react";
import { api, getErrorMessage } from "../api/client";
import { useNotificationStore } from "../store/notificationStore";
import { FiMoreVertical, FiTrash2, FiDownload, FiAlertTriangle } from "react-icons/fi";
import { exportConversationAsJSON, exportConversationAsMarkdown, downloadFile } from "../utils/exportUtils";
import type { Message } from "../api/types";

interface ConversationMenuProps {
  conversationId: number;
  conversationTitle: string;
  messages?: Message[];
  onDeleted?: () => void;
}

export default function ConversationMenu({ 
  conversationId, 
  conversationTitle, 
  messages = [],
  onDeleted 
}: ConversationMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const handleDelete = async () => {
    try {
      await api.delete(`/conversations/${conversationId}`);
      addNotification({ type: "success", message: "Conversation deleted" });
      onDeleted?.();
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to delete: ${msg}` });
    }
    setShowConfirm(false);
    setIsOpen(false);
  };

  const handleExport = (format: "json" | "markdown") => {
    try {
      const conversation = { id: conversationId, title: conversationTitle, messages };
      let content: string, filename: string, mimeType: string;

      if (format === "json") {
        content = exportConversationAsJSON(conversation);
        filename = `${conversationTitle.replace(/\s+/g, "_")}_${Date.now()}.json`;
        mimeType = "application/json";
      } else {
        content = exportConversationAsMarkdown(conversation);
        filename = `${conversationTitle.replace(/\s+/g, "_")}_${Date.now()}.md`;
        mimeType = "text/markdown";
      }

      downloadFile(filename, content, mimeType);
      addNotification({ type: "success", message: `Exported as ${format.toUpperCase()}` });
      setIsOpen(false);
    } catch (err) {
      addNotification({ type: "error", message: "Export failed" });
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1 hover:bg-slate-800 rounded transition"
        title="Conversation options"
      >
        <FiMoreVertical size={16} className="text-zinc-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-50">
          {!showConfirm ? (
            <>
              <button
                onClick={() => handleExport("json")}
                className="w-full text-left px-4 py-2 text-sm text-zinc-300 hover:bg-slate-700 flex items-center gap-2 border-b border-slate-700"
              >
                <FiDownload size={14} />
                Export as JSON
              </button>
              <button
                onClick={() => handleExport("markdown")}
                className="w-full text-left px-4 py-2 text-sm text-zinc-300 hover:bg-slate-700 flex items-center gap-2 border-b border-slate-700"
              >
                <FiDownload size={14} />
                Export as Markdown
              </button>
              <button
                onClick={() => setShowConfirm(true)}
                className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-900/20 flex items-center gap-2"
              >
                <FiTrash2 size={14} />
                Delete Conversation
              </button>
            </>
          ) : (
            <>
              <div className="px-4 py-3 border-b border-slate-700">
                <div className="flex items-center gap-2 mb-2 text-red-400">
                  <FiAlertTriangle size={16} />
                  <span className="text-sm font-medium">Delete conversation?</span>
                </div>
                <p className="text-xs text-zinc-400">This cannot be undone.</p>
              </div>
              <div className="flex gap-2 p-2">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-3 py-1.5 text-xs rounded bg-slate-700 hover:bg-slate-600 text-zinc-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  className="flex-1 px-3 py-1.5 text-xs rounded bg-red-600 hover:bg-red-500 text-white"
                >
                  Delete
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
