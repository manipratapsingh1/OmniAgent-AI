import React from "react";
import Sidebar from "../components/common/Sidebar";

interface MainLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  className?: string;
}

/**
 * MainLayout Component
 * Provides consistent layout with sidebar for protected routes
 */
export default function MainLayout({
  children,
  showSidebar = true,
  className = "",
}: MainLayoutProps) {
  return (
    <div className={`flex h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative ${className}`}>
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950/95 via-slate-950/90 to-slate-950/95 pointer-events-none -z-10" />

      {/* Sidebar */}
      {showSidebar && <Sidebar />}

      {/* Main Content */}
      <main className="relative z-10 flex-1 overflow-y-auto scrollbar-thin">{children}</main>
    </div>
  );
}
