import { useEffect, useState } from "react";
import { api } from "../api/client";
import { FiCheck, FiX, FiRefreshCw } from "react-icons/fi";

interface HealthStatus {
  ready: boolean;
  checks: {
    database: boolean;
    redis: boolean;
    ollama: boolean;
    chroma: boolean;
  };
}

interface DebugStatus {
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
}

type CombinedStatus = HealthStatus & Partial<DebugStatus>;

export default function HealthStatus() {
  const [status, setStatus] = useState<CombinedStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const healthRes = await api.get<HealthStatus>("/health/readyz");
      
      // Only try to get debug status if user is authenticated
      let debugData = {
        jobs: {
          total: 0,
          pending: 0,
          processing: 0,
          completed: 0,
          failed: 0,
          cancelled: 0,
        },
        memory: {
          per_user: { short_term: 0, long_term: 0 },
          global: { short_term: 0, long_term: 0 },
        },
      };
      
      try {
        const debugRes = await api.get<DebugStatus>("/debug/status");
        debugData = debugRes.data;
      } catch (err: any) {
        // Silently ignore 401 (not authenticated) - debug status only available when logged in
        if (err.response?.status !== 401) {
          console.warn("Debug status check failed", err);
        }
      }
      
      setStatus({ ...healthRes.data, ...debugData });
    } catch (err) {
      console.warn("Health check failed", err);
      setStatus({
        ready: false,
        checks: { database: false, redis: false, ollama: false, chroma: false },
        jobs: {
          total: 0,
          pending: 0,
          processing: 0,
          completed: 0,
          failed: 0,
          cancelled: 0,
        },
        memory: {
          per_user: { short_term: 0, long_term: 0 },
          global: { short_term: 0, long_term: 0 },
        },
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="p-3 rounded-lg border border-zinc-700 bg-zinc-900/20 animate-pulse">
      <div className="h-4 bg-zinc-700 rounded w-1/2 mb-2"></div>
      <div className="space-y-1">
        <div className="h-3 bg-zinc-800 rounded w-full"></div>
        <div className="h-3 bg-zinc-800 rounded w-3/4"></div>
      </div>
    </div>
  );

  const getStatusColor = (healthy: boolean) => healthy ? "text-emerald-400" : "text-rose-400";
  const getStatusBg = (healthy: boolean) => healthy ? "bg-emerald-500/5" : "bg-rose-500/5";
  const getStatusBorder = (healthy: boolean) => healthy ? "border-emerald-500/20" : "border-rose-500/20";

  return (
    <div className={`p-4 rounded-xl border text-xs ${getStatusBg(status?.ready ?? false)} ${getStatusBorder(status?.ready ?? false)} transition-all duration-300`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${status?.ready ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"}`}></div>
          <span className="font-bold text-zinc-300 uppercase tracking-wider text-[10px]">System Status</span>
        </div>
        <button
          onClick={checkHealth}
          className="text-zinc-500 hover:text-zinc-200 transition-colors p-1"
          title="Refresh status"
        >
          <FiRefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-4">
        <div className="flex items-center gap-2">
          {status?.checks.database ? <FiCheck className={getStatusColor(true)} size={12} /> : <FiX className={getStatusColor(false)} size={12} />}
          <span className="text-zinc-400">Database</span>
        </div>
        <div className="flex items-center gap-2">
          {status?.checks.redis ? <FiCheck className={getStatusColor(true)} size={12} /> : <FiX className={getStatusColor(false)} size={12} />}
          <span className="text-zinc-400">Cache</span>
        </div>
        <div className="flex items-center gap-2">
          {status?.checks.ollama ? <FiCheck className={getStatusColor(true)} size={12} /> : <FiX className={getStatusColor(false)} size={12} />}
          <span className="text-zinc-400">AI Engine</span>
        </div>
        <div className="flex items-center gap-2">
          {status?.checks.chroma ? <FiCheck className={getStatusColor(true)} size={12} /> : <FiX className={getStatusColor(false)} size={12} />}
          <span className="text-zinc-400">Vector DB</span>
        </div>
      </div>

      <div className="border-t border-zinc-700/50 pt-3 mt-1">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">Metrics</span>
          <span className="text-[9px] text-zinc-600">LIVE</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-300">
          <div className="rounded-lg bg-zinc-950/40 p-2 border border-zinc-800/50">
            <div className="text-zinc-500 mb-1 font-medium">JOBS</div>
            <div className="flex justify-between"><span>Active:</span> <span className="text-blue-400">{(status?.jobs?.pending ?? 0) + (status?.jobs?.processing ?? 0)}</span></div>
            <div className="flex justify-between"><span>Failed:</span> <span className="text-rose-400">{status?.jobs?.failed ?? 0}</span></div>
          </div>
          <div className="rounded-lg bg-zinc-950/40 p-2 border border-zinc-800/50">
            <div className="text-zinc-500 mb-1 font-medium">MEMORY</div>
            <div className="flex justify-between"><span>User:</span> <span className="text-cyan-400">{(status?.memory?.per_user?.short_term ?? 0) + (status?.memory?.per_user?.long_term ?? 0)}</span></div>
            <div className="flex justify-between"><span>Global:</span> <span className="text-purple-400">{(status?.memory?.global?.short_term ?? 0) + (status?.memory?.global?.long_term ?? 0)}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
