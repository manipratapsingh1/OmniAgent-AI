import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiX, FiCommand } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";

const SHORTCUTS = [
  { key: "⌘/Ctrl + Enter", action: "Send message" },
  { key: "⌘/Ctrl + K", action: "Search conversations" },
  { key: "⌘/Ctrl + N", action: "New chat" },
  { key: "⌘/Ctrl + S", action: "Settings" },
  { key: "Esc", action: "Close this menu" },
];

export default function KeyboardShortcuts() {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        navigate("/search");
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "n") {
        e.preventDefault();
        navigate("/chat");
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        navigate("/settings");
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "?") {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, navigate]);

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 rounded-lg border border-slate-700 p-6 max-w-md shadow-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FiCommand className="text-blue-400" size={24} />
                  <h2 className="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  title="Close keyboard shortcuts"
                  className="text-zinc-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <div className="space-y-3">
                {SHORTCUTS.map((shortcut, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-zinc-300">{shortcut.action}</span>
                    <span className="px-2 py-1 rounded bg-slate-800 text-blue-300 font-mono text-xs border border-slate-700">
                      {shortcut.key}
                    </span>
                  </div>
                ))}
              </div>

              <p className="text-xs text-zinc-500 mt-4 pt-4 border-t border-slate-700">
                Press <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-600 text-xs">⌘/Ctrl + ?</kbd> to toggle this menu
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
