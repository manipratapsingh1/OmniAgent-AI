import React, { useEffect, useRef, useState } from "react";
import { 
  FiSend, 
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  FiLoader, 
  FiTrash2, 
  FiRepeat, 
  FiSettings, 
  FiImage, 
  FiXCircle,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  FiPaperclip
} from "react-icons/fi";
import { Code2 } from "lucide-react";
import { useChat } from "../../hooks/useChat";
import { useStore } from "../../store";
import ToolsPanel from "../ToolsPanel";
import MessageBubble from "./MessageBubble";
import QueryTemplates from "../QueryTemplates";
import ArtifactPanel from "./ArtifactPanel";
import { motion, AnimatePresence } from "framer-motion";

const providerOptions = [
  { value: "phi3:mini", label: "Fast (phi3:mini)" },
  { value: "llama3.2", label: "Balanced (llama3.2)" },
  { value: "mistral", label: "Mistral" },
  { value: "llava", label: "Vision (llava)" },
  { value: "gpt-4o", label: "OpenAI GPT-4o" },
  { value: "claude-3-5-sonnet", label: "Anthropic Claude 3.5 Sonnet" },
  { value: "gemini-1.5-pro", label: "Google Gemini 1.5 Pro" },
  { value: "groq-llama-3-70b", label: "Groq LLaMA 3 70b" },
];

const personaOptions = [
  {
    label: "Helpful assistant",
    value: "You are a helpful assistant that answers clearly, politely, and concisely.",
  },
  {
    label: "Creative storyteller",
    value:
      "You are a creative storyteller who crafts imaginative, expressive, and engaging answers.",
  },
  {
    label: "Technical expert",
    value:
      "You are a technical expert. Provide precise, structured, and accurate answers with examples where appropriate.",
  },
  {
    label: "Research assistant",
    value:
      "You are a research assistant. Summarize facts, cite sources, and provide concise evidence-based answers.",
  },
  {
    label: "Deep Reasoning",
    value:
      "You are an advanced reasoning model. Think step-by-step. Decompose complex problems into sub-tasks. Use tools when necessary. Verify your assumptions and provide detailed, logical explanations.",
  },
];

export default function ChatWindow() {
  const { messages, activeId, setMessages, setSources } = useStore();
  const { send, stop } = useChat();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState("phi3:mini");
  const [chatMode, setChatMode] = useState<"fast" | "knowledge">("fast");
  const [systemPrompt, setSystemPrompt] = useState(personaOptions[0].value);
  const [showTools, setShowTools] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    try {
      const savedModel = localStorage.getItem("omniagent:model");
      const persona = localStorage.getItem("omniagent:persona");
      if (savedModel) setModel(savedModel);
      if (persona) setSystemPrompt(persona);
    } catch {
      // ignore localStorage errors
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("omniagent:model", model);
      localStorage.setItem("omniagent:persona", systemPrompt);
    } catch {
      // ignore
    }
  }, [model, systemPrompt]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        // Strip the data:image/jpeg;base64, part if needed by backend, 
        // but Ollama usually expects the full data URI or just base64.
        // Let's send the base64 part only as that's what Ollama API typically wants.
        const base64Data = base64String.split(",")[1];
        setImages((prev) => [...prev, base64Data]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = async (messageOverride?: string) => {
    const messageText = messageOverride ?? input.trim();
    if (!messageText && images.length === 0) return;

    setError(null);
    setLoading(true);
    setLastUserMessage(messageText);
    setInput("");
    const currentImages = [...images];
    setImages([]); // Clear images after sending

    try {
      await send(messageText, model, true, systemPrompt, chatMode, currentImages);
    } catch (err: unknown) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!lastUserMessage.trim()) {
      setError("Nothing to regenerate yet.");
      return;
    }
    await handleSend(lastUserMessage);
  };

  const handleStop = () => {
    stop();
    setLoading(false);
  };

  const handleClear = () => {
    setMessages([]);
    setSources([]);
    setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-white relative">
      {/* Header Section */}
      <div className="border-b border-slate-800/60 bg-slate-950/50 backdrop-blur-md px-6 py-4 sticky top-0 z-20">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-sm">
              <FiSend className="text-white" size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">AI Assistant</h1>
                <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                  <div className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
                  ONLINE
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">{messages.length} messages in this thread</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex bg-slate-900/50 p-1 rounded-xl border border-slate-800/50 mr-2">
              <button
                onClick={() => setChatMode("fast")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${chatMode === "fast" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"}`}
              >
                Fast
              </button>
              <button
                onClick={() => setChatMode("knowledge")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${chatMode === "knowledge" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"}`}
              >
                Knowledge
              </button>
            </div>
            <button
              type="button"
              onClick={handleClear}
              className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/50 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/20 transition-all"
              title="Clear conversation"
            >
              <FiTrash2 size={18} />
            </button>
            <button
              type="button"
              onClick={() => setShowTemplates(!showTemplates)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
            >
              Templates
            </button>
            <button
              type="button"
              onClick={() => setShowTools(!showTools)}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 text-sm font-bold text-white shadow-glow-sm hover:shadow-glow-md hover:scale-[1.02] transition-all"
            >
              <Code2 size={16} />
              Tools
            </button>
          </div>
        </div>

        {showTemplates && (
          <div className="mt-4">
            <QueryTemplates
              onSelectTemplate={(template) => {
                setInput(template);
                setShowTemplates(false);
              }}
            />
          </div>
        )}

        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">Engine</span>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs font-medium text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all appearance-none cursor-pointer"
            >
              {providerOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5 lg:col-span-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">Persona</span>
            <select
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs font-medium text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all appearance-none cursor-pointer"
            >
              {personaOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-8 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-16 h-16 rounded-3xl bg-slate-900 flex items-center justify-center mb-6 border border-slate-800 shadow-xl">
              <FiSend className="text-blue-500" size={32} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">How can I help you today?</h3>
            <p className="text-slate-400 max-w-md text-sm leading-relaxed">
              I can help with document analysis, coding, creative writing, or general research. Select a persona or template to get started.
            </p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-8">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`mb-4 flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <MessageBubble
                  role={message.role}
                  content={message.content}
                  timestamp={message.created_at}
                />
              </div>
            ))}
            {loading && (
              <div className="mb-4 flex justify-start">
                <MessageBubble
                  // eslint-disable-next-line jsx-a11y/aria-role
                  role="assistant"
                  content=""
                  isThinking={true}
                />
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
        <div className="max-w-4xl mx-auto relative">
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute -top-14 left-0 right-0 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <FiSettings size={14} />
                {error}
              </div>
              <button onClick={() => setError(null)} className="hover:text-white">Close</button>
            </motion.div>
          )}

          {/* Image Previews */}
          {images.length > 0 && (
            <div className="flex flex-wrap gap-3 mb-3">
              {images.map((img, idx) => (
                <div key={idx} className="relative group">
                  <img 
                    src={`data:image/jpeg;base64,${img}`} 
                    className="w-16 h-16 object-cover rounded-xl border border-slate-700 shadow-xl"
                    alt="Preview"
                  />
                  <button 
                    onClick={() => removeImage(idx)}
                    className="absolute -top-2 -right-2 text-rose-500 bg-slate-900 rounded-full group-hover:scale-110 transition-transform"
                  >
                    <FiXCircle size={18} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="relative group">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask anything... (Ctrl+Enter to send)"
              className={`w-full rounded-2xl border bg-slate-900/80 px-5 py-4 pr-44 text-sm text-white placeholder:text-slate-500 focus:outline-none transition-all resize-none min-h-[60px] max-h-[200px] shadow-2xl backdrop-blur-sm ${
                isFocused ? "border-blue-500/50 ring-2 ring-blue-500/30 shadow-glow-md" : "border-slate-800"
              }`}
              rows={1}
            />
            
            <div className="absolute right-2 bottom-2 flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageUpload}
                accept="image/*"
                multiple
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/50 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
                title="Upload image"
              >
                <FiImage size={18} />
              </button>

              {loading ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition-all border border-slate-700"
                >
                  <div className="w-2 h-2 rounded-sm bg-rose-500 animate-pulse" />
                  Stop
                </button>
              ) : (
                <>
                  {lastUserMessage && (
                    <button
                      type="button"
                      onClick={handleRegenerate}
                      className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/50 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
                      title="Regenerate last response"
                    >
                      <FiRepeat size={18} />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => handleSend()}
                    disabled={!input.trim() && images.length === 0}
                    className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white shadow-glow-sm transition-all ${
                      (input.trim() || images.length > 0)
                        ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-glow-md hover:scale-[1.02]" 
                        : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                    }`}
                  >
                    <FiSend size={16} />
                    Send
                  </button>
                </>
              )}
            </div>
          </div>
          <p className="mt-3 text-[10px] text-center text-slate-600 font-medium uppercase tracking-[0.2em]">
            OmniAgent X AI OS · Production Grade · v2.0.0
          </p>
        </div>
      </div>

      <ToolsPanel
        conversationId={activeId ?? 0}
        visible={showTools}
        onClose={() => setShowTools(false)}
      />

      {/* Artifact Panel Overlay */}
      <AnimatePresence>
        <ArtifactPanel />
      </AnimatePresence>
    </div>
  );
}
