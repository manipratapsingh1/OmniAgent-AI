import { useState } from "react";
import { useStore } from "../../store";
import { FiFileText, FiChevronDown, FiChevronUp } from "react-icons/fi";

export default function SourcesPanel() {
  const { sources } = useStore();
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const getConfidenceColor = (score: number) => {
    if (score >= 0.7) return "bg-emerald-500";
    if (score >= 0.4) return "bg-amber-500";
    return "bg-rose-500";
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.7) return "High";
    if (score >= 0.4) return "Medium";
    return "Low";
  };

  return (
    <div className="p-4 border-t border-slate-800/60">
      <div className="flex items-center gap-2 mb-3">
        <FiFileText size={14} className="text-blue-400" />
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
          Sources
        </h3>
        {sources.length > 0 && (
          <span className="text-[9px] font-bold bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">
            {sources.length}
          </span>
        )}
      </div>
      
      {sources.length === 0 && (
        <p className="text-xs text-slate-600 italic">No citations for this response.</p>
      )}
      
      <ul className="space-y-2">
        {sources.map((s, i) => {
          const confidence = s.confidence_score ?? 0;
          const isExpanded = expandedIdx === i;
          
          return (
            <li
              key={i}
              className="rounded-xl bg-slate-900/60 border border-slate-800/60 overflow-hidden transition-all hover:border-slate-700/60"
            >
              <button
                onClick={() => setExpandedIdx(isExpanded ? null : i)}
                className="w-full p-3 text-left flex items-start gap-2"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-blue-400 font-mono">
                      📄 {s.document_name || s.filename || `Document ${s.document_id}`}
                    </span>
                    <span className="text-[9px] text-slate-600">§{s.chunk_index}</span>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-1.5">
                    {s.page_number != null && (
                      <span className="text-[9px] font-medium text-slate-500 bg-slate-800/60 px-1.5 py-0.5 rounded">
                        Page {s.page_number}
                      </span>
                    )}
                    {s.section && (
                      <span className="text-[9px] font-medium text-slate-500 bg-slate-800/60 px-1.5 py-0.5 rounded truncate max-w-[120px]">
                        {s.section}
                      </span>
                    )}
                    {confidence > 0 && (
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 h-1 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${getConfidenceColor(confidence)} transition-all`}
                            style={{ width: `${Math.min(confidence * 100, 100)}%` }}
                          />
                        </div>
                        <span className="text-[9px] font-bold text-slate-500">
                          {getConfidenceLabel(confidence)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                {isExpanded ? (
                  <FiChevronUp size={12} className="text-slate-500 mt-0.5 flex-shrink-0" />
                ) : (
                  <FiChevronDown size={12} className="text-slate-500 mt-0.5 flex-shrink-0" />
                )}
              </button>
              
              {isExpanded && s.snippet && (
                <div className="px-3 pb-3 border-t border-slate-800/40">
                  <p className="text-[11px] text-slate-400 leading-relaxed mt-2">
                    {s.snippet}
                  </p>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
