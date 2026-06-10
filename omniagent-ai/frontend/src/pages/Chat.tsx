import MainLayout from "../layouts/MainLayout";
import ChatWindow from "../components/chat/ChatWindow";
import AgentTracePanel from "../components/chat/AgentTracePanel";
import SourcesPanel from "../components/chat/SourcesPanel";
import MemoryPanel from "../components/chat/MemoryPanel";
import { motion } from "framer-motion";

export default function Chat() {
  return (
    <MainLayout>
      <main className="p-6 lg:p-8 h-full">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex-1 glass-panel flex flex-col h-full overflow-hidden border border-slate-700/40"
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-700/40 bg-slate-950/90">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">AI Assistant</p>
                <h2 className="text-2xl font-semibold text-white mt-1">Chat</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
                <span className="badge badge-info">Online</span>
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-hidden flex gap-6">
            {/* Main Chat */}
            <div className="flex-1 flex flex-col min-w-0">
              <ChatWindow />
            </div>

            {/* Right Sidebar */}
            <aside className="w-80 border-l border-slate-700/50 bg-gradient-to-b from-slate-900/90 to-slate-950/90 backdrop-blur hidden lg:flex flex-col overflow-y-auto scrollbar-thin">
              <div className="flex-1 overflow-y-auto">
                <AgentTracePanel />
                <SourcesPanel />
              </div>
              <MemoryPanel />
            </aside>
          </div>
        </motion.div>
      </main>
    </MainLayout>
  );
}
