import React, { useState, useEffect } from "react";
import { FiBarChart2, FiLoader } from "react-icons/fi";
import { motion } from "framer-motion";
import { api } from "../api/client";

interface AnalyticsDashboardProps {}

export default function AnalyticsDashboard(_: AnalyticsDashboardProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [analytics, setAnalytics] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tags, setTags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchAnalytics();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [kbResponse, tagResponse] = await Promise.all([
        api.get(`/features/analytics/knowledge-base`, { params: { days: period } }),
        api.get(`/features/analytics/tag-usage`, { params: { days: period } }),
      ]);

      setAnalytics(kbResponse.data);
      setTags(tagResponse.data.tag_usage?.top_tags || []);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <FiLoader className="animate-spin text-blue-400" size={32} />
      </div>
    );
  }

  if (!analytics) {
    return <div className="p-8 text-zinc-400">Failed to load analytics</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-blue-600/30 to-blue-700/30">
            <FiBarChart2 className="text-blue-400" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Knowledge Base Analytics</h2>
            <p className="text-sm text-zinc-400">Last {period} days</p>
          </div>
        </div>

        <select
          aria-label="Analytics period"
          value={period}
          onChange={(e) => setPeriod(parseInt(e.target.value))}
          className="bg-slate-800/50 border border-slate-700 rounded px-3 py-2 text-sm text-zinc-300"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Documents */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <p className="text-xs text-zinc-400 mb-2 uppercase">Total Documents</p>
          <p className="text-3xl font-bold text-white">{analytics.documents?.total || 0}</p>
          <p className="text-xs text-green-400 mt-2">
            {analytics.documents?.indexed || 0} indexed
          </p>
        </motion.div>

        {/* Chunks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <p className="text-xs text-zinc-400 mb-2 uppercase">Total Chunks</p>
          <p className="text-3xl font-bold text-white">{analytics.documents?.total_chunks || 0}</p>
          <p className="text-xs text-zinc-500 mt-2">Content pieces</p>
        </motion.div>

        {/* Size */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <p className="text-xs text-zinc-400 mb-2 uppercase">Storage Used</p>
          <p className="text-3xl font-bold text-white">
            {analytics.documents?.total_size_gb || 0}
            <span className="text-sm text-zinc-400">GB</span>
          </p>
        </motion.div>

        {/* Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <p className="text-xs text-zinc-400 mb-2 uppercase">Failed</p>
          <p className="text-3xl font-bold text-red-400">{analytics.documents?.failed || 0}</p>
          <p className="text-xs text-zinc-500 mt-2">
            {analytics.documents?.pending || 0} pending
          </p>
        </motion.div>
      </div>

      {/* Top Documents */}
      {analytics.top_documents && analytics.top_documents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <h3 className="text-sm font-semibold text-white mb-4">Top Documents</h3>
          <div className="space-y-2">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {analytics.top_documents.map((doc: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div>
                  <p className="text-zinc-300">{doc.filename}</p>
                  <p className="text-xs text-zinc-500">{doc.chunks} chunks</p>
                </div>
                <span className="text-xs text-zinc-400">{doc.size_mb} MB</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {tags.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg"
        >
          <h3 className="text-sm font-semibold text-white mb-4">Top Tags</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {tags.map((tag: any, idx: number) => (
              <div key={idx} className="p-3 bg-slate-900/60 rounded-lg border border-slate-700">
                <p className="text-sm text-white font-medium">#{tag.tag}</p>
                <p className="text-xs text-zinc-400">Used {tag.count} times</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
