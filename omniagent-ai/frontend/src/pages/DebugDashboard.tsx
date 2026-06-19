import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { api, getErrorMessage } from "../api/client";
import Loading from "../components/common/Loading";
import { FiRefreshCw } from "react-icons/fi";

interface DebugStatus {
  timestamp: string;
  perf_metrics: Record<string, unknown>;
  cache: Record<string, unknown>;
  jobs: {
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
  memory: {
    per_user: {
      short_term: number;
      long_term: number;
    };
    global: {
      short_term: number;
      long_term: number;
    };
  };
  current_user: { id: number; email: string };
}

export default function DebugDashboard() {
  const [debugStatus, setDebugStatus] = useState<DebugStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get<DebugStatus>("/debug/status");
      setDebugStatus(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    document.title = "Debug status | OmniAgent AI";
    loadStatus();
    const interval = window.setInterval(loadStatus, 30000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <MainLayout>
      <div className="w-full p-6 lg:p-8 max-w-6xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Debug Dashboard</h1>
            <p className="text-zinc-400 max-w-2xl">Live diagnostics for request performance, cache state, background jobs, and memory activity.</p>
          </div>
          <button
            onClick={loadStatus}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2 text-sm text-zinc-200 hover:bg-slate-800 transition"
          >
            <FiRefreshCw /> Refresh
          </button>
        </div>

        {loading ? (
          <Loading message="Loading debug status..." fullScreen={false} />
        ) : error ? (
          <div className="rounded-2xl border border-red-600/30 bg-red-950/50 px-6 py-5 text-red-200">
            <p className="font-semibold">Failed to load debug status</p>
            <p>{error}</p>
          </div>
        ) : debugStatus ? (
          <div className="space-y-6">
            <section className="grid gap-4 lg:grid-cols-3">
              <div className="glass-panel p-6 rounded-2xl border border-slate-700/40">
                <p className="text-sm font-semibold text-zinc-400 uppercase tracking-[0.18em] mb-4">Current User</p>
                <p className="text-white text-lg font-semibold">{debugStatus.current_user.email}</p>
                <p className="text-zinc-400 text-sm">ID: {debugStatus.current_user.id}</p>
                <p className="mt-3 text-zinc-500 text-sm">Updated: {new Date(debugStatus.timestamp).toLocaleString()}</p>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-700/40">
                <p className="text-sm font-semibold text-zinc-400 uppercase tracking-[0.18em] mb-4">Background Jobs</p>
                <div className="grid grid-cols-2 gap-4 text-sm text-zinc-200">
                  <div className="rounded-xl bg-slate-950/60 p-3">
                    <p className="text-zinc-400 text-xs uppercase tracking-[0.18em] mb-2">Total</p>
                    <p className="text-3xl font-semibold text-white">{debugStatus.jobs.total}</p>
                  </div>
                  <div className="rounded-xl bg-slate-950/60 p-3">
                    <p className="text-zinc-400 text-xs uppercase tracking-[0.18em] mb-2">Pending</p>
                    <p className="text-3xl font-semibold text-blue-300">{debugStatus.jobs.pending}</p>
                  </div>
                  <div className="rounded-xl bg-slate-950/60 p-3">
                    <p className="text-zinc-400 text-xs uppercase tracking-[0.18em] mb-2">Processing</p>
                    <p className="text-3xl font-semibold text-amber-300">{debugStatus.jobs.processing}</p>
                  </div>
                  <div className="rounded-xl bg-slate-950/60 p-3">
                    <p className="text-zinc-400 text-xs uppercase tracking-[0.18em] mb-2">Failed</p>
                    <p className="text-3xl font-semibold text-red-400">{debugStatus.jobs.failed}</p>
                  </div>
                </div>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-700/40">
                <p className="text-sm font-semibold text-zinc-400 uppercase tracking-[0.18em] mb-4">Memory Counts</p>
                <div className="space-y-2 text-sm text-zinc-200">
                  <div className="flex justify-between rounded-xl bg-slate-950/60 p-3">
                    <span>User ST</span>
                    <span>{debugStatus.memory.per_user.short_term}</span>
                  </div>
                  <div className="flex justify-between rounded-xl bg-slate-950/60 p-3">
                    <span>User LT</span>
                    <span>{debugStatus.memory.per_user.long_term}</span>
                  </div>
                  <div className="flex justify-between rounded-xl bg-slate-950/60 p-3">
                    <span>Global ST</span>
                    <span>{debugStatus.memory.global.short_term}</span>
                  </div>
                  <div className="flex justify-between rounded-xl bg-slate-950/60 p-3">
                    <span>Global LT</span>
                    <span>{debugStatus.memory.global.long_term}</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="glass-panel p-6 rounded-2xl border border-slate-700/40">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-semibold text-zinc-400 uppercase tracking-[0.18em]">Cache Stats</p>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-200 bg-slate-950/70 rounded-xl p-4">{JSON.stringify(debugStatus.cache, null, 2)}</pre>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-700/40">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-semibold text-zinc-400 uppercase tracking-[0.18em]">Performance Metrics</p>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-200 bg-slate-950/70 rounded-xl p-4">{JSON.stringify(debugStatus.perf_metrics, null, 2)}</pre>
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </MainLayout>
  );
}
