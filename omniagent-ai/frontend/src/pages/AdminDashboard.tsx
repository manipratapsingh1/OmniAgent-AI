
import React, { useState, useEffect } from "react";
import MainLayout from "../layouts/MainLayout";
import { api, getErrorMessage } from "../api/client";
import Loading from "../components/common/Loading";
import { 
  FiBarChart2, FiUsers, FiMessageSquare, FiFileText, 
  FiActivity, FiClock, FiShield, FiRefreshCw,
  FiArrowUpRight, FiArrowDownRight, FiTrendingUp,
  FiCheck, FiX, FiSearch
} from "react-icons/fi";
import { motion } from "framer-motion";
import { adminService } from "../api/adminService";
import { useNotificationStore } from "../store/notificationStore";
import type { User } from "../api/types";

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

  const [activeTab, setActiveTab] = useState<"analytics" | "users">("analytics");
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editQuotaValue, setEditQuotaValue] = useState<string>("");

  const [healthChecks, setHealthChecks] = useState<Record<string, boolean>>({
    database: true,
    redis: true,
    chroma: true,
    ollama: true,
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, metricsRes, healthRes] = await Promise.all([
        api.get<AdminStats>("/admin/dashboard"),
        api.get<SystemMetrics>("/admin/metrics"),
        api.get<{ checks: Record<string, boolean> }>("/health/readyz").catch(err => {
          console.error("Failed to load health status:", err);
          return { data: { checks: { database: false, redis: false, chroma: false, ollama: false } } };
        }),
      ]);
      setStats(statsRes.data);
      setMetrics(metricsRes.data);
      if (healthRes && healthRes.data && healthRes.data.checks) {
        setHealthChecks(healthRes.data.checks);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setUsersLoading(true);
    setUsersError(null);
    try {
      const userList = await adminService.listUsers(0, 100);
      setUsers(userList);
    } catch (err) {
      setUsersError(getErrorMessage(err));
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    document.title = "Admin Dashboard | OmniAgent AI";
    loadData();
    const interval = setInterval(loadData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === "users") {
      loadUsers();
    }
  }, [activeTab]);

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    const addNotification = useNotificationStore.getState().addNotification;
    try {
      const updatedUser = await adminService.toggleUserActive(userId, !currentStatus);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: updatedUser.is_active } : u));
      addNotification({ 
        type: "success", 
        message: `Successfully ${updatedUser.is_active ? "activated" : "suspended"} user` 
      });
    } catch (err) {
      addNotification({ type: "error", message: `Failed to update status: ${getErrorMessage(err)}` });
    }
  };

  const handleChangeRole = async (userId: number, newRole: 'user' | 'moderator' | 'admin') => {
    const addNotification = useNotificationStore.getState().addNotification;
    try {
      const updatedUser = await adminService.changeUserRole(userId, newRole);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: updatedUser.role, is_admin: updatedUser.is_admin } : u));
      addNotification({ type: "success", message: `Successfully updated user role to ${newRole}` });
    } catch (err) {
      addNotification({ type: "error", message: `Failed to change role: ${getErrorMessage(err)}` });
    }
  };

  const handleStartEditQuota = (userId: number, currentQuota: number) => {
    setEditingUserId(userId);
    setEditQuotaValue(currentQuota.toString());
  };

  const handleSaveQuota = async (userId: number) => {
    const addNotification = useNotificationStore.getState().addNotification;
    const quotaNum = parseInt(editQuotaValue, 10);
    if (isNaN(quotaNum) || quotaNum < 0) {
      addNotification({ type: "error", message: "Quota must be a valid positive integer" });
      return;
    }
    try {
      const updatedUser = await adminService.updateUserQuota(userId, quotaNum);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, api_quota: updatedUser.api_quota } : u));
      setEditingUserId(null);
      addNotification({ type: "success", message: "Successfully updated user API quota" });
    } catch (err) {
      addNotification({ type: "error", message: `Failed to update quota: ${getErrorMessage(err)}` });
    }
  };

  const filteredUsers = users.filter((u) => {
    const search = searchTerm.toLowerCase();
    const emailMatch = u.email.toLowerCase().includes(search);
    const nameMatch = u.full_name ? u.full_name.toLowerCase().includes(search) : false;
    return emailMatch || nameMatch;
  });

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
            <h1 className="text-4xl font-black text-white tracking-tight">System Control & Analytics</h1>
            <p className="text-zinc-400 mt-2">Manage the platform, users, and inspect real-time system performance.</p>
          </div>
          <button
            onClick={activeTab === "analytics" ? loadData : loadUsers}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm font-bold text-white hover:bg-slate-800 transition-all shadow-xl"
          >
            <FiRefreshCw className={loading || usersLoading ? "animate-spin" : ""} />
            {activeTab === "analytics" ? "Refresh Data" : "Refresh Users"}
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800/60 pb-px">
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-6 py-3 border-b-2 font-bold text-sm transition-all duration-200 ${
              activeTab === "analytics"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Analytics & System Health
          </button>
          <button
            onClick={() => setActiveTab("users")}
            className={`px-6 py-3 border-b-2 font-bold text-sm transition-all duration-200 ${
              activeTab === "users"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            User Management
          </button>
        </div>

        {/* Analytics Tab */}
        {activeTab === "analytics" && (
          <>
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
              <div className="space-y-8 animate-fadeIn">
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
                    value={stats.documents.total ?? 0} 
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
                                animate={{ width: `${stats.agents.total_runs > 0 ? (item.count / stats.agents.total_runs) * 100 : 0}%` }}
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
                              <div className="text-3xl font-black text-white">{stats.documents.total_chunks ?? 0}</div>
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
                        <HealthRow label="Database" status={healthChecks.database ? "online" : "offline"} />
                        <HealthRow label="Redis Cache" status={healthChecks.redis ? "online" : "offline"} />
                        <HealthRow label="Vector Engine" status={healthChecks.chroma ? "online" : "offline"} />
                        <HealthRow label="Ollama API" status={healthChecks.ollama ? "online" : "offline"} />
                        <HealthRow label="RAG Pipeline" status={(healthChecks.chroma && healthChecks.ollama) ? "online" : "offline"} />
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
          </>
        )}

        {/* User Management Tab */}
        {activeTab === "users" && (
          <div className="space-y-6 animate-fadeIn">
            {/* Search and Action Bar */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="relative group max-w-md w-full">
                <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={16} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search users by name or email..."
                  className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 px-12 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all shadow-inner"
                />
              </div>
            </div>

            {usersError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm font-medium flex items-center gap-3">
                <FiShield size={18} />
                {usersError}
              </div>
            )}

            {usersLoading && users.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loading message="Loading users list..." />
              </div>
            ) : (
              <div className="glass-panel rounded-3xl border border-slate-800/40 bg-slate-900/20 overflow-hidden shadow-2xl">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800/60 bg-slate-950/40 text-slate-400 font-bold text-xs uppercase tracking-wider">
                        <th className="py-4 px-6">User</th>
                        <th className="py-4 px-6">Role</th>
                        <th className="py-4 px-6 text-center">Status</th>
                        <th className="py-4 px-6">API Quota Usage</th>
                        <th className="py-4 px-6 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40 text-sm">
                      {filteredUsers.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-12 text-center text-slate-500 font-medium">
                            No users found matching "{searchTerm}"
                          </td>
                        </tr>
                      ) : (
                        filteredUsers.map((u) => {
                          const isEditing = editingUserId === u.id;
                          const quotaPercent = u.api_quota && u.api_quota > 0 
                            ? Math.min(100, ((u.api_used || 0) / u.api_quota) * 100) 
                            : 0;

                          return (
                            <tr key={u.id} className="hover:bg-slate-950/20 transition-colors">
                              {/* User Info */}
                              <td className="py-4 px-6">
                                <div className="font-bold text-white">{u.full_name || "No Name"}</div>
                                <div className="text-xs text-slate-500 font-medium mt-0.5">{u.email}</div>
                              </td>

                              {/* Role Select */}
                              <td className="py-4 px-6">
                                <select
                                  value={u.role || (u.is_admin ? "admin" : "user")}
                                  onChange={(e) => handleChangeRole(u.id, e.target.value as any)}
                                  className="rounded-xl border border-slate-800 bg-slate-950 text-slate-300 text-xs font-bold px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/40 cursor-pointer"
                                >
                                  <option value="user">User</option>
                                  <option value="moderator">Moderator</option>
                                  <option value="admin">Admin</option>
                                </select>
                              </td>

                              {/* Status Toggle */}
                              <td className="py-4 px-6 text-center">
                                <button
                                  onClick={() => handleToggleActive(u.id, !!u.is_active)}
                                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider transition-all border ${
                                    u.is_active
                                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                                      : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                                  }`}
                                >
                                  <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? "bg-emerald-500" : "bg-rose-500"}`} />
                                  {u.is_active ? "Active" : "Suspended"}
                                </button>
                              </td>

                              {/* API Quota Edit */}
                              <td className="py-4 px-6 min-w-[200px]">
                                {isEditing ? (
                                  <div className="flex items-center gap-2">
                                    <input
                                      type="number"
                                      value={editQuotaValue}
                                      onChange={(e) => setEditQuotaValue(e.target.value)}
                                      className="w-24 rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 text-xs text-white font-bold focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                                      min="0"
                                    />
                                    <button
                                      onClick={() => handleSaveQuota(u.id)}
                                      className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-all border border-emerald-500/30"
                                      title="Save Quota"
                                    >
                                      <FiCheck size={14} />
                                    </button>
                                    <button
                                      onClick={() => setEditingUserId(null)}
                                      className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 transition-all border border-slate-700"
                                      title="Cancel"
                                    >
                                      <FiX size={14} />
                                    </button>
                                  </div>
                                ) : (
                                  <div className="space-y-1.5 max-w-[180px]">
                                    <div className="flex items-center justify-between text-xs">
                                      <span className="text-slate-300 font-bold">{u.api_used || 0} / {u.api_quota || 0}</span>
                                      <button
                                        onClick={() => handleStartEditQuota(u.id, u.api_quota || 0)}
                                        className="text-[10px] text-blue-400 font-bold hover:underline"
                                      >
                                        Edit Limit
                                      </button>
                                    </div>
                                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                      <div 
                                        className={`h-full rounded-full bg-gradient-to-r ${
                                          quotaPercent > 85 
                                            ? "from-rose-500 to-red-500" 
                                            : quotaPercent > 60 
                                            ? "from-amber-500 to-orange-500" 
                                            : "from-blue-500 to-indigo-500"
                                        }`}
                                        style={{ width: `${quotaPercent}%` }}
                                      />
                                    </div>
                                  </div>
                                )}
                              </td>

                              {/* Suspend / Activate Button */}
                              <td className="py-4 px-6 text-right">
                                <button
                                  onClick={() => handleToggleActive(u.id, !!u.is_active)}
                                  className="text-xs font-bold text-slate-400 hover:text-white transition-all bg-slate-900 border border-slate-800/80 px-3 py-1.5 rounded-xl hover:bg-slate-800"
                                >
                                  {u.is_active ? "Suspend" : "Activate"}
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
interface StatCardProps {
  title: string;
  value: string | number;
  subValue: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement> & { size?: number | string }>;
  color: string;
}

function StatCard({ title, value, subValue, icon: Icon, color }: StatCardProps) {
  const iconColors: Record<string, string> = {
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ResourceGauge({ label, value, color }: any) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
