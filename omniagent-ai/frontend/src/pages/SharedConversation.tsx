import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, getErrorMessage } from "../api/client";
import MessageBubble from "../components/chat/MessageBubble";
import Loading from "../components/common/Loading";
import { motion } from "framer-motion";
import { FiHome, FiAlertCircle, FiArrowRight } from "react-icons/fi";

interface SharedMessage {
  role: string;
  content: string;
  created_at?: string;
}

interface SharedConversationData {
  title: string;
  created_at: string;
  messages: SharedMessage[];
}

export default function SharedConversation() {
  const { shareToken } = useParams<{ shareToken: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SharedConversationData | null>(null);

  useEffect(() => {
    async function fetchSharedConversation() {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<SharedConversationData>(
          `/tools/shared-conversation/${shareToken}`
        );
        setData(response.data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    if (shareToken) {
      fetchSharedConversation();
    }
  }, [shareToken]);

  // Set document title dynamically
  useEffect(() => {
    if (data?.title) {
      document.title = `${data.title} | Shared Conversation | OmniAgent AI`;
    } else {
      document.title = "Shared Conversation | OmniAgent AI";
    }
  }, [data]);

  if (loading) {
    return <Loading message="Retrieving shared conversation..." fullScreen />;
  }

  if (error || !data) {
    return (
      <div className="w-full h-screen bg-slate-950 flex items-center justify-center p-6 mesh-bg">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full glass-panel border border-slate-700/40 p-8 text-center"
        >
          <div className="w-16 h-16 bg-red-500/10 border border-red-500/20 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-glow-sm">
            <FiAlertCircle size={32} />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Invalid or Expired Link</h2>
          <p className="text-slate-400 text-sm mb-6 leading-relaxed">
            {error || "The shared conversation link is invalid, expired, or may have been deleted by the owner."}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/"
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-all border border-slate-700/50 flex items-center justify-center gap-2"
            >
              <FiHome size={16} />
              Go Home
            </Link>
            <Link
              to="/login"
              className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/15"
            >
              Login
              <FiArrowRight size={16} />
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  const formatCreationDate = (isoString?: string) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleDateString([], {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="w-full h-screen bg-slate-950 flex flex-col overflow-hidden mesh-bg">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-700/40 bg-slate-950/90 backdrop-blur-md flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-sm border border-white/10">
              <span className="text-white font-extrabold text-sm tracking-tighter">Ω</span>
            </div>
            <span className="font-bold text-white text-lg tracking-wider hidden sm:inline-block">
              OMNIAGENT <span className="text-blue-500 font-medium">AI</span>
            </span>
          </Link>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-bold uppercase tracking-wider border border-slate-700/50">
            Shared Session
          </span>
        </div>
        <div>
          <Link
            to="/signup"
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-blue-500/15 flex items-center gap-1.5"
          >
            Create Your Account
            <FiArrowRight size={12} />
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-8 flex justify-center scrollbar-thin">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-4xl w-full flex flex-col h-full"
        >
          {/* Conversation Metadata Info */}
          <div className="glass-panel border border-slate-700/40 p-6 mb-6 rounded-2xl bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-1">
                Conversation Title
              </p>
              <h1 className="text-2xl font-bold text-white tracking-tight leading-snug">
                {data.title}
              </h1>
              <p className="text-slate-400 text-xs mt-1.5 flex items-center gap-1.5">
                <span>Shared on:</span>
                <span className="text-slate-300 font-medium">
                  {formatCreationDate(data.created_at)}
                </span>
              </p>
            </div>
            <div className="flex items-center">
              <span className="px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold flex items-center gap-2">
                🔒 Read-Only Archive
              </span>
            </div>
          </div>

          {/* Message List Panel */}
          <div className="flex-1 glass-panel border border-slate-700/40 rounded-2xl bg-slate-950/60 p-6 flex flex-col gap-4 overflow-y-auto shadow-inner mb-8 min-h-[300px]">
            {data.messages && data.messages.length > 0 ? (
              data.messages.map((msg, index) => (
                <MessageBubble
                  key={index}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.created_at}
                />
              ))
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
                <p className="text-sm">No messages found in this shared session.</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
