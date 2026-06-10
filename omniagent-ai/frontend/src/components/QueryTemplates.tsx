import React, { useState, useEffect } from "react";
import { FiEdit3, FiPlus, FiX, FiLoader } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../api/client";

interface QueryTemplatesProps {
  onSelectTemplate?: (template: string) => void;
}

export default function QueryTemplates({ onSelectTemplate }: QueryTemplatesProps) {
  const [templates, setTemplates] = useState<any[]>([]);
  const [category, setCategory] = useState("HR");
  const [loading, setLoading] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    title: "",
    template: "",
    icon: "❓",
  });

  const categories = ["HR", "Engineering", "Finance", "General"];

  useEffect(() => {
    fetchTemplates();
  }, [category]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/features/templates`, { params: { category } });
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error("Failed to fetch templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplate.title || !newTemplate.template) return;

    try {
      const response = await api.post("/features/templates", {
        ...newTemplate,
        category,
      });

      if (response.status === 200 || response.status === 201) {
        setNewTemplate({ title: "", template: "", icon: "❓" });
        setShowNew(false);
        fetchTemplates();
      }
    } catch (error) {
      console.error("Failed to create template:", error);
    }
  };

  const handleUseTemplate = (template: string) => {
    if (onSelectTemplate) {
      onSelectTemplate(template);
      return;
    }

    const input = document.querySelector('[placeholder="Ask anything..."]') as HTMLTextAreaElement;
    if (input) {
      input.value = template;
      input.focus();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* Categories */}
      <div className="flex gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition ${
              category === cat
                ? "bg-blue-600 text-white"
                : "bg-slate-800/50 text-zinc-300 hover:bg-slate-700/50"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex justify-center py-8">
          <FiLoader className="animate-spin text-blue-400" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {templates.map((template, idx) => (
            <motion.button
              key={idx}
              onClick={() => handleUseTemplate(template.template)}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-3 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded-lg text-left transition group"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-lg">{template.icon}</span>
                <span className="text-xs text-zinc-500">
                  Used {template.usage_count} times
                </span>
              </div>
              <p className="text-sm font-medium text-white group-hover:text-blue-400 transition">
                {template.title}
              </p>
              <p className="text-xs text-zinc-500 mt-1 line-clamp-2">
                {template.template}
              </p>
            </motion.button>
          ))}

          {/* New Template */}
          <motion.button
            onClick={() => setShowNew(!showNew)}
            className="p-3 border-2 border-dashed border-slate-700 rounded-lg hover:border-blue-600 transition flex items-center justify-center text-blue-400"
          >
            <FiPlus size={20} />
          </motion.button>
        </div>
      )}

      {/* New Template Form */}
      <AnimatePresence>
        {showNew && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg"
          >
            <input
              type="text"
              placeholder="Template title..."
              value={newTemplate.title}
              onChange={(e) => setNewTemplate({ ...newTemplate, title: e.target.value })}
              className="w-full mb-3 bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-sm text-zinc-300"
            />
            <textarea
              placeholder="Template text..."
              value={newTemplate.template}
              onChange={(e) => setNewTemplate({ ...newTemplate, template: e.target.value })}
              className="w-full mb-3 bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-sm text-zinc-300 h-20"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateTemplate}
                className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs text-white transition"
              >
                Create
              </button>
              <button
                onClick={() => setShowNew(false)}
                aria-label="Cancel template"
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-xs text-white transition"
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
