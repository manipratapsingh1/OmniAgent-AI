import { useState } from "react";
import { api, getErrorMessage } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";
import { useNotificationStore } from "../../store/notificationStore";
import { FiUpload, FiAlertCircle, FiCheckCircle } from "react-icons/fi";
import { motion } from "framer-motion";
import JobStatus from "./JobStatus";

export default function FileUpload({ onUploaded }: { onUploaded?: () => void }) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"success" | "error" | "info" | "">("");
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState<number | null>(null);
  const addNotification = useNotificationStore((s) => s.addNotification);

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

  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setMsg("File size exceeds 10MB limit");
      setMsgType("error");
      addNotification({ type: "error", message: "File too large (max 10MB)" });
      return;
    }

    // Validate file type.
    // Browsers are inconsistent about `file.type` (often empty or `application/octet-stream`).
    // Use both MIME type and file extension to avoid blocking valid uploads.
    const allowedMimeTypes = [
      "application/pdf",
      "text/plain",
      "text/markdown",
      "text/x-markdown",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "text/html",
      "application/octet-stream",
    ];
    const name = (file.name || "").toLowerCase();
    const allowedExtensions = [".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx", ".html", ".htm"];

    const hasAllowedExt = allowedExtensions.some((ext) => name.endsWith(ext));
    const hasAllowedMime = allowedMimeTypes.includes(file.type);

    if (!hasAllowedExt && !hasAllowedMime) {
      setMsg("Only PDF, TXT, MD, DOCX, PPTX, and HTML files are allowed");
      setMsgType("error");
      addNotification({ type: "error", message: "Invalid file type" });
      return;
    }


    setBusy(true);
    setMsg("");
    setProgress(0);

    try {
      const fd = new FormData();
      fd.append("file", file);

      const r = await api.post("/documents/upload_job", fd, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percentCompleted);
          }
        },
      });

      const jobId = r.data.job_id;
      setJobId(jobId || null);
      setMsg(`✓ Upload queued successfully${jobId ? ` (job ${jobId})` : ""}`);
      setMsgType("success");
      addNotification({
        type: "success",
        message: jobId
          ? `Document upload queued (job ${jobId}).` 
          : `Document upload queued successfully`,
      });
      onUploaded?.();

      // Clear message after 3 seconds
      setTimeout(() => {
        setMsg("");
        setMsgType("");
      }, 3000);
    } catch (err: any) {
      const errorMsg = getErrorMessage(err);
      setMsg(errorMsg);
      setMsgType("error");
      addNotification({ type: "error", message: `Upload failed: ${errorMsg}` });
    } finally {
      setBusy(false);
      setProgress(0);
      // Reset input
      e.target.value = "";
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-gradient-to-r from-slate-800/50 to-slate-800/30 rounded-xl border border-slate-700 backdrop-blur"
    >
      <label className="cursor-pointer block">
        <input
          type="file"
          className="hidden"
          onChange={onChange}
          accept=".pdf,.txt,.md,.markdown,.docx,.pptx,.html,.htm"
          disabled={busy}
        />
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <FiUpload className="text-purple-400" size={24} />
              <div>
                <p className="text-white font-medium">
                  {busy ? "Uploading..." : "Upload Documents"}
                </p>
                <p className="text-zinc-400 text-sm">
                  PDF, TXT, MD, DOCX, PPTX, HTML (Max 10MB)
                </p>
              </div>
            </div>
            {busy && progress > 0 && (
              <div className="mt-3 w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </div>

          <button
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            {busy ? "Uploading..." : "Select File"}
          </button>
        </div>
      </label>

      {/* Message display */}
      {msg && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${
            msgType === "success"
              ? "bg-green-900/30 text-green-300 border border-green-800"
              : msgType === "error"
              ? "bg-red-900/30 text-red-300 border border-red-800"
              : "bg-blue-900/30 text-blue-300 border border-blue-800"
          }`}
        >
          {msgType === "success" ? (
            <FiCheckCircle size={18} />
          ) : (
            <FiAlertCircle size={18} />
          )}
          <p className="text-sm">{msg}</p>
        </motion.div>
      )}
      {/* Job status */}
      {jobId && <JobStatus jobId={jobId} />}
    </motion.div>
  );
}

