import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import MainLayout from "../layouts/MainLayout";
import { FiLogOut, FiSettings, FiMessageSquare, FiFileText, FiUser, FiArrowRight, FiShield } from "react-icons/fi";
import { motion } from "framer-motion";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const menuItems = [
    { label: "Chat", icon: FiMessageSquare, href: "/chat", color: "from-blue-500 to-blue-600", description: "Have conversations with AI" },
    { label: "Documents", icon: FiFileText, href: "/documents", color: "from-purple-500 to-purple-600", description: "Upload and manage files" },
    { label: "Profile", icon: FiUser, href: "/profile", color: "from-cyan-500 to-cyan-600", description: "Manage your profile" },
    { label: "Debug", icon: FiShield, href: "/debug", color: "from-orange-500 to-orange-600", description: "Inspect metrics, cache and jobs" },
    { label: "Settings", icon: FiSettings, href: "/settings", color: "from-green-500 to-green-600", description: "App preferences" },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  };

  return (
    <MainLayout>
      <div className="w-full p-6 lg:p-8 max-w-6xl mx-auto">
        {/* Welcome Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-5xl font-bold text-white mb-3">
            Welcome, <span className="gradient-text-secondary">{user?.full_name || user?.email}</span>
          </h1>
          <p className="text-lg text-zinc-400">Start by choosing what you'd like to do</p>
        </motion.div>

        {/* Main Menu Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12"
        >
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <motion.div key={item.href} variants={itemVariants}>
                <Link
                  to={item.href}
                  className="group relative glass-panel p-6 rounded-xl border border-slate-700/40 hover:border-slate-500/60 transition-all duration-300 overflow-hidden"
                >
                  {/* Background Gradient */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${item.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />

                  {/* Content */}
                  <div className="relative z-10">
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                      <Icon size={24} className="text-white" />
                    </div>

                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-300 transition-colors">
                      {item.label}
                    </h3>

                    <p className="text-sm text-zinc-400 mb-4">{item.description}</p>

                    <div className="flex items-center gap-2 text-blue-400 text-sm font-medium group-hover:gap-3 transition-all">
                      Go <FiArrowRight size={16} />
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Quick Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
        >
          <div className="glass-panel p-6 rounded-xl border border-slate-700/40">
            <p className="text-sm font-semibold text-zinc-400 mb-2">Account Status</p>
            <p className="text-2xl font-bold text-green-400">Active</p>
          </div>
          <div className="glass-panel p-6 rounded-xl border border-slate-700/40">
            <p className="text-sm font-semibold text-zinc-400 mb-2">User Role</p>
            <p className="text-2xl font-bold text-blue-400 capitalize">
              {user?.role || "User"}
            </p>
          </div>
          <div className="glass-panel p-6 rounded-xl border border-slate-700/40">
            <p className="text-sm font-semibold text-zinc-400 mb-2">Member Since</p>
            <p className="text-lg font-bold text-cyan-400">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Today"}
            </p>
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex gap-4"
        >
          <Link
            to="/settings"
            className="inline-flex items-center gap-2 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            <FiSettings size={18} />
            Settings
          </Link>
          <button
            onClick={handleLogout}
            className="inline-flex items-center gap-2 px-6 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors border border-red-500/30"
          >
            <FiLogOut size={18} />
            Logout
          </button>
        </motion.div>
      </div>
    </MainLayout>
  );
}
