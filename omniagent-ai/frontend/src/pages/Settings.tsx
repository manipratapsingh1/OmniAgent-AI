import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { api, getErrorMessage } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useStore } from "../store";
import { apiKeyService } from "../api/apiKeyService";
import { quotaService } from "../api/adminService";
import { useNotificationStore } from "../store/notificationStore";
import {
  FiLock,
  FiLogOut,
  FiZap,
  FiKey,
  FiCopy,
  FiTrash2,
  FiPlus,
  FiLoader,
  FiCheckCircle,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  FiAlertCircle,
  FiBarChart2,
  FiEye,
  FiEyeOff,
  FiSettings,
} from "react-icons/fi";
import { motion } from "framer-motion";
import type { APIKey, QuotaInfo } from "../api/types";

export default function Settings() {
  const { setToken } = useStore();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { user } = useAuth();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [models, setModels] = useState<string[]>([]);
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [keyName, setKeyName] = useState("");
  const [expiryDays, setExpiryDays] = useState<number | undefined>(365);
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [deletingKey, setDeletingKey] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Settings | OmniAgent AI";
    loadAllData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      const [modelsData, apiKeys, quotaData] = await Promise.all([
        api.get("/chat/models"),
        apiKeyService.listKeys(),
        quotaService.getQuota(),
      ]);
      setModels(modelsData.data.models || []);
      setKeys(apiKeys || []);
      setQuota(quotaData);
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({ type: "error", message: `Failed to load data: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  const createKey = async () => {
    if (!keyName.trim()) {
      addNotification({
        type: "error",
        message: "Please enter a key name",
      });
      return;
    }

    try {
      setCreating(true);
      const result = await apiKeyService.createKey(keyName, expiryDays);
      setNewKey(result.key);
      setKeyName("");
      setExpiryDays(365);
      addNotification({
        type: "success",
        message: "API key created! (save this - it won't be shown again)",
      });
      setTimeout(() => loadAllData(), 1000);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      addNotification({
        type: "error",
        message: `Failed to create key: ${err.message}`,
      });
    } finally {
      setCreating(false);
    }
  };

  const revokeKey = async (keyId: number) => {
    if (!window.confirm("Are you sure you want to revoke this key?")) {
      return;
    }

    try {
      setDeletingKey(keyId);
      await apiKeyService.revokeKey(keyId);
      setKeys((prev) => prev.filter((k) => k.id !== keyId));
      addNotification({
        type: "success",
        message: "API key revoked",
      });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      addNotification({
        type: "error",
        message: `Failed to revoke key: ${err.message}`,
      });
    } finally {
      setDeletingKey(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    addNotification({
      type: "success",
      message: "Copied to clipboard",
    });
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      addNotification({ type: "error", message: "Passwords do not match" });
      return;
    }

    if (newPassword.length < 8) {
      addNotification({
        type: "error",
        message: "Password must be at least 8 characters",
      });
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      addNotification({
        type: "success",
        message: "Password changed successfully",
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setShowPasswordForm(false);
    } catch (err) {
      const msg = getErrorMessage(err);
      addNotification({
        type: "error",
        message: `Failed to change password: ${msg}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="relative z-10 p-8 overflow-y-auto scrollbar-thin">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 rounded-lg bg-gradient-to-br from-purple-600/30 to-purple-700/30">
              <FiSettings className="text-purple-400" size={32} />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold gradient-text-secondary">Settings</h1>
              <p className="text-lg text-zinc-400 mt-1">Manage account, API keys, and security</p>
            </div>
          </div>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="flex flex-col items-center gap-3">
              <FiLoader className="animate-spin text-purple-400" size={48} />
              <span className="text-zinc-400">Loading settings...</span>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-4xl">
            {/* Quota Display */}
            {quota && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-panel"
              >
                <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-700/50">
                  <div className="p-3 rounded-lg bg-gradient-to-br from-blue-600/30 to-blue-700/30">
                    <FiBarChart2 className="text-blue-400" size={24} />
                  </div>
                  <h2 className="text-2xl font-bold text-white">API Quota</h2>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="glass-panel-light p-4 flex flex-col">
                      <p className="text-zinc-400 text-sm mb-2">Used</p>
                      <p className="text-3xl font-bold gradient-text">{quota.used}</p>
                    </div>
                    <div className="glass-panel-light p-4 flex flex-col">
                      <p className="text-zinc-400 text-sm mb-2">Remaining</p>
                      <p className="text-3xl font-bold text-green-400">{quota.remaining}</p>
                    </div>
                    <div className="glass-panel-light p-4 flex flex-col">
                      <p className="text-zinc-400 text-sm mb-2">Usage</p>
                      <p className="text-3xl font-bold text-white">{quota.usage_percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* AI Models Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="glass-panel"
            >
              <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-700/50">
                <div className="p-3 rounded-lg bg-gradient-to-br from-blue-600/30 to-blue-700/30">
                  <FiZap className="text-blue-400" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-white">Available Models</h2>
              </div>
              <div className="p-6">
                {models.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {models.map((m) => (
                      <div
                        key={m}
                        className="px-4 py-3 bg-gradient-to-r from-blue-900/20 to-blue-800/10 rounded-lg border border-blue-800/50 text-sm text-blue-200 flex items-center gap-2"
                      >
                        <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                        {m}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-zinc-500 py-8">
                    <p>No models available</p>
                  </div>
                )}
              </div>
            </motion.section>

            {/* Password Change Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-panel"
            >
              <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-700/50">
                <div className="p-3 rounded-lg bg-gradient-to-br from-orange-600/30 to-orange-700/30">
                  <FiLock className="text-orange-400" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-white">Security</h2>
              </div>

              <div className="p-6">
                {!showPasswordForm ? (
                  <button
                    onClick={() => setShowPasswordForm(true)}
                    className="btn-primary"
                  >
                    Change Password
                  </button>
                ) : (
                  <form onSubmit={handlePasswordChange} className="space-y-4">
                    <div>
                      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                      <label className="block text-sm font-semibold text-zinc-300 mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                        className="input-field"
                        placeholder="Enter current password"
                      />
                    </div>

                    <div>
                      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                      <label className="block text-sm font-semibold text-zinc-300 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        minLength={8}
                        className="input-field"
                        placeholder="Enter new password (min 8 chars)"
                      />
                    </div>

                    <div>
                      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                      <label className="block text-sm font-semibold text-zinc-300 mb-2">
                        Confirm Password
                      </label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="input-field"
                        placeholder="Confirm new password"
                      />
                    </div>

                    <div className="flex gap-3 pt-2">
                      <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary"
                      >
                        {loading ? "Updating..." : "Update Password"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowPasswordForm(false);
                          setCurrentPassword("");
                          setNewPassword("");
                          setConfirmPassword("");
                        }}
                        className="btn-secondary"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </motion.section>

            {/* API Keys Management */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
              className="glass-panel"
            >
              <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-700/50">
                <div className="p-3 rounded-lg bg-gradient-to-br from-green-600/30 to-green-700/30">
                  <FiKey className="text-green-400" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-white">API Keys</h2>
              </div>

              <div className="p-6 space-y-6">
                {/* New Key Display */}
                {newKey && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-lg bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-800/50"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <FiCheckCircle className="text-green-400" size={20} />
                      <p className="text-green-200 font-semibold">API Key Created</p>
                    </div>
                    <p className="text-green-300 text-sm mb-4">
                      {/* eslint-disable-next-line react/no-unescaped-entities */}
                      Copy this key now. You won't be able to see it again!
                    </p>
                    <div className="flex items-center gap-2 bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
                      <code className="text-green-300 text-sm font-mono flex-1 truncate">
                        {showKey ? newKey : "••••••••••••••••"}
                      </code>
                      <button
                        onClick={() => setShowKey(!showKey)}
                        title={showKey ? "Hide key" : "Show key"}
                        aria-label={showKey ? "Hide API key" : "Show API key"}
                        className="p-2 hover:bg-slate-700/50 rounded transition text-green-400"
                      >
                        {showKey ? (
                          <FiEyeOff size={18} />
                        ) : (
                          <FiEye size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => copyToClipboard(newKey)}
                        title="Copy API key"
                        aria-label="Copy API key to clipboard"
                        className="p-2 hover:bg-slate-700/50 rounded transition text-green-400"
                      >
                        <FiCopy size={18} />
                      </button>
                    </div>
                  </motion.div>
                )}

                {/* Create New Key Form */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-slate-800/30 to-slate-900/20 border border-slate-700/50">
                  <p className="text-white font-semibold mb-4">Create New API Key</p>
                  <div className="flex flex-col md:flex-row gap-3">
                    <input
                      type="text"
                      value={keyName}
                      onChange={(e) => setKeyName(e.target.value)}
                      placeholder="Key name (e.g., mobile-app)"
                      className="flex-1 input-field"
                    />
                    <select
                      value={expiryDays || ""}
                      onChange={(e) =>
                        setExpiryDays(
                          e.target.value ? parseInt(e.target.value) : undefined
                        )
                      }
                      title="Select API key expiration time"
                      aria-label="API key expiration"
                      className="input-field"
                    >
                      <option value="30">30 days</option>
                      <option value="90">90 days</option>
                      <option value="365">1 year</option>
                      <option value="">No expiry</option>
                    </select>
                    <button
                      onClick={createKey}
                      disabled={creating || !keyName.trim()}
                      className="btn-primary flex items-center justify-center gap-2 md:w-auto"
                    >
                      {creating ? (
                        <FiLoader className="animate-spin" size={18} />
                      ) : (
                        <FiPlus size={18} />
                      )}
                      Create
                    </button>
                  </div>
                </div>

                {/* Existing Keys */}
                {keys.length === 0 ? (
                  <div className="text-center py-12">
                    <FiKey size={40} className="mx-auto mb-3 opacity-30" />
                    <p className="text-zinc-500">No API keys yet. Create one to get started.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {keys.map((key) => (
                      <motion.div
                        key={key.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center justify-between p-4 bg-gradient-to-r from-slate-800/30 to-slate-900/20 rounded-lg border border-slate-700/50 hover:border-slate-600/50 transition"
                      >
                        <div className="flex-1">
                          <p className="text-white font-semibold">{key.name}</p>
                          <p className="text-zinc-400 text-sm flex items-center gap-2 mt-1">
                            {key.key_preview && (
                              <>
                                <code className="text-zinc-500">...{key.key_preview}</code>
                                <span className="text-zinc-600">•</span>
                              </>
                            )}
                            {key.is_active ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-green-900/20 border border-green-800/50 text-green-300 text-xs font-medium">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-400"></div>
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-900/20 border border-red-800/50 text-red-300 text-xs font-medium">
                                <div className="w-1.5 h-1.5 rounded-full bg-red-400"></div>
                                Revoked
                              </span>
                            )}
                          </p>
                        </div>
                        <button
                          onClick={() => revokeKey(key.id)}
                          disabled={deletingKey === key.id}
                          title="Revoke API key"
                          aria-label="Revoke API key"
                          className="p-2.5 rounded-lg hover:bg-red-500/20 transition text-red-400 disabled:opacity-50 border border-transparent hover:border-red-600/50"
                        >
                          {deletingKey === key.id ? (
                            <FiLoader className="animate-spin" size={18} />
                          ) : (
                            <FiTrash2 size={18} />
                          )}
                        </button>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>

            {/* Logout Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-panel"
            >
              <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-700/50">
                <div className="p-3 rounded-lg bg-gradient-to-br from-red-600/30 to-red-700/30">
                  <FiLogOut className="text-red-400" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-white">Account</h2>
              </div>
              <div className="p-6">
                <button
                  onClick={() => {
                    setToken(null);
                    location.href = "/login";
                  }}
                  className="btn-danger"
                >
                  <FiLogOut size={18} className="mr-2" />
                  Logout
                </button>
              </div>
            </motion.section>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
