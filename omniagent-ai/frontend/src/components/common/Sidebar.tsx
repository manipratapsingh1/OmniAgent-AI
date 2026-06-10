import { Link } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import { api, getErrorMessage } from "../../api/client";
import { useStore } from "../../store";
import { useAuth } from "../../hooks/useAuth";
import { useNotificationStore } from "../../store/notificationStore";
import ThemeToggle from "./ThemeToggle";
import HealthStatus from "../HealthStatus";
import { 
  FiMessageSquare, FiFileText, FiSettings, FiShield, 
  FiPlus, FiLoader, FiChevronDown, FiChevronRight,
  FiFolder, FiStar, FiSearch, FiMoreHorizontal, FiBarChart2, FiUsers
} from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";

export default function Sidebar() {
  const { conversations, setConversations, activeId, setActive, setMessages } = useStore();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({ "All": true });
  const addNotification = useNotificationStore((s) => s.addNotification);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadConversations(searchQuery);
    }, 300);

    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  const loadConversations = async (query = "") => {
    try {
      if (query) {
        setSearching(true);
      } else {
        setLoading(true);
      }

      const endpoint = query ? "/conversations/search" : "/conversations/";
      const config = query ? { params: { q: query } } : undefined;
      const r = await api.get(endpoint, config);
      const conversations = Array.isArray(r.data) ? r.data : (r.data?.items || []);
      setConversations(conversations);
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to load conversations: ${msg}` });
    } finally {
      setLoading(false);
      setSearching(false);
    }
  };

  async function open(id: number) {
    try {
      setActive(id);
      const r = await api.get(`/conversations/${id}/messages`);
      setMessages(r.data || []);
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to load conversation: ${msg}` });
      setActive(null);
    }
  }

  const toggleFolder = (folderName: string) => {
    setExpandedFolders(prev => ({ ...prev, [folderName]: !prev[folderName] }));
  };

  const pinnedConversations = useMemo(() => conversations.filter(c => c.is_pinned), [conversations]);
  
  const sharedConversations = useMemo(() => conversations.filter(c => c.is_shared), [conversations]);
  
  const folders = useMemo(() => {
    const groups: Record<string, typeof conversations> = {};
    conversations.filter(c => !c.is_pinned && !c.is_shared).forEach(c => {
      const folder = c.folder_name || "Recent";
      if (!groups[folder]) groups[folder] = [];
      groups[folder].push(c);
    });
    return groups;
  }, [conversations]);

  const navItems = [
    { icon: FiMessageSquare, label: "Chat", to: "/chat" },
    { icon: FiFileText, label: "Documents", to: "/documents" },
    { icon: FiShield, label: "Debug", to: "/debug" },
    ...(user?.is_admin ? [{ icon: FiBarChart2, label: "Admin", to: "/admin" }] : []),
    { icon: FiSettings, label: "Settings", to: "/settings" },
  ];

  return (
    <aside className="w-72 flex flex-col h-screen bg-slate-950 border-r border-slate-800/60 shadow-2xl relative z-30">
      {/* Brand Header */}
      <div className="p-6 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-sm">
            <div className="w-4 h-4 rounded-full bg-white/20 animate-pulse" />
          </div>
          <div>
            <h1 className="font-black text-xl tracking-tighter text-white">OMNIAGENT<span className="text-blue-500">X</span></h1>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-none">AI Operating System</p>
          </div>
        </div>
        <ThemeToggle />
      </div>

      {/* Action Area */}
      <div className="p-4 space-y-4">
        <motion.button
          whileHover={{ scale: 1.02, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => {
            setActive(null);
            setMessages([]);
          }}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-bold shadow-glow-sm hover:shadow-glow-md transition-all duration-300"
        >
          <FiPlus size={18} />
          New Thread
        </motion.button>

        <div className="relative group">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={14} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-10 py-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
          />
        </div>
      </div>

      {/* Scrollable Chat History */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-2 space-y-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <FiLoader className="animate-spin text-blue-500" size={24} />
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Indexing History...</span>
          </div>
        ) : (
          <>
            {/* Pinned Section */}
            {pinnedConversations.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-2 py-1">
                  <FiStar className="text-amber-400" size={12} />
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Pinned</span>
                </div>
                {pinnedConversations.map(c => (
                  <ChatLink key={c.id} c={c} active={activeId === c.id} onClick={() => open(c.id)} />
                ))}
              </div>
            )}

            {/* Shared Section */}
            {sharedConversations.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-2 py-1">
                  <FiUsers className="text-cyan-400" size={12} />
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Shared</span>
                </div>
                {sharedConversations.map(c => (
                  <ChatLink key={c.id} c={c} active={activeId === c.id} onClick={() => open(c.id)} />
                ))}
              </div>
            )}

            {/* Folders & Recent */}
            {Object.entries(folders).map(([folderName, items]) => (
              <div key={folderName} className="space-y-1">
                <button 
                  onClick={() => toggleFolder(folderName)}
                  className="w-full flex items-center justify-between px-2 py-1 group"
                >
                  <div className="flex items-center gap-2">
                    {expandedFolders[folderName] ? <FiChevronDown className="text-slate-600" size={12} /> : <FiChevronRight className="text-slate-600" size={12} />}
                    <FiFolder className={expandedFolders[folderName] ? "text-blue-400" : "text-slate-600"} size={12} />
                    <span className={`text-[10px] font-bold uppercase tracking-widest ${expandedFolders[folderName] ? "text-slate-300" : "text-slate-500"}`}>
                      {folderName}
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-slate-700 group-hover:text-slate-500 transition-colors">{items.length}</span>
                </button>
                
                <AnimatePresence>
                  {expandedFolders[folderName] && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden space-y-1 ml-1 pl-3 border-l border-slate-800/60"
                    >
                      {items.map(c => (
                        <ChatLink key={c.id} c={c} active={activeId === c.id} onClick={() => open(c.id)} />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Bottom Nav */}
      <div className="p-4 border-t border-slate-800/60 bg-slate-900/20">
        <nav className="space-y-1 mb-4">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group border ${
                window.location.pathname === item.to 
                  ? "bg-blue-600/10 border-blue-600/20 text-blue-400" 
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50 border-transparent"
              }`}
            >
              <item.icon size={18} />
              <span className="text-sm font-semibold">{item.label}</span>
            </Link>
          ))}
        </nav>
        <HealthStatus />
      </div>
    </aside>
  );
}

function ChatLink({ c, active, onClick }: { c: any, active: boolean, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left text-xs px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
        active
          ? "bg-slate-900 text-white border border-slate-700 shadow-xl"
          : "hover:bg-slate-900/50 text-slate-400 hover:text-slate-200 border border-transparent"
      }`}
    >
      <div className="flex items-center gap-3 overflow-hidden">
        <FiMessageSquare size={14} className={`flex-shrink-0 ${active ? "text-blue-500" : "opacity-40"}`} />
        <span className="flex-1 truncate font-medium">{c.title}</span>
        {active && <div className="w-1 h-4 rounded-full bg-blue-500 absolute left-0 top-1/2 -translate-y-1/2" />}
        <FiMoreHorizontal size={14} className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-600 hover:text-white" />
      </div>
    </button>
  );
}