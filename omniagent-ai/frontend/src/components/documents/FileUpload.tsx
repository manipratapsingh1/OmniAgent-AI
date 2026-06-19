import { useState, useRef } from "react";
import { api, getErrorMessage } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";
import { useNotificationStore } from "../../store/notificationStore";
import { FiUpload, FiAlertCircle, FiFile } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import JobStatus from "./JobStatus";

interface UploadFileItem {
  id: string;
  file: File;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  jobId: number | null;
  errorMsg?: string;
}

export default function FileUpload({ onUploaded }: { onUploaded?: () => void }) {
  const { user } = useAuth();
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadList, setUploadList] = useState<UploadFileItem[]>([]);
  const addNotification = useNotificationStore((s) => s.addNotification);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Only admins can upload
  if (!user?.is_admin && user?.role !== 'admin') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 bg-yellow-900/30 rounded-xl border border-yellow-800 flex items-start gap-3"
      >
        <FiAlertCircle className="text-yellow-400 mt-1 flex-shrink-0" size={20} />
        <div>
          <p className="text-yellow-200 font-medium">Admin Only</p>
          <p className="text-yellow-300 text-sm">Only administrators can upload documents</p>
        </div>
      </motion.div>
    );
  }

  const allowedMimeTypes = [
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/html",
    "application/octet-stream",
  ];
  const allowedExtensions = [".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx", ".csv", ".xlsx", ".html", ".htm"];

  const validateFile = (file: File): { valid: boolean; reason?: string } => {
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return { valid: false, reason: "File size exceeds 10MB limit" };
    }

    const name = (file.name || "").toLowerCase();
    const hasAllowedExt = allowedExtensions.some((ext) => name.endsWith(ext));
    const hasAllowedMime = allowedMimeTypes.includes(file.type);

    if (!hasAllowedExt && !hasAllowedMime) {
      return { valid: false, reason: "Supported: PDF, TXT, MD, DOCX, PPTX, CSV, XLSX, HTML" };
    }
    return { valid: true };
  };

  const startUploadQueue = async (newItems: UploadFileItem[]) => {
    for (const item of newItems) {
      // Set status to uploading
      setUploadList((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: "uploading" } : i))
      );

      try {
        const fd = new FormData();
        fd.append("file", item.file);

        const r = await api.post("/documents/upload_job", fd, {
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadList((prev) =>
                prev.map((i) => (i.id === item.id ? { ...i, progress: percentCompleted } : i))
              );
            }
          },
        });

        const jobId = r.data.job_id;
        setUploadList((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, status: "success", jobId: jobId || null } : i
          )
        );

        addNotification({
          type: "success",
          message: `Uploaded ${item.file.name} successfully ${jobId ? `(Job #${jobId})` : ""}`,
        });

        onUploaded?.();
      } catch (err) {
        const errorMsg = getErrorMessage(err);
        setUploadList((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, status: "error", errorMsg } : i
          )
        );
        addNotification({
          type: "error",
          message: `Failed to upload ${item.file.name}: ${errorMsg}`,
        });
      }
    }
  };

  const handleFiles = (files: FileList) => {
    const validItems: UploadFileItem[] = [];
    const invalidMessages: string[] = [];

    Array.from(files).forEach((file) => {
      const validation = validateFile(file);
      if (validation.valid) {
        validItems.push({
          id: `${file.name}-${Date.now()}-${Math.random()}`,
          file,
          progress: 0,
          status: "pending",
          jobId: null,
        });
      } else {
        invalidMessages.push(`${file.name}: ${validation.reason}`);
      }
    });

    if (invalidMessages.length > 0) {
      addNotification({
        type: "error",
        message: `Validation failed:\n${invalidMessages.join("\n")}`,
      });
    }

    if (validItems.length > 0) {
      setUploadList((prev) => [...prev, ...validItems]);
      startUploadQueue(validItems);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const clearCompleted = () => {
    setUploadList((prev) => prev.filter((i) => i.status === "uploading" || i.status === "pending"));
  };

  const showClearButton = uploadList.some((i) => i.status === "success" || i.status === "error");

  return (
    <div className="space-y-4">
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        animate={{
          borderColor: isDragOver ? "#ec4899" : "#334155",
          backgroundColor: isDragOver ? "rgba(236, 72, 153, 0.05)" : "rgba(30, 41, 59, 0.3)",
          scale: isDragOver ? 1.01 : 1,
        }}
        transition={{ duration: 0.2 }}
        className="cursor-pointer border-2 border-dashed rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-3 relative overflow-hidden group select-none backdrop-blur-md"
      >
        <input
          type="file"
          className="hidden"
          multiple
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          accept=".pdf,.txt,.md,.markdown,.docx,.pptx,.csv,.xlsx,.html,.htm"
        />

        <div className="p-4 bg-slate-800/80 rounded-full border border-slate-700 group-hover:scale-110 transition duration-300">
          <FiUpload className="text-purple-400 group-hover:text-pink-400 transition" size={32} />
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white group-hover:text-purple-300 transition">
            Drag & drop files here
          </h3>
          <p className="text-sm text-zinc-400 mt-1">
            or click to browse from your device
          </p>
        </div>

        <p className="text-xs text-zinc-500 uppercase tracking-widest mt-2">
          PDF, TXT, MD, DOCX, PPTX, CSV, XLSX, HTML (Max 10MB)
        </p>
      </motion.div>

      {/* Uploading File List */}
      <AnimatePresence>
        {uploadList.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-2xl border border-slate-700 bg-slate-950/80 p-5 space-y-4 shadow-xl backdrop-blur-lg"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-sm font-semibold text-white">Upload Queue</span>
              {showClearButton && (
                <button
                  onClick={clearCompleted}
                  className="text-xs font-semibold text-purple-400 hover:text-purple-300 hover:underline transition"
                >
                  Clear Finished
                </button>
              )}
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
              {uploadList.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="p-3 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2 flex flex-col"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <FiFile className="text-zinc-400 flex-shrink-0" size={18} />
                      <span className="text-sm text-white truncate font-medium">{item.file.name}</span>
                      <span className="text-xs text-zinc-500">
                        ({(item.file.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.status === "success" && (
                        <span className="text-xs font-medium text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                          ✓ Ready
                        </span>
                      )}
                      {item.status === "error" && (
                        <span className="text-xs font-medium text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/20">
                          ✕ Failed
                        </span>
                      )}
                      {item.status === "uploading" && (
                        <span className="text-xs font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20 animate-pulse">
                          {item.progress}%
                        </span>
                      )}
                      {item.status === "pending" && (
                        <span className="text-xs font-medium text-zinc-400 bg-slate-800 px-2 py-0.5 rounded-full">
                          Queued
                        </span>
                      )}
                    </div>
                  </div>

                  {item.status === "uploading" && (
                    <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  )}

                  {item.jobId && <JobStatus jobId={item.jobId} />}

                  {item.errorMsg && (
                    <p className="text-xs text-red-400 bg-red-950/20 p-2 rounded-lg border border-red-900/30">
                      Error: {item.errorMsg}
                    </p>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
