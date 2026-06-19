import { useEffect, useState } from "react";
import { api } from "../api/client";
import { FiCheck, FiX, FiRefreshCw, FiChevronDown, FiChevronUp } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";

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
  const [expanded, setExpanded] = useState(false);

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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
    <div className="p-2.5 rounded-xl border border-slate-800/60 bg-slate-900/10 animate-pulse flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-700"></div>
        <div className="h-3 bg-slate-800 rounded w-20"></div>
      </div>
      <div className="w-3 h-3 bg-slate-800 rounded-full"></div>
    </div>
  );

  const isReady = status?.ready ?? false;
 
   return (
     <div className={`p-2.5 rounded-xl border text-xs bg-slate-900/10 ${isReady ? "border-emerald-500/10 hover:border-emerald-500/20" : "border-rose-500/10 hover:border-rose-500/20"} transition-all duration-300`}>
       <div 
         className="flex items-center justify-between cursor-pointer select-none outline-none focus:ring-1 focus:ring-slate-800 rounded"
         onClick={() => setExpanded(!expanded)}
         role="button"
         tabIndex={0}
         onKeyDown={(e) => {
           if (e.key === "Enter" || e.key === " ") {
             e.preventDefault();
             setExpanded(!expanded);
           }
         }}
       >
         <div className="flex items-center gap-2">
           <div className={`w-1.5 h-1.5 rounded-full ${isReady ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"}`}></div>
           <span className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">System Status</span>
         </div>
        <div className="flex items-center gap-1.5 text-slate-500 group">
          <button
            onClick={(e) => {
              e.stopPropagation();
              checkHealth();
            }}
            className="hover:text-slate-200 transition-colors p-0.5"
            title="Refresh status"
          >
            <FiRefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
          {expanded ? <FiChevronUp size={14} className="group-hover:text-slate-300" /> : <FiChevronDown size={14} className="group-hover:text-slate-300" />}
        </div>
      </div>
      
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0, marginTop: 0 }}
            animate={{ height: "auto", opacity: 1, marginTop: 10 }}
            exit={{ height: 0, opacity: 0, marginTop: 0 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-3 pt-2 border-t border-slate-800/40 text-[11px]">
              <div className="flex items-center gap-2">
                {status?.checks.database ? <FiCheck className="text-emerald-400" size={11} /> : <FiX className="text-rose-400" size={11} />}
                <span className="text-slate-400">Database</span>
              </div>
              <div className="flex items-center gap-2">
                {status?.checks.redis ? <FiCheck className="text-emerald-400" size={11} /> : <FiX className="text-rose-400" size={11} />}
                <span className="text-slate-400">Cache</span>
              </div>
              <div className="flex items-center gap-2">
                {status?.checks.ollama ? <FiCheck className="text-emerald-400" size={11} /> : <FiX className="text-rose-400" size={11} />}
                <span className="text-slate-400">AI Engine</span>
              </div>
              <div className="flex items-center gap-2">
                {status?.checks.chroma ? <FiCheck className="text-emerald-400" size={11} /> : <FiX className="text-rose-400" size={11} />}
                <span className="text-slate-400">Vector DB</span>
              </div>
            </div>

            <div className="border-t border-slate-800/40 pt-2.5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Metrics</span>
                <span className="text-[8px] text-slate-600">LIVE</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[9px] text-slate-300">
                <div className="rounded-lg bg-slate-950/40 p-1.5 border border-slate-800/50">
                  <div className="text-slate-500 mb-0.5 font-semibold">JOBS</div>
                  <div className="flex justify-between"><span>Active:</span> <span className="text-blue-400 font-bold">{(status?.jobs?.pending ?? 0) + (status?.jobs?.processing ?? 0)}</span></div>
                  <div className="flex justify-between"><span>Failed:</span> <span className="text-rose-400 font-bold">{status?.jobs?.failed ?? 0}</span></div>
                </div>
                <div className="rounded-lg bg-slate-950/40 p-1.5 border border-slate-800/50">
                  <div className="text-slate-500 mb-0.5 font-semibold">MEMORY</div>
                  <div className="flex justify-between"><span>User:</span> <span className="text-cyan-400 font-bold">{(status?.memory?.per_user?.short_term ?? 0) + (status?.memory?.per_user?.long_term ?? 0)}</span></div>
                  <div className="flex justify-between"><span>Global:</span> <span className="text-purple-400 font-bold">{(status?.memory?.global?.short_term ?? 0) + (status?.memory?.global?.long_term ?? 0)}</span></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
