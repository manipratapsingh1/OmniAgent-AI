import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import {
  FiUpload,
  FiLoader,
  FiTrash2,
  FiBookOpen,
  FiFileText,
  FiAlertCircle,
  FiChevronDown,
  FiChevronRight,
} from "react-icons/fi";
import DocumentTagging from "./documents/DocumentTagging";
import DocumentFAQs from "./documents/DocumentFAQs";

interface KnowledgeDocument {
  id: number;
  filename: string;
  status: string;
  chunk_count: number;
  size_bytes: number;
  created_at: string;
}

interface KnowledgeBaseInfo {
  total_documents: number;
  indexed_documents: number;
  failed_documents: number;
  total_size_bytes: number;
  total_chunks: number;
  documents: KnowledgeDocument[];
}

export default function KnowledgeBaseAdmin() {
  const { token } = useAuth();
  const { addNotification } = useNotificationStore();
  const [kbInfo, setKbInfo] = useState<KnowledgeBaseInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadKnowledgeBaseInfo();
  }, []);

  const loadKnowledgeBaseInfo = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/v1/document/knowledge-base/info", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Failed to load knowledge base info");

      const data = await response.json();
      setKbInfo(data);
    } catch (error) {
      console.error("Error:", error);
      addNotification({
        type: "error",
        message: "Failed to load knowledge base information",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "/api/v1/document/knowledge-base/upload",
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      addNotification({
        type: "success",
        message: `Knowledge base document "${file.name}" uploaded successfully`,
      });

      // Reload knowledge base info
      await loadKnowledgeBaseInfo();

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Error:", error);
      addNotification({
        type: "error",
        message: `Failed to upload: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    } finally {
      setUploading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <FiLoader className="animate-spin mr-2" />
        Loading knowledge base...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <FiBookOpen size={24} className="text-blue-400" />
        <div>
          <h2 className="text-xl font-bold text-white">Knowledge Base</h2>
          <p className="text-sm text-slate-400">
            Manage company documents for the AI assistant
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      {kbInfo && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm font-medium mb-1">
              Total Documents
            </p>
            <p className="text-2xl font-bold text-white">
              {kbInfo.total_documents}
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm font-medium mb-1">Indexed</p>
            <p className="text-2xl font-bold text-green-400">
              {kbInfo.indexed_documents}
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm font-medium mb-1">
              Total Size
            </p>
            <p className="text-2xl font-bold text-blue-400">
              {formatBytes(kbInfo.total_size_bytes)}
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm font-medium mb-1">
              Total Chunks
            </p>
            <p className="text-2xl font-bold text-purple-400">
              {kbInfo.total_chunks}
            </p>
          </div>
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FiUpload size={20} />
          Upload Document
        </h3>

        <label
          htmlFor="knowledge-upload"
          className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition"
        >
          <FiFileText size={32} className="mx-auto mb-2 text-slate-400" />
          <p className="text-slate-300 mb-1">Click to upload or drag and drop</p>
          <p className="text-xs text-slate-500">
            PDF, TXT, MD, DOCX, PPTX, HTML (max 10MB)
          </p>
          <input
            id="knowledge-upload"
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown,.docx,.pptx,.html,.htm"
            onChange={handleFileSelect}
            disabled={uploading}
            aria-label="Upload knowledge base document"
            className="hidden"
          />
        </label>

        {uploading && (
          <div className="mt-4 flex items-center justify-center gap-2 text-blue-400">
            <FiLoader className="animate-spin" />
            Uploading and processing...
          </div>
        )}
      </div>

      {/* Failed Documents Warning */}
      {kbInfo && kbInfo.failed_documents > 0 && (
        <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg p-4 flex gap-3">
          <FiAlertCircle size={20} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-100 font-medium">
              {kbInfo.failed_documents} document{kbInfo.failed_documents > 1 ? "s" : ""} failed to index
            </p>
            <p className="text-amber-200/70 text-sm">
              Check the documents list below for details
            </p>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-slate-700/50">
          <h3 className="text-lg font-semibold text-white">
            Documents ({kbInfo?.documents.length || 0})
          </h3>
        </div>

        {!kbInfo || kbInfo.documents.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <FiFileText size={32} className="mx-auto mb-2 opacity-50" />
            <p>No documents in knowledge base yet</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {kbInfo.documents.map((doc) => (
              <div
                key={doc.id}
                className="p-4 hover:bg-slate-700/30 transition flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">{doc.filename}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {formatBytes(doc.size_bytes)} •{" "}
                    {doc.chunk_count} chunks •{" "}
                    <span
                      className={
                        doc.status === "indexed"
                          ? "text-green-400"
                          : doc.status === "pending"
                          ? "text-yellow-400"
                          : "text-red-400"
                      }
                    >
                      {doc.status}
                    </span>
                  </p>
                </div>
                <div className="text-xs text-slate-500 flex-shrink-0">
                  {new Date(doc.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
