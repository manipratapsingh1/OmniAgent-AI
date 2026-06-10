
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FiSearch, FiMessageSquare, FiFileText, FiSettings, FiShield, FiCommand } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const actions = [
    { icon: FiMessageSquare, label: "New Chat", path: "/chat" },
    { icon: FiFileText, label: "View Documents", path: "/documents" },
    { icon: FiShield, label: "Admin Analytics", path: "/admin" },
    { icon: FiSettings, label: "User Settings", path: "/settings" },
    { icon: FiCommand, label: "Debug Status", path: "/debug" },
  ].filter(a => a.label.toLowerCase().includes(query.toLowerCase()));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 p-4 bg-slate-950/60 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: -20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden"
      >
        <div className="flex items-center px-4 border-b border-slate-800">
          <FiSearch className="text-slate-500" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="w-full bg-transparent border-none focus:ring-0 text-white p-4 text-sm"
          />
          <div className="px-2 py-1 rounded bg-slate-800 text-[10px] font-bold text-slate-500 uppercase">ESC</div>
        </div>
        
        <div className="max-h-[300px] overflow-y-auto p-2">
          {actions.length > 0 ? (
            actions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => {
                  navigate(action.path);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-blue-600/10 hover:text-blue-400 text-slate-400 transition-all text-sm group"
              >
                <action.icon className="group-hover:scale-110 transition-transform" />
                <span className="font-medium">{action.label}</span>
              </button>
            ))
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm italic">No commands found matching "{query}"</div>
          )}
        </div>
        
        <div className="p-3 border-t border-slate-800 bg-slate-950/50 flex justify-between items-center text-[10px] font-bold text-slate-600 uppercase tracking-widest">
          <span>Navigate with arrows</span>
          <span>Select with Enter</span>
        </div>
      </motion.div>
    </div>
  );
}
