import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import FileUpload from "../components/documents/FileUpload";
import { api, getErrorMessage } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import { usePolling } from "../hooks/usePolling";
import { jobService } from "../api/jobService";
import { FiLoader, FiTrash2, FiAlertTriangle, FiFileText, FiSearch, FiCpu, FiMessageSquare, FiX, FiActivity } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import type { BackgroundJob, Citation, DocumentItem } from "../api/types";

type DocumentChunkPreview = {
  id: number;
  chunk_index: number;
  text: string;
  vector_id?: string;
};

type DocumentPreviewResponse = {
  document: DocumentItem;
  chunks: DocumentChunkPreview[];
};

type SemanticResult = {
  chunk_text: string;
  chunk_index: number;
  document_id: number;
  filename: string;
  similarity_score: number;
};

export default function Documents() {
  useEffect(() => {
    document.title = "Documents | OmniAgent AI";
  }, []);

  const { user, loading: authLoading } = useAuth();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [question, setQuestion] = useState("");
  const [selectedDocId, setSelectedDocId] = useState<number | undefined>(undefined);
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaSources, setQaSources] = useState<Citation[]>([]);
  const [qaLoading, setQaLoading] = useState(false);
  const [qaError, setQaError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DocumentItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [semanticQuery, setSemanticQuery] = useState("");
  const [semanticResults, setSemanticResults] = useState<SemanticResult[]>([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [previewingDoc, setPreviewingDoc] = useState<DocumentItem | null>(null);
  const [previewChunks, setPreviewChunks] = useState<DocumentChunkPreview[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [jobFilter, setJobFilter] = useState<string>("all");
  const [cancellingJobId, setCancellingJobId] = useState<number | null>(null);
  const [searchTab, setSearchTab] = useState<"filename" | "semantic">("filename");

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { data: jobs, loading: jobsLoading, error: jobsError, refetch: refetchJobs } = usePolling<BackgroundJob[]>(
    () => jobService.getJobs(0, 20),
    {
      interval: 5000,
      enabled: true,
      onError: (error) => {
        const message = error instanceof Error ? error.message : "Unable to refresh job status";
        addNotification({ type: "error", message });
      },
      initialData: [],
    }
  );

  const load = async () => {
    try {
      setLoading(true);
      const r = await api.get<DocumentItem[]>("/documents/");
      setDocs(r.data || []);
    } catch (err) {
      const msg = getErrorMessage(err);
      if (msg.includes("403") || msg.includes("Forbidden")) {
        addNotification({ type: "error", message: "Admin access required to view documents" });
      } else {
        addNotification({ type: "error", message: `Failed to load documents: ${msg}` });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      load();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  const deleteDoc = async (id: number) => {
    if (!user?.is_admin && user?.role !== 'admin') {
      addNotification({ type: "error", message: "Only admins can delete documents" });
      return;
    }

    if (!window.confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      setDeleting(id);
      await api.delete(`/documents/${id}`);
      addNotification({ type: "success", message: "Document deleted successfully" });
      await load();
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to delete document: ${msg}` });
    } finally {
      setDeleting(null);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      setQaError("Please enter a question.");
      return;
    }

    setQaLoading(true);
    setQaError("");
    setQaAnswer("");
    setQaSources([]);

    try {
      const response = await api.post("/documents/qa", {
        question: question.trim(),
        document_id: selectedDocId,
        k: 5,
      });

      setQaAnswer(response.data.content || "");
      setQaSources(response.data.sources || []);
      setQuestion("");
    } catch (error) {
      const message = getErrorMessage(error);
      setQaError(message);
      addNotification({ type: "error", message: `QA request failed: ${message}` });
    } finally {
      setQaLoading(false);
    }
  };

  const cancelJob = async (jobId: number) => {
    setCancellingJobId(jobId);
    try {
      await jobService.cancelJob(jobId);
      addNotification({ type: "success", message: "Job cancelled successfully." });
      refetchJobs();
    } catch (error) {
      addNotification({ type: "error", message: `Unable to cancel job: ${getErrorMessage(error)}` });
    } finally {
      setCancellingJobId(null);
    }
  };

  const filteredJobs = jobs?.filter((job) => {
    if (jobFilter === "all") return true;
    return job.status === jobFilter;
  }) || [];

  const searchDocuments = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await api.get<DocumentItem[]>("/documents/search", {
        params: { q: searchQuery.trim() },
      });
      setSearchResults(response.data || []);
    } catch (error) {
      addNotification({ type: "error", message: `Document search failed: ${getErrorMessage(error)}` });
    } finally {
      setSearchLoading(false);
    }
  };

  const semanticSearch = async () => {
    if (!semanticQuery.trim()) {
      setSemanticResults([]);
      return;
    }

    setSemanticLoading(true);
    try {
      const response = await api.get<SemanticResult[]>("/documents/rag-search", {
        params: { q: semanticQuery.trim(), k: 6 },
      });
      setSemanticResults(response.data || []);
    } catch (error) {
      addNotification({ type: "error", message: `Semantic search failed: ${getErrorMessage(error)}` });
    } finally {
      setSemanticLoading(false);
    }
  };

  const previewDocument = async (doc: DocumentItem) => {
    setPreviewLoading(true);
    setPreviewingDoc(null);
    setPreviewChunks([]);
    try {
      const response = await api.get<DocumentPreviewResponse>(`/documents/${doc.id}/preview`);
      setPreviewingDoc(response.data.document);
      setPreviewChunks(response.data.chunks || []);
    } catch (error) {
      addNotification({ type: "error", message: `Failed to load preview: ${getErrorMessage(error)}` });
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewingDoc(null);
    setPreviewChunks([]);
  };

  return (
    <MainLayout>
      <main className="relative z-10 flex-1 p-8 overflow-y-auto scrollbar-thin">
        {/* Header Section */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="mb-8">
            <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-2">Documents</h1>
            <p className="text-lg text-zinc-400">Upload and manage your documents for RAG retrieval</p>
          </div>
        </motion.div>

        {/* Upload Section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="mb-8">
          <div className="glass-panel p-6">
            <FileUpload onUploaded={() => {
              load();
              refetchJobs();
            }} />
          </div>
        </motion.div>

        {/* Background Job Status */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }} className="mb-8">
          <div className="glass-panel p-6 border border-zinc-800 bg-zinc-950/40 relative overflow-hidden group">
            {/* Ambient light overlay */}
            <div className="absolute -inset-px bg-gradient-to-r from-purple-500/10 via-transparent to-pink-500/10 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 relative z-10">
              <div>
                <div className="flex items-center gap-2">
                  <FiActivity className="text-purple-400 animate-pulse" />
                  <h2 className="text-xl font-bold text-white tracking-wide">Ingestion Jobs</h2>
                </div>
                <p className="text-zinc-400 text-sm mt-1">Track real-time background processing for document embeddings.</p>
              </div>
              <div className="flex items-center gap-3">
                <label htmlFor="job-filter-select" className="sr-only">Job filter</label>
                <select
                  id="job-filter-select"
                  value={jobFilter}
                  onChange={(e) => setJobFilter(e.target.value)}
                  className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-purple-500 focus:outline-none transition"
                >
                  <option value="all">All Jobs</option>
                  <option value="pending">Pending</option>
                  <option value="processing">Processing</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
                {jobsLoading && <FiLoader className="animate-spin text-purple-400 text-xs" />}
              </div>
            </div>
            {jobs && jobs.length > 0 ? (
              <div className="space-y-3 relative z-10">
                {filteredJobs.map((job) => (
                  <div key={job.id} className="rounded-xl border border-zinc-900 bg-zinc-900/40 hover:bg-zinc-900/60 p-4 transition duration-300 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-xs text-zinc-500 font-mono">Job #{job.id}</span>
                        <span className="text-xs text-zinc-400 font-medium bg-zinc-850 px-2 py-0.5 rounded font-mono capitalize">{job.job_type}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          job.status === 'completed' ? 'bg-green-400' :
                          job.status === 'failed' ? 'bg-red-400 animate-pulse' :
                          job.status === 'processing' ? 'bg-blue-400 animate-ping' :
                          'bg-zinc-400'
                        }`} />
                        <span className="text-sm font-semibold text-zinc-200 capitalize">{job.status}</span>
                      </div>
                      {job.error && (
                        <p className="text-xs text-red-400 bg-red-950/20 border border-red-900/20 px-3 py-1.5 rounded-lg mt-2 font-mono">
                          {job.error}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <div className="flex flex-col items-end gap-1">
                        <div className="w-24 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              job.status === 'completed' ? 'bg-green-500' :
                              job.status === 'failed' ? 'bg-red-500' :
                              'bg-gradient-to-r from-purple-500 to-pink-500'
                            }`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-zinc-400">{job.progress}%</span>
                      </div>
                      <span className="text-xs text-zinc-500 font-mono hidden sm:inline">{new Date(job.created_at).toLocaleTimeString()}</span>
                      { (job.status === 'pending' || job.status === 'processing') && (
                        <button
                          type="button"
                          onClick={() => cancelJob(job.id)}
                          disabled={cancellingJobId === job.id}
                          className="rounded-xl border border-red-950 bg-red-900/10 px-3 py-1.5 text-xs font-bold text-red-400 hover:bg-red-900/20 disabled:opacity-50 transition"
                        >
                          {cancellingJobId === job.id ? 'Stopping...' : 'Cancel'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-8 text-center text-zinc-500 relative z-10">
                {jobsLoading ? "Checking jobs..." : "No active ingestion jobs queued."}
              </div>
            )}
          </div>
        </motion.div>

        {/* Unified Search Section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.18 }} className="mb-8">
          <div className="glass-panel p-6 border border-zinc-800 bg-zinc-950/40 relative">
            <div className="flex items-center gap-1.5 border-b border-zinc-850 pb-4 mb-6">
              <button
                onClick={() => setSearchTab("filename")}
                className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 ${
                  searchTab === "filename"
                    ? "bg-zinc-850 text-white shadow-lg"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <FiSearch size={16} />
                Filename Search
              </button>
              <button
                onClick={() => setSearchTab("semantic")}
                className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 ${
                  searchTab === "semantic"
                    ? "bg-zinc-850 text-white shadow-lg border border-purple-900/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <FiCpu size={16} className={searchTab === "semantic" ? "text-purple-400" : ""} />
                Semantic RAG Search
              </button>
            </div>

            {searchTab === "filename" ? (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                  <div className="relative">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <input
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      onKeyDown={(event) => event.key === "Enter" && searchDocuments()}
                      placeholder="Search files by name..."
                      className="w-full pl-11 pr-4 py-3 rounded-xl border border-zinc-800 bg-zinc-900/40 text-white text-sm outline-none focus:border-purple-500 transition"
                    />
                  </div>
                  <button
                    onClick={searchDocuments}
                    disabled={searchLoading}
                    className="rounded-xl bg-purple-600 hover:bg-purple-500 px-6 py-3 font-semibold text-sm text-white transition disabled:opacity-50 shadow-lg shadow-purple-600/20"
                  >
                    {searchLoading ? "Searching..." : "Search Files"}
                  </button>
                </div>
                {searchResults.length > 0 ? (
                  <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-4 space-y-2">
                    <p className="text-xs text-zinc-500 font-mono tracking-wider uppercase mb-3">Matching documents</p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {searchResults.map((result) => (
                        <button
                          key={result.id}
                          onClick={() => previewDocument(result)}
                          className="text-left rounded-xl border border-zinc-900 hover:border-zinc-855 bg-zinc-955/60 hover:bg-zinc-955 px-4 py-3 text-white transition flex flex-col justify-between group"
                        >
                          <span className="font-semibold text-sm group-hover:text-purple-300 transition truncate w-full">{result.filename}</span>
                          <div className="flex items-center justify-between w-full mt-2 text-xs text-zinc-500">
                            <span>{result.chunk_count ?? 0} chunks</span>
                            <span className="capitalize bg-zinc-900 px-2 py-0.5 rounded font-mono text-[10px]">{result.status}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : searchQuery.trim() && !searchLoading && (
                  <p className="text-sm text-zinc-500 text-center py-4">No matching filenames found.</p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                  <div className="relative">
                    <FiCpu className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <input
                      value={semanticQuery}
                      onChange={(event) => setSemanticQuery(event.target.value)}
                      onKeyDown={(event) => event.key === "Enter" && semanticSearch()}
                      placeholder="Ask/search concepts inside document contents..."
                      className="w-full pl-11 pr-4 py-3 rounded-xl border border-zinc-800 bg-zinc-900/40 text-white text-sm outline-none focus:border-pink-500 transition"
                    />
                  </div>
                  <button
                    onClick={semanticSearch}
                    disabled={semanticLoading}
                    className="rounded-xl bg-pink-600 hover:bg-pink-500 px-6 py-3 font-semibold text-sm text-white transition disabled:opacity-50 shadow-lg shadow-pink-600/20"
                  >
                    {semanticLoading ? "Analyzing..." : "RAG Search"}
                  </button>
                </div>
                {semanticResults.length > 0 ? (
                  <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-4 space-y-3">
                    <p className="text-xs text-zinc-500 font-mono tracking-wider uppercase mb-3">Relevant Passage Matches</p>
                    <div className="space-y-3">
                      {semanticResults.map((item, index) => (
                        <div key={`${item.document_id}-${index}`} className="rounded-xl border border-zinc-900 bg-zinc-950/60 p-4 hover:border-zinc-850 transition">
                          <div className="flex items-center justify-between gap-3 mb-2 pb-2 border-b border-zinc-900/60">
                            <span className="text-xs font-semibold text-zinc-300 truncate font-sans">{item.filename}</span>
                            <span className="rounded-full bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 text-[10px] font-semibold text-purple-300 font-mono">
                              Match {item.similarity_score.toFixed(3)}
                            </span>
                          </div>
                          <p className="text-sm text-zinc-300 leading-6 font-sans italic">&quot;{item.chunk_text}&quot;</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : semanticQuery.trim() && !semanticLoading && (
                  <p className="text-sm text-zinc-500 text-center py-4">No relevant passages found for this concept.</p>
                )}
              </div>
            )}
          </div>
        </motion.div>

        {/* Document QA Section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="mb-8">
          <div className="glass-panel p-6 border border-zinc-800 bg-zinc-950/40 relative group">
            {/* Glow effect */}
            <div className="absolute -inset-px bg-gradient-to-r from-purple-500/5 to-pink-500/5 rounded-2xl opacity-100 group-hover:opacity-100 transition duration-700 pointer-events-none" />
            
            <div className="mb-6 relative z-10 flex items-center gap-2">
              <FiMessageSquare className="text-pink-400" />
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">Ask Document Assistant</h2>
                <p className="text-zinc-400 text-sm mt-0.5">Generate direct conceptual answers extracted directly from your index.</p>
              </div>
            </div>
            
            <div className="grid gap-4 md:grid-cols-[1fr_260px] relative z-10">
              <div className="relative flex">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="What would you like to ask or analyze about the documents?"
                  className="min-h-[140px] w-full rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-white text-sm focus:border-purple-500 focus:outline-none resize-none transition"
                />
              </div>
              <div className="space-y-4">
                <div>
                  <label htmlFor="qa-doc-filter" className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Scope Filter</label>
                  <select
                    id="qa-doc-filter"
                    value={selectedDocId ?? ""}
                    onChange={(event) => setSelectedDocId(event.target.value ? Number(event.target.value) : undefined)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-white focus:border-purple-500 focus:outline-none transition"
                  >
                    <option value="">All indexed documents</option>
                    {docs.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.filename}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleAskQuestion}
                  disabled={qaLoading}
                  className="w-full rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 px-4 py-3 text-sm font-bold text-white transition disabled:opacity-50 shadow-lg shadow-purple-600/10 cursor-pointer"
                >
                  {qaLoading ? "Synthesizing..." : "Ask Assistant"}
                </button>
                {qaError && <p className="text-xs text-red-400 font-mono">{qaError}</p>}
              </div>
            </div>

            {qaAnswer && (
              <div className="mt-6 rounded-xl border border-zinc-850 bg-zinc-900/30 p-5 relative z-10">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">Synthesized Answer</h3>
                <p className="whitespace-pre-wrap text-zinc-100 text-sm leading-7 font-sans">{qaAnswer}</p>
                {qaSources.length > 0 && (
                  <div className="mt-5 border-t border-zinc-850 pt-4">
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Document Citations</h4>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {qaSources.map((source, idx) => (
                        <div key={idx} className="rounded-xl bg-zinc-950/80 border border-zinc-900/60 p-3.5 hover:border-zinc-800 transition">
                          <p className="text-xs font-semibold text-purple-400 font-mono mb-1.5">
                            Doc #{source.document_id} · Chunk {source.chunk_index}
                          </p>
                          <p className="text-xs text-zinc-400 leading-5 italic">&quot;{source.snippet}&quot;</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>

        {/* Documents List Section */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <div className="flex items-center gap-2 mb-6">
            <div className="h-1.5 w-1.5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"></div>
            <h2 className="text-xl font-semibold text-white tracking-wide">Your Documents ({docs.length})</h2>
          </div>

          {loading ? (
            <div className="glass-panel p-12 flex items-center justify-center border border-zinc-900">
              <div className="flex flex-col items-center gap-3">
                <FiLoader className="animate-spin text-purple-400" size={32} />
                <span className="text-zinc-400 text-sm">Loading document inventory...</span>
              </div>
            </div>
          ) : docs.length === 0 ? (
            <div className="glass-panel p-12 text-center border border-zinc-900">
              <FiFileText className="mx-auto mb-4 text-zinc-500" size={48} />
              <h3 className="text-lg font-semibold text-white mb-2">No documents yet</h3>
              <p className="text-zinc-400 text-sm">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map((d, idx) => (
                <motion.div
                  key={d.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="rounded-xl border border-zinc-900 hover:border-zinc-800 bg-zinc-955/40 hover:bg-zinc-955/60 p-4 transition duration-300 group hover:shadow-lg hover:shadow-purple-95/5"
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* Document Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 group-hover:border-zinc-700 transition">
                          <FiFileText className="text-purple-400" size={18} />
                        </div>
                        <h3 className="font-semibold text-white text-base truncate">{d.filename}</h3>
                      </div>
                      
                      <div className="flex flex-wrap gap-3 items-center mb-1 ml-12">
                        <span className="text-xs text-zinc-400 bg-zinc-900 px-2.5 py-1 rounded-md border border-zinc-850">
                          {(d.size_bytes / 1024).toFixed(1)} KB
                        </span>
                        <span className="text-xs text-zinc-500">•</span>
                        <span className="text-xs text-zinc-400">{d.mime_type}</span>
                        {(d.chunk_count ?? 0) > 0 && (
                          <>
                            <span className="text-xs text-zinc-500">•</span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                              <span className="text-xs text-purple-300 font-semibold">{d.chunk_count} chunks indexed</span>
                            </span>
                          </>
                        )}
                      </div>

                      {/* Error Message */}
                      {d.error_message && (
                        <div className="ml-12 mt-3 p-3 bg-red-955/10 border border-red-900/20 rounded-lg">
                          <div className="flex items-start gap-2">
                            <FiAlertTriangle size={16} className="flex-shrink-0 mt-0.5 text-red-400" />
                            <span className="text-xs text-red-300">{d.error_message}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Status Badge & Actions */}
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider border ${
                        d.status === 'indexed' ? 'bg-green-950/20 text-green-300 border-green-900/30' :
                        d.status === 'processing' ? 'bg-blue-900/20 text-blue-300 border-blue-900/30 animate-pulse' :
                        d.status === 'failed' ? 'bg-red-955/20 text-red-300 border-red-900/30' :
                        'bg-zinc-900 text-zinc-400 border-zinc-800'
                      }`}>
                        {d.status === 'indexed' && '✓ Indexed'}
                        {d.status === 'processing' && '⟳ Ingesting'}
                        {d.status === 'failed' && '✕ Failed'}
                      </span>
                      
                      <button
                        onClick={() => previewDocument(d)}
                        disabled={previewLoading}
                        className="rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 px-4 py-2 text-xs font-semibold text-zinc-200 hover:text-white transition"
                        title="Preview document chunks"
                      >
                        {previewLoading && previewingDoc?.id === d.id ? "Loading..." : "Preview"}
                      </button>
                      <button
                        onClick={() => deleteDoc(d.id)}
                        disabled={deleting === d.id}
                        className="p-2 rounded-lg hover:bg-red-900/20 border border-transparent hover:border-red-900/30 text-red-400 transition"
                        title="Delete document (Admin only)"
                      >
                        {deleting === d.id ? (
                          <FiLoader className="animate-spin" size={18} />
                        ) : (
                          <FiTrash2 size={18} />
                        )}
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Premium slide-out chunk preview drawer */}
        <AnimatePresence>
          {previewingDoc && (
            <>
              {/* Dark backdrop overlay */}
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-45 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
                onClick={closePreview}
              />
              
              {/* Slide-out drawer */}
              <motion.div 
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 220 }}
                className="fixed inset-y-0 right-0 z-50 w-full max-w-2xl bg-zinc-950 border-l border-zinc-850 p-6 shadow-2xl flex flex-col h-full overflow-hidden"
              >
                <div className="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-zinc-900">
                  <div className="min-w-0">
                    <h2 className="text-lg font-bold text-white truncate" title={previewingDoc.filename}>
                      Preview: {previewingDoc.filename}
                    </h2>
                    <p className="text-xs text-zinc-400 mt-1">Showing first indexed document chunks</p>
                  </div>
                  <button
                    onClick={closePreview}
                    className="p-2 rounded-lg hover:bg-zinc-900 border border-transparent hover:border-zinc-800 text-zinc-400 hover:text-zinc-200 transition"
                  >
                    <FiX size={20} />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto pr-1 space-y-4 scrollbar-thin">
                  {previewLoading ? (
                    <div className="p-12 text-center text-zinc-400 flex flex-col items-center gap-3">
                      <FiLoader className="animate-spin text-purple-400" size={28} />
                      <span className="text-sm">Retrieving indexed chunks...</span>
                    </div>
                  ) : previewChunks.length === 0 ? (
                    <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 text-center text-zinc-400 text-sm">
                      No chunks available for preview.
                    </div>
                  ) : (
                    previewChunks.map((chunk) => (
                      <div key={chunk.id} className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-4 hover:border-zinc-850 transition">
                        <div className="flex items-center justify-between gap-4 mb-2.5 text-xs font-semibold text-zinc-500 uppercase tracking-widest">
                          <span>Chunk {chunk.chunk_index}</span>
                          <span className="text-[10px] bg-zinc-900 px-2 py-0.5 rounded text-zinc-400 font-mono">
                            {chunk.vector_id ? `Vector ${chunk.vector_id}` : "Indexed"}
                          </span>
                        </div>
                        <p className="text-sm leading-6 text-zinc-300 whitespace-pre-wrap font-sans">{chunk.text}</p>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </main>
    </MainLayout>
  );
}



