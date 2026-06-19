import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import MainLayout from "../layouts/MainLayout";
import { useStore } from "../store";
import { api } from "../api/client";
import { 
  FiLogOut, FiSettings, FiMessageSquare, FiFileText, 
  FiUser, FiArrowRight, FiShield, FiActivity, FiFolder, FiCheckCircle 
} from "react-icons/fi";
import { motion } from "framer-motion";

function CountUp({ end, duration = 1000 }: { end: number; duration?: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const endValue = Number(end);
    if (isNaN(endValue) || endValue <= 0) {
      setCount(0);
      return;
    }

    const incrementTime = Math.max(Math.floor(duration / endValue), 20);
    const timer = setInterval(() => {
      start += 1;
      setCount(start);
      if (start >= endValue) {
        clearInterval(timer);
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [end, duration]);

  return <span>{count}</span>;
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { conversations, setConversations, setMessages, setActive } = useStore();
  const [docCount, setDocCount] = useState<number>(0);
  const [greeting, setGreeting] = useState("Welcome");

  useEffect(() => {
    document.title = "Dashboard | OmniAgent AI";
  }, []);

  useEffect(() => {
    // Time-aware greeting
    const hrs = new Date().getHours();
    if (hrs < 12) setGreeting("Good morning");
    else if (hrs < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");

    // Fetch counts
    const fetchCounts = async () => {
      try {
        const docRes = await api.get("/documents/");
        if (Array.isArray(docRes.data)) {
          setDocCount(docRes.data.length);
        }
        const convRes = await api.get("/conversations/");
        const convData = Array.isArray(convRes.data) ? convRes.data : (convRes.data?.items || []);
        setConversations(convData);
      } catch (err) {
        console.error("Error fetching dashboard statistics", err);
      }
    };
    fetchCounts();
  }, [setConversations]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleNewChat = () => {
    setActive(null);
    setMessages([]);
    navigate("/chat");
  };

  const menuItems = [
    { 
      label: "Chat Terminal", 
      icon: FiMessageSquare, 
      action: handleNewChat, 
      color: "from-blue-600 to-indigo-600 border-blue-500/20 shadow-blue-500/10", 
      description: "Engage with deep reasoning AI and agentic tools." 
    },
    { 
      label: "Knowledge Base", 
      icon: FiFileText, 
      href: "/documents", 
      color: "from-purple-600 to-pink-600 border-purple-500/20 shadow-purple-500/10", 
      description: "Upload real-world assets & index documents for RAG." 
    },
    { 
      label: "Diagnostics Hub", 
      icon: FiShield, 
      href: "/debug", 
      color: "from-orange-500 to-amber-500 border-orange-500/20 shadow-orange-500/10", 
      description: "Inspect active background jobs, cache metrics, and health." 
    },
    { 
      label: "Settings", 
      icon: FiSettings, 
      href: "/settings", 
      color: "from-emerald-500 to-teal-500 border-emerald-500/20 shadow-emerald-500/10", 
      description: "Manage system preferences, API endpoints and security." 
    },
  ];

  const timelineEvents = [
    { time: "Just Now", title: "Secure Session Verified", desc: "JWT active, role mapping: " + (user?.role || "user"), status: "success" },
    { time: "System Boot", title: "Knowledge Retrieval Engine Online", desc: "Connected to vector database and semantic index.", status: "success" },
    { time: "Boot Complete", title: "Multi-Model Router Activated", desc: "Optimised routing for Gemini, OpenAI and Local Ollama engines.", status: "info" },
  ];

  // Particle positions
  const particles = [
    { top: "15%", left: "10%", size: "4px", delay: 0 },
    { top: "45%", left: "85%", size: "6px", delay: 1.5 },
    { top: "75%", left: "20%", size: "5px", delay: 0.8 },
    { top: "25%", left: "70%", size: "3px", delay: 2.2 },
    { top: "85%", left: "60%", size: "4px", delay: 1.1 },
  ];

  return (
    <MainLayout>
      <div className="relative w-full p-6 lg:p-10 max-w-6xl mx-auto overflow-hidden">
        
        {/* Animated Background Mesh & Glowing Orbs */}
        <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
          <motion.div 
            animate={{ 
              x: [0, 40, -20, 0],
              y: [0, -40, 20, 0],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute top-[10%] left-[20%] w-[350px] h-[350px] bg-blue-500/10 rounded-full blur-[100px]"
          />
          <motion.div 
            animate={{ 
              x: [0, -30, 30, 0],
              y: [0, 50, -30, 0],
            }}
            transition={{
              duration: 25,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute bottom-[20%] right-[15%] w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[120px]"
          />
          
          {/* Floating Particles */}
          {particles.map((p, i) => (
            <motion.div
              key={i}
              className="absolute bg-slate-400 rounded-full opacity-35"
              style={{
                top: p.top,
                left: p.left,
                width: p.size,
                height: p.size,
              }}
              animate={{
                y: [0, -30, 0],
                opacity: [0.2, 0.6, 0.2]
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                delay: p.delay,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>

        {/* Content Container */}
        <div className="relative z-10 space-y-10">
          
          {/* Welcome Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800/40 pb-8"
          >
            <div>
              <p className="text-xs font-bold text-blue-500 tracking-[0.25em] uppercase mb-2">OmniAgent Control Center</p>
              <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white mb-3">
                {greeting}, <span className="gradient-text">{user?.full_name || user?.email}</span>
              </h1>
              <p className="text-zinc-400 text-base md:text-lg max-w-xl leading-relaxed">
                Unlock agentic reasoning, hybrid document search, and second-brain analytics.
              </p>
            </div>
            
            <div className="mt-4 md:mt-0 flex items-center gap-2.5 px-4 py-2 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-slate-300 uppercase tracking-widest">v2.0.0 Online</span>
            </div>
          </motion.div>

          {/* Quick Stats Grid with Count-up */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/40 flex items-center gap-5 hover:border-blue-500/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400">
                <FiMessageSquare size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-0.5">Total Threads</p>
                <p className="text-3xl font-black text-white">
                  <CountUp end={conversations.length} duration={800} />
                </p>
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/40 flex items-center gap-5 hover:border-purple-500/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
                <FiFileText size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-0.5">Knowledge Assets</p>
                <p className="text-3xl font-black text-white">
                  <CountUp end={docCount} duration={800} />
                </p>
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/40 flex items-center gap-5 hover:border-emerald-500/30 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400">
                <FiActivity size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-0.5">Engine Status</p>
                <p className="text-3xl font-black text-emerald-400">Active</p>
              </div>
            </div>
          </motion.div>

          {/* Quick Actions & Menu Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Quick Actions Column */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <FiFolder className="text-blue-500" size={16} />
                <h2 className="text-lg font-bold text-white uppercase tracking-widest text-xs">Direct Core Gateways</h2>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {menuItems.map((item, idx) => {
                  const Icon = item.icon;
                  const CardContent = (
                    <div className="relative z-10 flex flex-col justify-between h-full">
                      <div>
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center mb-4 border border-white/10 group-hover:scale-110 transition-transform duration-300`}>
                          <Icon size={20} className="text-white" />
                        </div>
                        <h3 className="text-base font-bold text-white mb-2 group-hover:text-blue-300 transition-colors">
                          {item.label}
                        </h3>
                        <p className="text-xs text-zinc-400 leading-relaxed mb-4">{item.description}</p>
                      </div>
                      <div className="flex items-center gap-2 text-blue-400 text-xs font-bold group-hover:gap-3 transition-all">
                        Access Hub <FiArrowRight size={14} />
                      </div>
                    </div>
                  );

                  return (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.1 * idx }}
                    >
                      {item.action ? (
                        <button
                          onClick={item.action}
                          className="w-full text-left group relative glass-panel p-5 rounded-2xl border border-slate-800/80 bg-slate-950/20 hover:border-slate-700/80 transition-all duration-300 overflow-hidden flex flex-col justify-between min-h-[160px]"
                        >
                          <div className={`absolute inset-0 bg-gradient-to-br ${item.color} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />
                          {CardContent}
                        </button>
                      ) : (
                        <Link
                          to={item.href || "#"}
                          className="group relative glass-panel p-5 rounded-2xl border border-slate-800/80 bg-slate-950/20 hover:border-slate-700/80 transition-all duration-300 overflow-hidden flex flex-col justify-between min-h-[160px]"
                        >
                          <div className={`absolute inset-0 bg-gradient-to-br ${item.color} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />
                          {CardContent}
                        </Link>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Activity Log / System Logs */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <FiActivity className="text-purple-500" size={16} />
                <h2 className="text-lg font-bold text-white uppercase tracking-widest text-xs">Live Kernel Diagnostics</h2>
              </div>
              
              <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-slate-950/20 space-y-4 h-[340px] overflow-y-auto scrollbar-thin">
                {timelineEvents.map((evt, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: idx * 0.1 }}
                    className="flex gap-3 items-start border-l border-slate-800 pl-4 relative"
                  >
                    <div className="absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-950 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase">{evt.time}</span>
                        <FiCheckCircle size={10} className="text-emerald-400" />
                      </div>
                      <h4 className="text-xs font-bold text-slate-200 mt-0.5">{evt.title}</h4>
                      <p className="text-[11px] text-zinc-400 mt-1 leading-normal">{evt.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

          </div>

          {/* Settings / System Action row */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="flex flex-wrap gap-4 border-t border-slate-800/40 pt-6 justify-between items-center"
          >
            <div className="flex gap-4">
              <Link
                to="/profile"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-bold transition-all"
              >
                <FiUser size={14} />
                Profile Settings
              </Link>
              <Link
                to="/settings"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-bold transition-all"
              >
                <FiSettings size={14} />
                Configure Engines
              </Link>
            </div>
            
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 rounded-xl transition-all border border-rose-500/20 text-xs font-bold"
            >
              <FiLogOut size={14} />
              Terminate Session
            </button>
          </motion.div>

        </div>
      </div>
    </MainLayout>
  );
}
