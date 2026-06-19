import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import { FiMail, FiLock, FiCheckCircle, FiZap, FiShield } from "react-icons/fi";
import { motion } from "framer-motion";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";

export default function Login() {
  useEffect(() => {
    document.title = "Login | OmniAgent AI";
  }, []);

  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const addNotification = useNotificationStore((s) => s.addNotification);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      addNotification({ type: "warning", message: "Please enter your email" });
      return;
    }
    if (!password.trim()) {
      addNotification({ type: "warning", message: "Please enter your password" });
      return;
    }

    try {
      setLoading(true);
      await login(email, password);
      navigate("/");
    } catch (err) {
      // Error notification is already handled in useAuth hook
    } finally {
      setLoading(false);
    }
  }

  const features = [
    { icon: FiZap, title: "AI-Powered", desc: "Advanced AI agents" },
    { icon: FiShield, title: "Secure", desc: "Enterprise security" },
    { icon: FiCheckCircle, title: "Reliable", desc: "99.9% uptime" },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950/30 to-slate-950 flex items-center justify-center relative overflow-hidden">
      {/* Background Layer */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-slate-950 via-blue-950/80 to-slate-950" />

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/70 via-slate-950/40 to-slate-950/70 pointer-events-none" />

      {/* Animated Background Orbs */}
      <motion.div
        animate={{
          top: ["0%", "50%"],
          left: ["0%", "30%"],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        className="absolute w-96 h-96 bg-blue-500/15 rounded-full filter blur-3xl pointer-events-none"
      />
      <motion.div
        animate={{
          bottom: ["0%", "40%"],
          right: ["0%", "20%"],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        className="absolute w-96 h-96 bg-purple-500/15 rounded-full filter blur-3xl pointer-events-none"
      />
      <motion.div
        animate={{
          top: ["50%", "10%"],
          left: ["50%", "70%"],
        }}
        transition={{ duration: 28, repeat: Infinity, ease: "easeInOut" }}
        className="absolute w-64 h-64 bg-cyan-500/10 rounded-full filter blur-3xl pointer-events-none"
      />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left Side - Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            {/* Logo & Heading */}
            <div>
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 100 }}
                className="flex items-center gap-3 mb-6"
              >
                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-600 shadow-glow-md hover:shadow-glow-lg transition-shadow">
                  <FiZap size={28} className="text-white" />
                </div>
                <span className="text-3xl font-bold gradient-text">OmniAgent</span>
              </motion.div>

              <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 leading-tight">
                Welcome
                <br />
                <span className="gradient-text from-blue-400 to-cyan-400">Back</span>
              </h1>
              <p className="text-lg text-zinc-400 max-w-sm">
                Experience the power of intelligent AI agents. Log in to access your personalized dashboard.
              </p>
            </div>

            {/* Features */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-4"
            >
              {features.map((feature, idx) => {
                const Icon = feature.icon;
                return (
                  <motion.div key={idx} variants={itemVariants} className="flex items-start gap-4 group cursor-pointer">
                    <div className="p-3 rounded-lg bg-gradient-to-br from-blue-600/20 to-blue-700/10 border border-blue-600/30 flex-shrink-0 group-hover:border-blue-500/60 group-hover:shadow-glow-sm transition-all duration-300">
                      <Icon size={20} className="text-blue-400 group-hover:text-blue-300 transition-colors" />
                    </div>
                    <div>
                      <p className="font-semibold text-white group-hover:text-blue-200 transition-colors">{feature.title}</p>
                      <p className="text-sm text-zinc-400">{feature.desc}</p>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Trust Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex items-center gap-3 pt-4 p-4 bg-slate-900/50 rounded-lg border border-blue-500/20"
            >
              <div className="flex -space-x-2">
                {[1, 2, 3].map((i) => (
                  <motion.div
                    key={i}
                    whileHover={{ scale: 1.1 }}
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 border-2 border-slate-900 flex items-center justify-center text-xs text-white font-semibold cursor-pointer"
                  >
                    {i}K
                  </motion.div>
                ))}
              </div>
              <span className="text-sm text-zinc-300">10K+ users trust OmniAgent</span>
            </motion.div>
          </motion.div>

          {/* Right Side - Form */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.3, type: "spring", stiffness: 100 }}
              className="glass-panel p-8 backdrop-blur-xl shadow-2xl border border-blue-500/20 bg-gradient-to-br from-slate-900/60 to-blue-950/30"
            >
              {/* Form Title */}
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-white mb-2">Sign In</h2>
                <p className="text-zinc-400">Enter your credentials to continue</p>
              </div>

              {/* Form */}
              <form onSubmit={submit} className="space-y-6">
                {/* Email Input */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <Input
                    type="email"
                    label="Email Address"
                    icon={<FiMail />}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    disabled={loading}
                    helperText="We'll never share your email"
                    required
                  />
                </motion.div>

                {/* Password Input */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                >
                  <Input
                    type="password"
                    label="Password"
                    icon={<FiLock />}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={loading}
                    required
                  />
                </motion.div>

                {/* Sign In Button */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    fullWidth
                    isLoading={loading}
                    disabled={loading}
                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                    onClick={(e) => {
                      // Form submission is handled by the form tag
                    }}
                  >
                    {loading ? "Signing in..." : "Sign In"}
                  </Button>
                </motion.div>

                {/* Divider */}
                <div className="relative py-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-700/50"></div>
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="px-2 bg-gradient-to-b from-slate-800/50 to-slate-900/50 text-zinc-500">
                      OR
                    </span>
                  </div>
                </div>

                {/* Sign Up Link */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  className="text-center"
                >
                  <p className="text-zinc-400">
                    {/* eslint-disable-next-line react/no-unescaped-entities */}
                    Don't have an account?{" "}
                    <Link
                      to="/signup"
                      className="text-blue-400 hover:text-blue-300 font-semibold transition duration-200"
                    >
                      Create one
                    </Link>
                  </p>
                </motion.div>
              </form>

              {/* Footer */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="mt-8 pt-6 border-t border-slate-700/50 text-center text-xs text-zinc-500"
              >
                By signing in, you agree to our Terms of Service and Privacy Policy
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}