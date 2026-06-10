import React, { useState } from "react";
import { FiDownload, FiLoader, FiCopy, FiCheck } from "react-icons/fi";
import { motion } from "framer-motion";
import { api } from "../api/client";

interface ExportConversationProps {
  conversationId: number;
  messages: any[];
}

export default function ExportConversation({ conversationId, messages }: ExportConversationProps) {
  const [loading, setLoading] = useState(false);
  const [format, setFormat] = useState<"markdown" | "json" | "csv">("markdown");
  const [copied, setCopied] = useState(false);

  const handleExport = async (exportFormat: "markdown" | "json" | "csv") => {
    setLoading(true);
    try {
      const response = await api.get(`/features/export/conversation/${conversationId}`, {
        params: { format: exportFormat },
      });
      const data = response.data;

      const element = document.createElement("a");
      const file = new Blob([data.content], { type: "text/plain" });
      element.href = URL.createObjectURL(file);
      element.download = data.filename;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAll = () => {
    const text = messages
      .map((m) => `${m.role === "user" ? "You" : "Assistant"}: ${m.content}`)
      .join("\n\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2"
    >
      <button
        onClick={() => handleExport("markdown")}
        disabled={loading}
        title="Export as Markdown"
        className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 rounded text-xs text-zinc-300 flex items-center gap-2 transition disabled:opacity-50"
      >
        {loading ? <FiLoader className="animate-spin" size={14} /> : <FiDownload size={14} />}
        MD
      </button>

      <button
        onClick={() => handleExport("json")}
        disabled={loading}
        title="Export as JSON"
        className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 rounded text-xs text-zinc-300 flex items-center gap-2 transition disabled:opacity-50"
      >
        {loading ? <FiLoader className="animate-spin" size={14} /> : <FiDownload size={14} />}
        JSON
      </button>

      <button
        onClick={handleCopyAll}
        title="Copy all messages"
        className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 rounded text-xs text-zinc-300 flex items-center gap-2 transition"
      >
        {copied ? <FiCheck size={14} className="text-green-400" /> : <FiCopy size={14} />}
        Copy
      </button>
    </motion.div>
  );
}
