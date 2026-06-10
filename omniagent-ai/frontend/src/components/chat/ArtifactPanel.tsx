
import React, { useState } from "react";
import { useStore } from "../../store";
import { FiX, FiMaximize2, FiCode, FiEye, FiDownload, FiCopy } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";

export default function ArtifactPanel() {
  const { currentArtifact, setArtifact } = useStore();
  const [view, setView] = useState<"preview" | "code">("preview");
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!currentArtifact) return null;

  const isPreviewable = ["html", "svg", "javascript", "react", "markdown"].includes(
    currentArtifact.language.toLowerCase()
  );

  const getPreviewContent = () => {
    if (currentArtifact.language === "html") {
      return currentArtifact.code;
    }
    if (currentArtifact.language === "svg") {
      return currentArtifact.code;
    }
    // For other types, we might need a more complex runner, but let's start with basic HTML/SVG
    return `<pre style="color: white; padding: 20px;">Preview not supported for ${currentArtifact.language} yet.</pre>`;
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(currentArtifact.code);
  };

  const handleDownload = () => {
    const blob = new Blob([currentArtifact.code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `artifact.${currentArtifact.language === 'javascript' ? 'js' : currentArtifact.language}`;
    a.click();
  };

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      className={`fixed top-0 right-0 h-full bg-slate-950 border-l border-slate-800 z-50 flex flex-col shadow-2xl transition-all duration-300 ${
        isFullscreen ? "w-full" : "w-[500px] lg:w-[700px]"
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400">
            <FiCode size={18} />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm truncate max-w-[200px]">
              {currentArtifact.title || "Generated Artifact"}
            </h3>
            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">
              {currentArtifact.language}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 rounded-lg p-1 mr-4">
            <button
              onClick={() => setView("preview")}
              disabled={!isPreviewable}
              className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-2 ${
                view === "preview" ? "bg-slate-700 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
              } ${!isPreviewable ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <FiEye size={14} />
              Preview
            </button>
            <button
              onClick={() => setView("code")}
              className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-2 ${
                view === "code" ? "bg-slate-700 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <FiCode size={14} />
              Code
            </button>
          </div>

          <button onClick={handleCopy} className="p-2 text-slate-400 hover:text-white" title="Copy code">
            <FiCopy size={18} />
          </button>
          <button onClick={handleDownload} className="p-2 text-slate-400 hover:text-white" title="Download">
            <FiDownload size={18} />
          </button>
          <button onClick={() => setIsFullscreen(!isFullscreen)} className="p-2 text-slate-400 hover:text-white">
            <FiMaximize2 size={18} />
          </button>
          <button onClick={() => setArtifact(null)} className="p-2 text-slate-400 hover:text-rose-400 ml-2">
            <FiX size={20} />
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden bg-slate-900/20">
        {view === "preview" ? (
          <iframe
            srcDoc={getPreviewContent()}
            className="w-full h-full border-none bg-white"
            title="Artifact Preview"
            sandbox="allow-scripts"
          />
        ) : (
          <div className="w-full h-full overflow-auto p-6 font-mono text-sm text-slate-300 selection:bg-blue-500/30">
            <pre className="whitespace-pre-wrap">{currentArtifact.code}</pre>
          </div>
        )}
      </div>
    </motion.div>
  );
}
