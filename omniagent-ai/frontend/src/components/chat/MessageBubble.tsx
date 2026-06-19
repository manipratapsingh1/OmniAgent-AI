import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { useNotificationStore } from "../../store/notificationStore";

import { useStore } from "../../store";
import { FiEye } from "react-icons/fi";

interface MessageBubbleProps {
  role: string;
  content: string;
  timestamp?: string;
  isThinking?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CodeBlock({ inline, className, children }: any) {
  const isInline = inline;
  const code = String(children[0] || "");
  const langMatch = /language-(\w+)/.exec(className || "") || [];
  const lang = langMatch[1] || null;
  const { setArtifact } = useStore();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      addNotification({ type: "success", message: "Code copied to clipboard", duration: 2500 });
      setTimeout(() => setCopied(false), 1500);
    } catch (e) {
      addNotification({ type: "error", message: "Unable to copy to clipboard" });
    }
  };

  const isArtifact = ["html", "svg", "javascript", "react", "mermaid", "python"].includes(lang?.toLowerCase() || "");

  if (isInline) {
    return <code className="rounded px-1 py-0.5 bg-slate-800 text-slate-100">{code}</code>;
  }

  return (
    <div className="relative my-3 group/code">
      <div className="absolute right-2 top-2 flex items-center gap-2 opacity-0 group-hover/code:opacity-100 transition-opacity">
        {isArtifact && (
          <button
            onClick={() => setArtifact({ code, language: lang || "text", title: "Generated Snippet" })}
            className="text-[10px] font-bold bg-blue-600/80 hover:bg-blue-600 px-2 py-1 rounded text-white border border-blue-400/20 flex items-center gap-1.5 shadow-lg backdrop-blur-sm"
          >
            <FiEye size={12} />
            Preview
          </button>
        )}
        {lang && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 py-1 bg-slate-800/60 rounded border border-slate-700/50">{lang}</span>}
        <button
          onClick={handleCopy}
          className="text-[10px] font-bold bg-slate-800/80 hover:bg-slate-700 px-2 py-1 rounded text-slate-300 border border-slate-700/50 shadow-lg backdrop-blur-sm"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-auto rounded-xl bg-slate-950 border border-slate-800/60 p-5 text-sm shadow-inner selection:bg-blue-500/20">
         <code className={className}>{code}</code>
      </pre>
    </div>
  );
}

export default function MessageBubble({ role, content, timestamp, isThinking = false }: MessageBubbleProps) {
  const mine = role === "user";
  const formatTime = (isoString?: string) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"} my-4 group items-end gap-3`}>
      {!mine && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-blue-700 flex items-center justify-center flex-shrink-0 shadow-glow-sm border border-white/10">
          <div className="text-[10px] font-bold text-white">AI</div>
        </div>
      )}
      
      <div className={`flex flex-col max-w-[85%] ${mine ? "items-end" : "items-start"}`}>
        <div className={`rounded-2xl px-5 py-4 shadow-xl border backdrop-blur-sm transition-all duration-300
          ${mine 
            ? "bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-br-none border-blue-400/20 shadow-blue-500/10" 
            : "bg-slate-900/80 text-slate-100 rounded-bl-none border-slate-800 shadow-black/20"}`}>
          
          {isThinking ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-widest animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                Thinking...
              </div>
              <div className="space-y-2.5 w-48">
                <div className="h-2 bg-slate-800 rounded-full w-full shimmer" />
                <div className="h-2 bg-slate-800 rounded-full w-5/6 shimmer" />
                <div className="h-2 bg-slate-800 rounded-full w-2/3 shimmer" />
              </div>
              <div className="flex items-center gap-1.5 mt-1 pl-1">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-950/50 prose-pre:border prose-pre:border-slate-800">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm as never]} 
                rehypePlugins={[rehypeHighlight as never]} 
                components={{ code: CodeBlock }}
              >
                {content}
              </ReactMarkdown>
              {/* Render citation badges if citations detected */}
              {!mine && /\[doc:\d+#\d+\]/.test(content) && (
                <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-800/60">
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mr-1 self-center">Sources:</span>
                  {Array.from(content.matchAll(/\[doc:(\d+)#(\d+)\]/g)).map(([, docId, chunkId], idx) => (
                    <span
                      key={`${docId}-${chunkId}-${idx}`}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-bold text-blue-400"
                    >
                      📄 Doc {docId} · §{chunkId}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        
        {!isThinking && (
          <div className={`flex items-center gap-3 mt-2 px-1 transition-all duration-300 ${timestamp ? "opacity-100" : "opacity-0"}`}>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              {mine ? "You" : "OmniAgent"}
            </span>
            <span className="text-[10px] text-slate-600">
              {formatTime(timestamp)}
            </span>
          </div>
        )}
      </div>

      {mine && (
        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0 border border-slate-700 shadow-lg">
          <div className="text-[10px] font-bold text-slate-400">ME</div>
        </div>
      )}
    </div>
  );
}