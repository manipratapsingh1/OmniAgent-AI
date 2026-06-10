import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import FileUpload from "../components/documents/FileUpload";
import { api, getErrorMessage } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import { usePolling } from "../hooks/usePolling";
import { jobService } from "../api/jobService";
import { FiLoader, FiTrash2, FiAlertTriangle, FiLock, FiFileText, FiDownload, FiCheck } from "react-icons/fi";
import { motion } from "framer-motion";
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

  const statusStyles = {
    indexed: "bg-green-900/30 text-green-300 border border-green-800",
    failed: "bg-red-900/30 text-red-300 border border-red-800",
    processing: "bg-blue-900/30 text-blue-300 border border-blue-800",
    pending: "bg-slate-800/30 text-slate-300 border border-slate-700",
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
          <div className="glass-panel p-6">
              <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-white">Ingestion Jobs</h2>
                <p className="text-zinc-400 text-sm">Monitor document ingestion progress for queued uploads.</p>
              </div>
              <div className="flex items-center gap-3">
                <label htmlFor="job-filter-select" className="sr-only">
                  Job filter
                </label>
                <select
                  id="job-filter-select"
                  value={jobFilter}
                  onChange={(e) => setJobFilter(e.target.value)}
                  className="rounded-2xl border border-slate-700 bg-slate-950/80 p-2 text-sm text-white"
                >
                  <option value="all">All</option>
                  <option value="pending">Pending</option>
                  <option value="processing">Processing</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
                {jobsLoading && <span className="text-sm text-blue-300">Refreshing...</span>}
              </div>
            </div>
            {jobs && jobs.length > 0 ? (
              <div className="space-y-3">
                {filteredJobs.map((job) => (
                  <div key={job.id} className="rounded-xl border border-slate-700 bg-slate-950/80 p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-zinc-400">Job #{job.id} · {job.job_type}</p>
                      <p className="text-white">Status: <span className="font-semibold">{job.status}</span></p>
                      {job.error && <p className="text-sm text-red-400">Error: {job.error}</p>}
                    </div>
                    <div className="inline-flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs uppercase tracking-[0.12em] ${
                        job.status === 'completed' ? 'bg-green-900/30 text-green-300' :
                        job.status === 'failed' ? 'bg-red-900/30 text-red-300' :
                        job.status === 'processing' ? 'bg-blue-900/30 text-blue-300' :
                        'bg-slate-800/30 text-slate-300'
                      }`}>
                        {job.progress}%
                      </span>
                      <span className="text-xs text-zinc-500">Updated: {new Date(job.created_at).toLocaleString()}</span>
                      { (job.status === 'pending' || job.status === 'processing') && (
                        <button
                          type="button"
                          onClick={() => cancelJob(job.id)}
                          disabled={cancellingJobId === job.id}
                          className="ml-2 rounded-md bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-500 disabled:opacity-50"
                        >
                          {cancellingJobId === job.id ? 'Cancelling...' : 'Cancel'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-slate-700 bg-slate-950/80 p-6 text-center text-zinc-400">
                {jobsLoading ? "Loading jobs..." : "No ingestion jobs queued right now."}
              </div>
            )}
          </div>
        </motion.div>

        {/* Document Search + Preview Section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.18 }} className="mb-8">
          <div className="glass-panel p-6">
            <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
              <div>
                <h2 className="text-xl font-semibold text-white">Search documents</h2>
                <p className="text-zinc-400 text-sm mb-4">Search by filename or explore content with semantic RAG search.</p>
                <div className="space-y-3">
                  <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                    <input
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Search by filename..."
                      className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 p-3 text-white outline-none focus:border-purple-500"
                    />
                    <button
                      onClick={searchDocuments}
                      disabled={searchLoading}
                      className="rounded-2xl bg-purple-600 px-4 py-3 font-semibold text-white transition hover:bg-purple-500 disabled:opacity-50"
                    >
                      {searchLoading ? "Searching..." : "Search"}
                    </button>
                  </div>
                  {searchResults.length > 0 && (
                    <div className="rounded-2xl border border-slate-700 bg-slate-950/80 p-4">
                      <p className="text-sm text-zinc-400 mb-3">Filename search results</p>
                      <div className="space-y-2">
                        {searchResults.map((result) => (
                          <button
                            key={result.id}
                            onClick={() => previewDocument(result)}
                            className="w-full text-left rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-white hover:bg-slate-900 transition"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span>{result.filename}</span>
                              <span className="text-xs text-zinc-400">{result.status}</span>
                            </div>
                            <p className="text-xs text-zinc-500 mt-1">{result.chunk_count ?? 0} chunks</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-semibold text-white">Semantic content search</h2>
                <p className="text-zinc-400 text-sm mb-4">Find relevant passages across your documents using embedded search.</p>
                <div className="space-y-3">
                  <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                    <input
                      value={semanticQuery}
                      onChange={(event) => setSemanticQuery(event.target.value)}
                      placeholder="Search inside documents..."
                      className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 p-3 text-white outline-none focus:border-pink-500"
                    />
                    <button
                      onClick={semanticSearch}
                      disabled={semanticLoading}
                      className="rounded-2xl bg-pink-600 px-4 py-3 font-semibold text-white transition hover:bg-pink-500 disabled:opacity-50"
                    >
                      {semanticLoading ? "Searching..." : "Search"}
                    </button>
                  </div>
                  {semanticResults.length > 0 && (
                    <div className="rounded-2xl border border-slate-700 bg-slate-950/80 p-4">
                      <p className="text-sm text-zinc-400 mb-3">Semantic search results</p>
                      <div className="space-y-3">
                        {semanticResults.map((item, index) => (
                          <div key={`${item.document_id}-${index}`} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-sm text-zinc-300">
                              <span>{item.filename}</span>
                              <span className="rounded-full bg-slate-800/80 px-2 py-1 text-xs text-zinc-400">Score {item.similarity_score.toFixed(3)}</span>
                            </div>
                            <p className="text-sm text-zinc-200 leading-6">{item.chunk_text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Document QA Section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="mb-8">
          <div className="glass-panel p-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-white">Ask a question</h2>
              <p className="text-zinc-400 text-sm">Ask about your indexed documents. Optionally choose a single document for a narrow answer.</p>
            </div>
            <div className="grid gap-4 md:grid-cols-[1fr_240px]">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What do you want to know about your documents?"
                className="min-h-[140px] w-full rounded-2xl border border-slate-700 bg-slate-950/70 p-4 text-white focus:border-purple-500 focus:outline-none"
              />
              <div className="space-y-4">
                <label className="block text-sm font-medium text-zinc-300">Document Filter</label>
                <select
                  aria-label="Document filter"
                  value={selectedDocId ?? ""}
                  onChange={(event) => setSelectedDocId(event.target.value ? Number(event.target.value) : undefined)}
                  className="w-full rounded-2xl border border-slate-700 bg-slate-950/70 p-3 text-white focus:border-purple-500 focus:outline-none"
                >
                  <option value="">All indexed documents</option>
                  {docs.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAskQuestion}
                  disabled={qaLoading}
                  className="w-full rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-3 text-sm font-semibold text-white transition hover:from-purple-600 hover:to-pink-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {qaLoading ? "Asking..." : "Get Answer"}
                </button>
                {qaError && <p className="text-sm text-red-400">{qaError}</p>}
              </div>
            </div>

            {qaAnswer && (
              <div className="mt-6 rounded-2xl border border-slate-700 bg-slate-950/80 p-5">
                <h3 className="text-lg font-semibold text-white mb-3">Answer</h3>
                <p className="whitespace-pre-wrap text-zinc-100">{qaAnswer}</p>
                {qaSources.length > 0 && (
                  <div className="mt-4 border-t border-slate-700 pt-4">
                    <h4 className="text-sm font-medium text-zinc-300 mb-2">Sources</h4>
                    <ul className="space-y-2 text-sm text-zinc-400">
                      {qaSources.map((source, idx) => (
                        <li key={idx} className="rounded-xl bg-slate-900/60 p-3">
                          <p className="text-zinc-200">Document #{source.document_id} · Chunk {source.chunk_index}</p>
                          <p>{source.snippet}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>

        {/* Documents List Section */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <div className="flex items-center gap-2 mb-6">
            <div className="h-1 w-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"></div>
            <h2 className="text-xl font-semibold text-white">Your Documents ({docs.length})</h2>
          </div>

          {loading ? (
            <div className="glass-panel p-12 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <FiLoader className="animate-spin text-blue-400" size={32} />
                <span className="text-zinc-400">Loading documents...</span>
              </div>
            </div>
          ) : docs.length === 0 ? (
            <div className="glass-panel p-12 text-center">
              <FiFileText className="mx-auto mb-4 text-zinc-500" size={48} />
              <h3 className="text-lg font-semibold text-white mb-2">No documents yet</h3>
              <p className="text-zinc-400">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map((d, idx) => (
                <motion.div
                  key={d.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="card group hover:border-slate-600/70 hover:shadow-card-hover"
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* Document Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-600/30 to-purple-700/30 group-hover:from-purple-600/40 group-hover:to-purple-700/40 transition">
                          <FiFileText className="text-purple-400" size={18} />
                        </div>
                        <h3 className="font-semibold text-white text-lg truncate">{d.filename}</h3>
                      </div>
                      
                      <div className="flex flex-wrap gap-3 items-center mb-3 ml-11">
                        <span className="text-sm text-zinc-400 bg-slate-800/50 px-2.5 py-1 rounded-md">
                          {(d.size_bytes / 1024).toFixed(1)} KB
                        </span>
                        <span className="text-sm text-zinc-500">•</span>
                        <span className="text-sm text-zinc-400">{d.mime_type}</span>
                        {(d.chunk_count ?? 0) > 0 && (
                          <>
                            <span className="text-sm text-zinc-500">•</span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-900/20 border border-blue-800/50">
                              <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
                              <span className="text-sm text-blue-300">{d.chunk_count} chunks indexed</span>
                            </span>
                          </>
                        )}
                      </div>

                      {/* Error Message */}
                      {d.error_message && (
                        <div className="ml-11 mt-3 p-3 bg-red-900/20 border border-red-800/50 rounded-lg">
                          <div className="flex items-start gap-2">
                            <FiAlertTriangle size={16} className="flex-shrink-0 mt-0.5 text-red-400" />
                            <span className="text-sm text-red-300">{d.error_message}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Status Badge & Actions */}
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className={`badge whitespace-nowrap ${
                        statusStyles[d.status as keyof typeof statusStyles] || "bg-slate-700/30 text-zinc-300 border-slate-600/50"
                      }`}>
                        {d.status === 'indexed' && '✓ Indexed'}
                        {d.status === 'processing' && '⟳ Processing'}
                        {d.status === 'failed' && '✕ Failed'}
                      </span>
                      
                        <button
                        onClick={() => previewDocument(d)}
                        disabled={previewLoading}
                        className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs font-semibold text-white transition hover:border-slate-500 hover:bg-slate-800"
                        title="Preview document chunks"
                      >
                        {previewLoading && previewingDoc?.id === d.id ? "Loading" : "Preview"}
                      </button>
                      <button
                        onClick={() => deleteDoc(d.id)}
                        disabled={deleting === d.id}
                        className="p-2.5 rounded-lg hover:bg-red-500/20 transition text-red-400 disabled:opacity-50 disabled:cursor-not-allowed border border-transparent hover:border-red-600/50 group/btn"
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

          {previewingDoc && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }} className="glass-panel p-6 mt-8">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">Preview: {previewingDoc.filename}</h2>
                  <p className="text-sm text-zinc-400">Showing the first chunks from the document index.</p>
                </div>
                <button
                  onClick={closePreview}
                  className="rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-sm text-white hover:border-slate-500"
                >
                  Close preview
                </button>
              </div>

              {previewLoading ? (
                <div className="rounded-2xl border border-slate-700 bg-slate-950/80 p-8 text-center text-zinc-400">
                  Loading preview...
                </div>
              ) : (
                <div className="space-y-4">
                  {previewChunks.length === 0 ? (
                    <div className="rounded-2xl border border-slate-700 bg-slate-950/80 p-6 text-zinc-400">
                      No preview chunks available for this document.
                    </div>
                  ) : (
                    previewChunks.map((chunk) => (
                      <div key={chunk.id} className="rounded-2xl border border-slate-700 bg-slate-900/80 p-4">
                        <div className="flex items-center justify-between gap-4 mb-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
                          <span>Chunk {chunk.chunk_index}</span>
                          <span>{chunk.vector_id ? `Vector ${chunk.vector_id}` : "Indexed chunk"}</span>
                        </div>
                        <p className="text-sm leading-7 text-zinc-200 whitespace-pre-wrap">{chunk.text}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </motion.div>
          )}
        </main>
    </MainLayout>
  );
}




