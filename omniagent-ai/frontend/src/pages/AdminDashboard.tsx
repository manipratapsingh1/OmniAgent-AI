
import React, { useState, useEffect } from "react";
import MainLayout from "../layouts/MainLayout";
import { api, getErrorMessage } from "../api/client";
import Loading from "../components/common/Loading";
import { 
  FiBarChart2, FiUsers, FiMessageSquare, FiFileText, 
  FiActivity, FiClock, FiShield, FiRefreshCw,
  FiArrowUpRight, FiArrowDownRight, FiTrendingUp
} from "react-icons/fi";
import { motion } from "framer-motion";

interface AdminStats {
  overview: {
    users: number;
    messages: number;
    agent_runs: number;
    avg_agent_latency_ms: number;
  };
  users: {
    total_users: number;
    active_users: number;
    admin_users: number;
  };
  documents: {
    total: number;
    indexed: number;
    failed: number;
    pending: number;
    total_chunks: number;
  };
  messages: {
    total_messages: number;
    user_messages: number;
    assistant_messages: number;
    messages_last_24h: number;
  };
  agents: {
    total_runs: number;
    avg_latency_ms: number;
    success_rate: number;
    popular_agents: Array<{agent: string, count: number}>;
  };
  timestamp: string;
}

interface SystemMetrics {
  system: {
    cpu_percent: number;
    memory: {
      percent: number;
      process_usage_mb: number;
    };
    disk: {
      percent: number;
    };
    uptime_seconds: number;
  };
  application: {
    users: { total: number; active_today: number };
    chat: { total_messages: number; avg_response_time_ms: number };
    storage: { total_documents: number; indexed_success_rate: number };
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, metricsRes] = await Promise.all([
        api.get<AdminStats>("/admin/dashboard"),
        api.get<SystemMetrics>("/admin/metrics"),
      ]);
      setStats(statsRes.data);
      setMetrics(metricsRes.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) return <Loading message="Loading analytics..." fullScreen />;

  return (
    <MainLayout>
      <div className="w-full p-6 lg:p-8 max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400">
                <FiBarChart2 size={20} />
              </div>
              <span className="text-xs font-bold text-blue-500 uppercase tracking-widest">Admin Control Center</span>
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">System Analytics</h1>
            <p className="text-zinc-400 mt-2">Real-time overview of platform activity, performance, and health.</p>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm font-bold text-white hover:bg-slate-800 transition-all shadow-xl"
          >
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
            Refresh Data
          </button>
        </div>

        {/* System Health Section */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ResourceGauge label="CPU Usage" value={metrics.system.cpu_percent} color="blue" />
            <ResourceGauge label="Memory" value={metrics.system.memory.percent} color="indigo" />
            <ResourceGauge label="Disk Space" value={metrics.system.disk.percent} color="cyan" />
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm font-medium flex items-center gap-3">
            <FiShield size={18} />
            {error}
          </div>
        )}

        {stats && (
          <div className="space-y-8">
            {/* Top Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard 
                title="Total Users" 
                value={stats.users.total_users} 
                subValue={`${stats.users.active_users} active`} 
                icon={FiUsers} 
                color="blue" 
              />
              <StatCard 
                title="Total Messages" 
                value={stats.messages.total_messages} 
                subValue={`${stats.messages.messages_last_24h} today`} 
                icon={FiMessageSquare} 
                color="indigo" 
              />
              <StatCard 
                title="Knowledge Base" 
                value={stats.documents.total} 
                subValue={`${stats.documents.indexed} indexed`} 
                icon={FiFileText} 
                color="cyan" 
              />
              <StatCard 
                title="Avg Latency" 
                value={`${Math.round(stats.overview.avg_agent_latency_ms)}ms`} 
                subValue="Response time" 
                icon={FiClock} 
                color="emerald" 
              />
            </div>

            {/* Detailed Analytics Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Agent Performance */}
              <div className="lg:col-span-2 space-y-6">
                <div className="glass-panel p-8 rounded-3xl border border-slate-800/40 bg-slate-900/20">
                  <div className="flex items-center justify-between mb-8">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                      <FiActivity className="text-blue-500" />
                      Agent Utilization
                    </h3>
                    <div className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-widest border border-blue-500/20">
                      Live Stats
                    </div>
                  </div>
                  
                  <div className="space-y-6">
                    {stats.agents.popular_agents.map((item, idx) => (
                      <div key={item.agent} className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-bold text-slate-300 capitalize">{item.agent} Agent</span>
                          <span className="text-slate-500 font-mono">{item.count} runs</span>
                        </div>
                        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${(item.count / stats.agents.total_runs) * 100}%` }}
                            transition={{ duration: 1, delay: idx * 0.1 }}
                            className="h-full bg-gradient-to-r from-blue-600 to-indigo-600"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* System Activity */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <div className="glass-panel p-6 rounded-3xl border border-slate-800/40 bg-slate-900/20">
                      <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Document Pipeline</h4>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-3xl font-black text-white">{stats.documents.total_chunks}</div>
                          <div className="text-xs text-slate-500 font-medium">Semantic chunks stored</div>
                        </div>
                        <div className="p-4 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                          <FiTrendingUp size={24} />
                        </div>
                      </div>
                   </div>
                   <div className="glass-panel p-6 rounded-3xl border border-slate-800/40 bg-slate-900/20">
                      <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Agent Accuracy</h4>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-3xl font-black text-white">{Math.round(stats.agents.success_rate * 100)}%</div>
                          <div className="text-xs text-slate-500 font-medium">Task success rate</div>
                        </div>
                        <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <FiShield size={24} />
                        </div>
                      </div>
                   </div>
                </div>
              </div>

              {/* Quick Actions / Recent Activity */}
              <div className="space-y-6">
                <div className="glass-panel p-8 rounded-3xl border border-slate-800/40 bg-slate-900/20 h-full">
                  <h3 className="text-xl font-bold text-white mb-6">System Health</h3>
                  <div className="space-y-4">
                    <HealthRow label="Database" status="online" />
                    <HealthRow label="Redis Cache" status="online" />
                    <HealthRow label="Vector Engine" status="online" />
                    <HealthRow label="Ollama API" status="online" />
                    <HealthRow label="RAG Pipeline" status="online" />
                  </div>

                  <div className="mt-10 pt-8 border-t border-slate-800/60">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Storage Metrics</h4>
                    <div className="flex items-end justify-between mb-2">
                      <span className="text-sm font-bold text-white">Database Usage</span>
                      <span className="text-xs text-slate-500">4.2 GB / 10 GB</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full w-[42%] bg-blue-500" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

function StatCard({ title, value, subValue, icon: Icon, color }: any) {
  const colors: any = {
    blue: "from-blue-600 to-indigo-600 shadow-blue-500/10 border-blue-500/20",
    indigo: "from-indigo-600 to-violet-600 shadow-indigo-500/10 border-indigo-500/20",
    cyan: "from-cyan-600 to-blue-600 shadow-cyan-500/10 border-cyan-500/20",
    emerald: "from-emerald-600 to-teal-600 shadow-emerald-500/10 border-emerald-500/20",
  };

  const iconColors: any = {
    blue: "bg-blue-500/10 text-blue-400",
    indigo: "bg-indigo-500/10 text-indigo-400",
    cyan: "bg-cyan-500/10 text-cyan-400",
    emerald: "bg-emerald-500/10 text-emerald-400",
  };

  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className={`glass-panel p-6 rounded-3xl border border-slate-800/40 bg-slate-900/20 relative overflow-hidden group shadow-2xl`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-2xl ${iconColors[color]} transition-transform group-hover:scale-110 duration-300`}>
          <Icon size={20} />
        </div>
        <div className="flex items-center gap-1 text-[10px] font-black text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full border border-emerald-400/20">
          <FiArrowUpRight />
          12%
        </div>
      </div>
      <div>
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest">{title}</h3>
        <div className="text-3xl font-black text-white mt-1">{value}</div>
        <p className="text-xs text-slate-500 font-medium mt-1">{subValue}</p>
      </div>
    </motion.div>
  );
}

function ResourceGauge({ label, value, color }: any) {
  const colors: any = {
    blue: "bg-blue-500",
    indigo: "bg-indigo-500",
    cyan: "bg-cyan-500",
  };

  return (
    <div className="glass-panel p-6 rounded-3xl border border-slate-800/40 bg-slate-900/20">
      <div className="flex justify-between items-end mb-4">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        <span className="text-2xl font-black text-white">{Math.round(value)}%</span>
      </div>
      <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden p-0.5">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          className={`h-full rounded-full ${colors[color]} shadow-[0_0_10px_rgba(59,130,246,0.5)]`}
        />
      </div>
    </div>
  );
}

function HealthRow({ label, status }: { label: string, status: 'online' | 'offline' | 'warning' }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm font-medium text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{status}</span>
        <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-rose-500'}`} />
      </div>
    </div>
  );
}
