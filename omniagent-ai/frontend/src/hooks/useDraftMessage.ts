import { useEffect, useState } from "react";

/**
 * Hook for auto-saving and restoring draft messages
 * Uses localStorage to persist draft between sessions
 */
export function useDraftMessage(conversationId: number | null) {
  const [draft, setDraft] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  // Generate storage key
  const getKey = (id: number | null) => `draft_${id || "new"}`;

  // Load draft on mount or when conversation changes
  useEffect(() => {
    if (conversationId === null || conversationId === undefined) {
      setDraft("");
      return;
    }

    const key = getKey(conversationId);
    const saved = localStorage.getItem(key);
    if (saved) {
      setDraft(saved);
    } else {
      setDraft("");
    }
    setIsDirty(false);
  }, [conversationId]);

  // Auto-save draft to localStorage (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (conversationId !== null && conversationId !== undefined) {
        const key = getKey(conversationId);
        if (draft.trim()) {
          localStorage.setItem(key, draft);
        } else {
          localStorage.removeItem(key);
        }
      }
    }, 1000); // Save after 1 second of inactivity

    return () => clearTimeout(timer);
  }, [draft, conversationId]);

  const updateDraft = (newDraft: string) => {
    setDraft(newDraft);
    setIsDirty(true);
  };

  const clearDraft = () => {
    setDraft("");
    setIsDirty(false);
    if (conversationId !== null && conversationId !== undefined) {
      const key = getKey(conversationId);
      localStorage.removeItem(key);
    }
  };

  return {
    draft,
    updateDraft,
    clearDraft,
    isDirty,
    hasSavedDraft: draft.length > 0
  };
}
