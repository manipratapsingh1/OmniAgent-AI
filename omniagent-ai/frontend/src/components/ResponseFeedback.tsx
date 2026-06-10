import React, { useState } from "react";
import { FiThumbsUp, FiThumbsDown, FiLoader } from "react-icons/fi";
import { motion } from "framer-motion";
import { api } from "../api/client";

interface ResponseFeedbackProps {
  messageId: number | string;
  onSubmit?: (helpful: boolean, reason?: string) => void;
}

export default function ResponseFeedback({ messageId, onSubmit }: ResponseFeedbackProps) {
  const [feedback, setFeedback] = useState<"helpful" | "unhelpful" | null>(null);
  const [showReason, setShowReason] = useState(false);
  const [reason, setReason] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!feedback) return;

    setLoading(true);
    try {
      await api.post("/features/feedback/submit", {
        response_id: messageId,
        helpful: feedback === "helpful",
        rating_scale: null,
      });

      setSubmitted(true);
      onSubmit?.(feedback === "helpful", reason);
      
      setTimeout(() => {
        setFeedback(null);
        setShowReason(false);
        setReason("");
        setSubmitted(false);
      }, 2000);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 mt-3"
    >
      {submitted ? (
        <span className="text-xs text-green-400">✓ Thank you for your feedback!</span>
      ) : (
        <>
          <span className="text-xs text-zinc-500">Was this helpful?</span>
          <button
            onClick={() => {
              setFeedback("helpful");
              setShowReason(true);
            }}
            className={`p-1.5 rounded transition ${
              feedback === "helpful"
                ? "bg-green-600/30 text-green-400"
                : "hover:bg-slate-800/50 text-zinc-500 hover:text-green-400"
            }`}
            title="Mark as helpful"
          >
            <FiThumbsUp size={16} />
          </button>
          <button
            onClick={() => {
              setFeedback("unhelpful");
              setShowReason(true);
            }}
            className={`p-1.5 rounded transition ${
              feedback === "unhelpful"
                ? "bg-red-600/30 text-red-400"
                : "hover:bg-slate-800/50 text-zinc-500 hover:text-red-400"
            }`}
            title="Mark as unhelpful"
          >
            <FiThumbsDown size={16} />
          </button>

          {showReason && feedback && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 ml-2"
            >
              <input
                type="text"
                placeholder="Tell us why..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="text-xs bg-slate-800/50 border border-slate-700 rounded px-2 py-1 text-zinc-300"
                maxLength={100}
              />
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-500 rounded transition disabled:opacity-50"
              >
                {loading ? <FiLoader className="animate-spin" /> : "Send"}
              </button>
            </motion.div>
          )}
        </>
      )}
    </motion.div>
  );
}
