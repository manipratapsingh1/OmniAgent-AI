import React, { useState } from "react";
import { FiShare2, FiCopy, FiCheck, FiLoader, FiClock } from "react-icons/fi";
import { motion } from "framer-motion";
import { api } from "../api/client";

interface ShareConversationProps {
  conversationId: number;
  onShare?: (shareUrl: string) => void;
}

export default function ShareConversation({ conversationId, onShare }: ShareConversationProps) {
  const [showShare, setShowShare] = useState(false);
  const [loading, setLoading] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [expiresIn, setExpiresIn] = useState<number>(24);

  const handleCreateShare = async () => {
    setLoading(true);
    try {
      const response = await api.post(`/features/conversation/${conversationId}/share`, {
        expires_in_hours: expiresIn,
      });

      const data = response.data;
      const fullUrl = `${window.location.origin}${data.share_url}`;
      setShareUrl(fullUrl);
      onShare?.(fullUrl);
    } catch (error) {
      console.error("Failed to create share:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUrl = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const expandedState = showShare ? 'true' : 'false';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="relative"
    >
      <button
        type="button"
        onClick={() => setShowShare(!showShare)}
        className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 rounded text-xs text-zinc-300 flex items-center gap-2 transition"
        aria-label={showShare ? 'Close share options' : 'Open share options'}
      >
        <FiShare2 size={14} />
        Share
      </button>

      {showShare && (
        <motion.div
          id="share-conversation-panel"
          role="dialog"
          aria-modal="true"
          aria-label="Share conversation options"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-full mt-2 right-0 bg-slate-900 border border-slate-700 rounded-lg p-4 min-w-80 shadow-lg z-50"
        >
          <h3 className="text-sm font-semibold text-white mb-3">Share Conversation</h3>

          {!shareUrl ? (
            <>
              <div className="mb-4">
                <label htmlFor="share-expires-in" className="text-xs text-zinc-400 mb-2 block">
                  <span className="inline-flex items-center gap-2">
                    <FiClock size={14} />
                    Expires in
                  </span>
                </label>
                <select
                  id="share-expires-in"
                  value={expiresIn}
                  onChange={(e) => setExpiresIn(parseInt(e.target.value))}
                  className="w-full bg-slate-800/50 border border-slate-700 rounded px-2 py-1.5 text-xs text-zinc-300"
                >
                  <option value={1}>1 hour</option>
                  <option value={24}>24 hours</option>
                  <option value={168}>7 days</option>
                  <option value={720}>30 days</option>
                </select>
              </div>

              <button
                type="button"
                onClick={handleCreateShare}
                disabled={loading}
                className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs text-white transition disabled:opacity-50 flex items-center justify-center gap-2"
                aria-label="Create shareable conversation link"
              >
                {loading && <FiLoader className="animate-spin" />}
                Create Share Link
              </button>
            </>
          ) : (
            <>
              <div className="bg-slate-800/50 border border-slate-700 rounded p-2 mb-3">
                <p className="text-xs text-zinc-400 break-all">{shareUrl}</p>
              </div>

              <button
                type="button"
                onClick={handleCopyUrl}
                className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs text-white transition flex items-center justify-center gap-2"
                aria-label={copied ? 'Link copied to clipboard' : 'Copy share link to clipboard'}
              >
                {copied ? <FiCheck size={14} /> : <FiCopy size={14} />}
                {copied ? "Copied!" : "Copy Link"}
              </button>

              <button
                type="button"
                onClick={() => {
                  setShareUrl(null);
                  setShowShare(false);
                }}
                className="w-full mt-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-700/50 rounded text-xs text-zinc-300 transition"
                aria-label="Close share panel"
              >
                Done
              </button>
            </>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
