import React, { useState } from "react";
import { FiCopy, FiCheck } from "react-icons/fi";
import ReactMarkdown from "react-markdown";
import ResponseFeedback from "./ResponseFeedback";
import type { Message } from "../api/types";

interface KnowledgeMessageProps {
  message: Message;
  onCopy: (id: number | string, content: string) => void;
  isCopied: boolean;
}

export default function KnowledgeMessage({
  message,
  onCopy,
  isCopied,
}: KnowledgeMessageProps) {
  const isUser = message.role === "user";
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 animate-in fade-in-50 slide-in-from-bottom-4 duration-300`}
    >
      <div
        className={`max-w-xl px-4 py-3 rounded-lg ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-slate-800 text-slate-100 border border-slate-700/50"
        }`}
      >
        {!isUser && (
          <div className="prose prose-invert max-w-none text-sm">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                code: ({ children, inline }: any) =>
                  inline ? (
                    <code className="bg-slate-700 px-1.5 py-0.5 rounded text-xs">
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-slate-900 p-3 rounded my-2 overflow-x-auto text-xs">
                      {children}
                    </code>
                  ),
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1">{children}</ol>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-blue-500 pl-3 my-2 italic">
                    {children}
                  </blockquote>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {isUser && <p className="text-white whitespace-pre-wrap">{message.content}</p>}

        {!isUser && (
          <div>
            <button
              onClick={() => onCopy(message.id, message.content)}
              className="mt-2 text-xs text-slate-400 hover:text-slate-200 transition flex items-center gap-1"
            >
              {isCopied ? (
                <>
                  <FiCheck size={14} />
                  Copied
                </>
              ) : (
                <>
                  <FiCopy size={14} />
                  Copy
                </>
              )}
            </button>

            {showFeedback && (
              <div className="mt-2">
                <ResponseFeedback messageId={message.id} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
