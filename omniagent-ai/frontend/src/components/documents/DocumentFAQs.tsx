import React, { useState, useEffect } from "react";
import { FiHelpCircle, FiPlus, FiLoader, FiX } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../../api/client";

interface DocumentFAQsProps {
  documentId: number;
}

export default function DocumentFAQs({ documentId }: DocumentFAQsProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [faqs, setFaqs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null);
  const [newFAQ, setNewFAQ] = useState({ question: "", answer: "" });

  useEffect(() => {
    fetchFAQs();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const fetchFAQs = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/features/document/${documentId}/faqs`);
      setFaqs(response.data.faqs || []);
    } catch (error) {
      console.error("Failed to fetch FAQs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddFAQ = async () => {
    if (!newFAQ.question || !newFAQ.answer) return;

    try {
      const response = await api.post(`/features/document/${documentId}/faq`, newFAQ);

      if (response.status === 200 || response.status === 201) {
        setNewFAQ({ question: "", answer: "" });
        setShowNew(false);
        fetchFAQs();
      }
    } catch (error) {
      console.error("Failed to add FAQ:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <FiLoader className="animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FiHelpCircle size={16} />
          FAQs ({faqs.length})
        </h3>
        <button
          type="button"
          onClick={() => setShowNew(!showNew)}
          className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 rounded text-white transition flex items-center gap-1"
        >
          <FiPlus size={14} />
          Add
        </button>
      </div>

      {/* FAQ List */}
      {faqs.length > 0 ? (
        <div className="space-y-2">
          {faqs.map((faq, idx) => (
            <motion.button
              key={idx}
              onClick={() => setExpandedFAQ(expandedFAQ === idx ? null : idx)}
              className="w-full text-left p-3 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded transition"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="flex items-start justify-between">
                <p className="text-sm font-medium text-white">{faq.question}</p>
                <span className="text-xs text-zinc-500">
                  {expandedFAQ === idx ? "−" : "+"}
                </span>
              </div>

              <AnimatePresence>
                {expandedFAQ === idx && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="text-xs text-zinc-400 mt-2"
                  >
                    {faq.answer}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.button>
          ))}
        </div>
      ) : (
        <p className="text-xs text-zinc-500 italic">No FAQs yet</p>
      )}

      {/* New FAQ Form */}
      <AnimatePresence>
        {showNew && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 bg-slate-800/50 border border-slate-700 rounded space-y-2"
          >
            <input
              type="text"
              placeholder="Question..."
              value={newFAQ.question}
              onChange={(e) => setNewFAQ({ ...newFAQ, question: e.target.value })}
              className="w-full bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-xs text-zinc-300"
            />
            <textarea
              placeholder="Answer..."
              value={newFAQ.answer}
              onChange={(e) => setNewFAQ({ ...newFAQ, answer: e.target.value })}
              className="w-full bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-xs text-zinc-300 h-16"
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleAddFAQ}
                className="flex-1 px-2 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs text-white transition"
              >
                Add FAQ
              </button>
              <button
                type="button"
                onClick={() => setShowNew(false)}
                aria-label="Close add FAQ"
                className="px-2 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-xs text-white transition"
              >
                <FiX />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
