import React from "react";
import { FiFileText, FiBookmark } from "react-icons/fi";

interface Source {
  document_id: number;
  filename?: string;
  chunk_index: number;
  snippet: string;
}

interface KnowledgeSourcesPanelProps {
  sources: Source[];
}

export default function KnowledgeSourcesPanel({
  sources,
}: KnowledgeSourcesPanelProps) {
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <FiBookmark size={18} />
          Sources
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          {sources.length === 0
            ? "No sources found"
            : `${sources.length} source${sources.length > 1 ? "s" : ""} found`}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {sources.length === 0 ? (
          <div className="p-4 text-center text-slate-500">
            <FiFileText size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-xs">No sources referenced</p>
          </div>
        ) : (
          <div className="space-y-2 p-4">
            {sources.map((source, idx) => (
              <div
                key={`${source.document_id}-${source.chunk_index}-${idx}`}
                className="p-3 bg-slate-800/50 border border-slate-700/30 rounded-lg hover:border-blue-500/50 transition"
              >
                <div className="flex items-start gap-2 mb-1">
                  <FiFileText size={14} className="text-blue-400 mt-1 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-100 truncate">
                      {source.filename}
                    </p>
                    <p className="text-xs text-slate-500">
                      Chunk {source.chunk_index}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                  {source.snippet}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
