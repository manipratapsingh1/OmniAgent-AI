import React from "react";
import { motion } from "framer-motion";

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export default function Loading({ message = "Loading...", fullScreen = false }: LoadingProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full"
      />
      <p className="text-zinc-400 text-sm">{message}</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="w-full h-screen bg-slate-950 flex items-center justify-center">
        {content}
      </div>
    );
  }

  return <div className="flex items-center justify-center p-8">{content}</div>;
}
