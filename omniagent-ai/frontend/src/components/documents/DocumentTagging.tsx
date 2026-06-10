import React, { useState, useEffect } from "react";
import { FiTag, FiX, FiPlus, FiLoader } from "react-icons/fi";
import { motion } from "framer-motion";
import { api } from "../../api/client";

interface DocumentTaggingProps {
  documentId: number;
  initialTags?: string[];
  onTagsChange?: (tags: string[]) => void;
}

export default function DocumentTagging({ documentId, initialTags = [], onTagsChange }: DocumentTaggingProps) {
  const [tags, setTags] = useState<string[]>(initialTags);
  const [newTag, setNewTag] = useState("");
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");

  useEffect(() => {
    loadTags();
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get("/features/categories");
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const loadTags = async () => {
    try {
      const response = await api.get(`/features/document/${documentId}/tags`);
      setTags(response.data.tags || []);
      onTagsChange?.(response.data.tags || []);
    } catch (error) {
      console.error("Failed to load document tags:", error);
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) return;

    setLoading(true);
    try {
      const response = await api.post(`/features/document/${documentId}/tags`, {
        tags: [newTag],
        category: selectedCategory || null,
      });

      if (response.status === 200 || response.status === 201) {
        await loadTags();
        setNewTag("");
      }
    } catch (error) {
      console.error("Failed to add tag:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    setLoading(true);
    try {
      await api.delete(`/features/document/${documentId}/tags/${encodeURIComponent(tagToRemove)}`);
      await loadTags();
    } catch (error) {
      console.error("Failed to remove tag:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50"
    >
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <FiTag size={16} />
        Tags & Categories
      </h3>

      {/* Category Selection */}
      <div className="mb-4">
        <label htmlFor="category-select" className="block text-xs text-zinc-400 mb-2">
          Category
        </label>
        <select
          id="category-select"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-xs text-zinc-300"
        >
          <option value="">Select category...</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.name}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      {/* Tag Input */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAddTag()}
          placeholder="Add a tag..."
          className="flex-1 bg-slate-900/50 border border-slate-700 rounded px-2 py-1.5 text-xs text-zinc-300"
        />
        <button
          type="button"
          onClick={handleAddTag}
          disabled={loading || !newTag.trim()}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs flex items-center gap-1 transition disabled:opacity-50"
        >
          {loading ? <FiLoader className="animate-spin" /> : <FiPlus />}
          Add
        </button>
      </div>

      {/* Current Tags */}
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <motion.span
            key={tag}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            className="inline-flex items-center gap-2 px-2.5 py-1 bg-blue-600/30 text-blue-300 rounded-full text-xs"
          >
            {tag}
            <button
              type="button"
              onClick={() => handleRemoveTag(tag)}
              aria-label={`Remove tag ${tag}`}
              className="hover:text-blue-200 transition"
            >
              <FiX size={14} />
            </button>
          </motion.span>
        ))}
      </div>

      {tags.length === 0 && (
        <p className="text-xs text-zinc-500 italic">No tags yet. Add one to organize this document.</p>
      )}
    </motion.div>
  );
}
