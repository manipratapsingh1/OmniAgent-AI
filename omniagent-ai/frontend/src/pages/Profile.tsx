import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNotificationStore } from "../store/notificationStore";
import { api, getErrorMessage } from "../api/client";
import MainLayout from "../layouts/MainLayout";
import { motion } from "framer-motion";
import { FiMail, FiUser, FiEdit2, FiSave, FiX } from "react-icons/fi";

interface UserProfile {
  id: number;
  email: string;
  full_name?: string;
  created_at: string;
}

export default function Profile() {
  const { user } = useAuth();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({ full_name: "" });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfile(user as UserProfile);
      setFormData({ full_name: user.full_name || "" });
    }
  }, [user]);

  const handleSaveProfile = async () => {
    try {
      setLoading(true);
      await api.patch("/users/profile", {
        full_name: formData.full_name,
      });
      setProfile({ ...profile!, full_name: formData.full_name });
      setEditing(false);
      addNotification({
        type: "success",
        message: "Profile updated successfully",
      });
    } catch (error) {
      const msg = getErrorMessage(error);
      addNotification({
        type: "error",
        message: `Failed to update profile: ${msg}`,
      });
    } finally {
      setLoading(false);
    }
  };

  if (!profile) return null;

  return (
    <MainLayout>
      <div className="p-8 max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">My Profile</h1>
          <p className="text-zinc-400">Manage your account settings</p>
        </motion.div>

        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-8 mb-6"
        >
          {/* User Info */}
          <div className="space-y-6">
            {/* Email */}
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold text-zinc-400 mb-2">
                <FiMail className="text-blue-400" />
                Email Address
              </label>
              <div className="bg-slate-900/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <p className="text-white">{profile.email}</p>
              </div>
            </div>

            {/* Full Name */}
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold text-zinc-400 mb-2">
                <FiUser className="text-blue-400" />
                Full Name
              </label>
              {editing ? (
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  placeholder="Enter your full name"
                  className="w-full bg-slate-900/50 rounded-lg px-4 py-3 border border-blue-500/50 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
                />
              ) : (
                <div className="bg-slate-900/50 rounded-lg px-4 py-3 border border-slate-700/50">
                  <p className="text-white">
                    {profile.full_name || "Not provided"}
                  </p>
                </div>
              )}
            </div>

            {/* Member Since */}
            <div>
              <label className="text-sm font-semibold text-zinc-400 mb-2 block">
                Member Since
              </label>
              <div className="bg-slate-900/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <p className="text-white">
                  {new Date(profile.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 mt-8">
            {editing ? (
              <>
                <button
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 transition-all"
                >
                  <FiSave /> {loading ? "Saving..." : "Save Changes"}
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    setFormData({ full_name: profile.full_name || "" });
                  }}
                  className="flex items-center gap-2 px-6 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all"
                >
                  <FiX /> Cancel
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-2 px-6 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all"
              >
                <FiEdit2 /> Edit Profile
              </button>
            )}
          </div>
        </motion.div>

        {/* Account Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-panel p-8"
        >
          <h2 className="text-xl font-bold text-white mb-4">Account Information</h2>
          <div className="space-y-3 text-sm text-zinc-400">
            <p>
              <strong>Account ID:</strong> {profile.id}
            </p>
            <p>
              <strong>Created:</strong>{" "}
              {new Date(profile.created_at).toLocaleString()}
            </p>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
}
