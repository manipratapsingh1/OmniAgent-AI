import { create } from "zustand";
import type { Conversation, Message, AgentTrace, Citation } from "../api/types";

interface Artifact {
  code: string;
  language: string;
  title?: string;
}

interface AppState {
  token: string | null;
  setToken: (t: string | null) => void;
  conversations: Conversation[];
  setConversations: (c: Conversation[]) => void;
  activeId: number | null;
  setActive: (id: number | null) => void;
  messages: Message[];
  setMessages: (m: Message[]) => void;
  trace: AgentTrace[];
  setTrace: (t: AgentTrace[]) => void;
  sources: Citation[];
  setSources: (s: Citation[]) => void;
  currentArtifact: Artifact | null;
  setArtifact: (a: Artifact | null) => void;
}

export const useStore = create<AppState>((set) => ({
  token: localStorage.getItem("token"),
  setToken: (t) => { t ? localStorage.setItem("token", t) : localStorage.removeItem("token"); set({ token: t }); },
  conversations: [], setConversations: (c) => set({ conversations: c }),
  activeId: null, setActive: (id) => set({ activeId: id }),
  messages: [], setMessages: (m) => set({ messages: m }),
  trace: [], setTrace: (t) => set({ trace: t }),
  sources: [], setSources: (s) => set({ sources: s }),
  currentArtifact: null,
  setArtifact: (a) => set({ currentArtifact: a }),
}));