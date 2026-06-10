import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import { FiUser, FiMail, FiLock, FiCheckCircle, FiZap, FiShield } from "react-icons/fi";
import { motion } from "framer-motion";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";

export default function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const addNotification = useNotificationStore((s) => s.addNotification);

  async function submit(e: React.FormEvent) {
    e.preventDefault();

    if (!fullName.trim()) {
      addNotification({ type: "warning", message: "Please enter your full name" });
      return;
    }
    if (!email.trim()) {
      addNotification({ type: "warning", message: "Please enter your email" });
      return;
    }
    if (password.length < 8) {
      addNotification({ type: "warning", message: "Password must be at least 8 characters" });
      return;
    }

    try {
      setLoading(true);
      await signup(email, password, fullName);
      navigate("/");
    } catch (err) {
      // Error notification is already handled in useAuth hook
    } finally {
      setLoading(false);
    }
  }

  const benefits = [
    { icon: FiZap, title: "Instant Setup", desc: "Start in seconds" },
    { icon: FiShield, title: "Enterprise Grade", desc: "Bank-level security" },
    { icon: FiCheckCircle, title: "AI-Powered", desc: "Smart automation" },
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center relative overflow-hidden">
      {/* Background Layer */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-slate-950 via-purple-950/80 to-slate-950" />

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/75 via-slate-950/50 to-slate-950/75 pointer-events-none" />

      {/* Animated Background Orbs */}
      <motion.div
        animate={{
          top: ["0%", "100%"],
          left: ["0%", "50%"],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute w-96 h-96 bg-purple-500/10 rounded-full filter blur-3xl pointer-events-none"
      />
      <motion.div
        animate={{
          bottom: ["0%", "100%"],
          right: ["0%", "50%"],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        className="absolute w-96 h-96 bg-pink-500/10 rounded-full filter blur-3xl pointer-events-none"
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
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="flex items-center gap-3 mb-6"
              >
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-600 to-pink-600 shadow-glow-md">
                  <FiZap size={24} className="text-white" />
                </div>
                <span className="text-2xl font-bold gradient-text-secondary">OmniAgent</span>
              </motion.div>

              <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 leading-tight">
                Join the
                <br />
                <span className="gradient-text-secondary">Future</span>
              </h1>
              <p className="text-xl text-zinc-400 max-w-sm">
                Unlock the power of intelligent automation. Create your account and start building today.
              </p>
            </div>

            {/* Benefits */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-4"
            >
              {benefits.map((benefit, idx) => {
                const Icon = benefit.icon;
                return (
                  <motion.div key={idx} variants={itemVariants} className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-pink-700/10 border border-purple-600/30 flex-shrink-0">
                      <Icon size={20} className="text-purple-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">{benefit.title}</p>
                      <p className="text-sm text-zinc-400">{benefit.desc}</p>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Testimonial */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="glass-panel p-4"
            >
              <p className="text-sm text-zinc-300 italic mb-2">
                "OmniAgent transformed how we automate our workflows. Highly recommended!"
              </p>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500"></div>
                <div>
                  <p className="text-sm font-semibold text-white">Sarah Chen</p>
                  <p className="text-xs text-zinc-500">CTO at TechCorp</p>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* Right Side - Form */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="glass-panel p-8 backdrop-blur-xl shadow-2xl"
            >
              {/* Form Title */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Create Account</h2>
                <p className="text-zinc-400">Join thousands of AI enthusiasts</p>
              </div>

              {/* Form */}
              <form onSubmit={submit} className="space-y-6">
                {/* Full Name Input */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <Input
                    type="text"
                    label="Full Name"
                    icon={<FiUser />}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Doe"
                    disabled={loading}
                    required
                  />
                </motion.div>

                {/* Email Input */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.45 }}
                >
                  <Input
                    type="email"
                    label="Email Address"
                    icon={<FiMail />}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    disabled={loading}
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
                    helperText="Minimum 8 characters"
                    required
                  />
                </motion.div>

                {/* Sign Up Button */}
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
                  >
                    {loading ? "Creating account..." : "Create Account"}
                  </Button>
                </motion.div>

                {/* Terms Checkbox */}
                <motion.label
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.65 }}
                  className="flex items-start gap-3 text-sm text-zinc-400"
                  htmlFor="terms-checkbox"
                >
                  <input
                    id="terms-checkbox"
                    type="checkbox"
                    title="Agree to Terms of Service and Privacy Policy"
                    required
                    className="w-4 h-4 mt-0.5 rounded border-slate-700 accent-purple-600 cursor-pointer"
                  />
                  <span>
                    I agree to the{" "}
                    <a href="#" className="text-purple-400 hover:text-purple-300">
                      Terms of Service
                    </a>{" "}
                    and{" "}
                    <a href="#" className="text-purple-400 hover:text-purple-300">
                      Privacy Policy
                    </a>
                  </span>
                </motion.label>

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

                {/* Sign In Link */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  className="text-center"
                >
                  <p className="text-zinc-400">
                    Already have an account?{" "}
                    <Link
                      to="/login"
                      className="text-purple-400 hover:text-purple-300 font-semibold transition duration-200"
                    >
                      Sign in
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
                We'll never share your data. Read our privacy policy.
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}