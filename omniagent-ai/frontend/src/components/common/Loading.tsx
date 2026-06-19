import { motion } from "framer-motion";

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export default function Loading({ message = "Loading...", fullScreen = false }: LoadingProps) {
  const orbs = [
    { color: "from-blue-500 to-cyan-500", delay: 0, size: "w-4 h-4" },
    { color: "from-violet-500 to-purple-500", delay: 0.2, size: "w-5 h-5" },
    { color: "from-cyan-500 to-blue-500", delay: 0.4, size: "w-4 h-4" },
  ];

  const content = (
    <div className="flex flex-col items-center justify-center gap-8">
      {/* Animated Orbs */}
      <div className="relative flex items-center gap-3">
        {orbs.map((orb, i) => (
          <motion.div
            key={i}
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.6,
              repeat: Infinity,
              delay: orb.delay,
              ease: "easeInOut",
            }}
            className={`${orb.size} rounded-full bg-gradient-to-br ${orb.color} shadow-lg`}
            style={{
              boxShadow: `0 0 20px rgba(59,130,246,0.3)`,
            }}
          />
        ))}
      </div>

      {/* Brand + Message */}
      <div className="text-center space-y-2">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-sm font-semibold gradient-text tracking-wider"
        >
          OMNIAGENT
        </motion.p>
        <motion.p
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-xs text-slate-500"
        >
          {message}
        </motion.p>
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="w-full h-screen bg-slate-950 flex items-center justify-center mesh-bg">
        {content}
      </div>
    );
  }

  return <div className="flex items-center justify-center p-8">{content}</div>;
}
