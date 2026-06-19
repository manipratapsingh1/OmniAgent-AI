import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense } from "react";
import { useAuth } from "./hooks/useAuth";
import { useNotificationStore } from "./store/notificationStore";
import Loading from "./components/common/Loading";
import ErrorBoundary from "./components/common/ErrorBoundary";
import NotificationCenter from "./components/common/NotificationCenter";
import KeyboardShortcuts from "./components/KeyboardShortcuts";

// Auth Pages
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import SharedConversation from "./pages/SharedConversation";

// Protected Pages
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import Settings from "./pages/Settings";
import Profile from "./pages/Profile";
import DebugDashboard from "./pages/DebugDashboard";
import AdminDashboard from "./pages/AdminDashboard";

// Route protection wrapper
function Protected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading message="Authenticating..." fullScreen />;
  if (!user) return <Navigate to="/login" />;
  return children;
}

// Admin Route protection wrapper
function AdminProtected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading message="Authenticating..." fullScreen />;
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const notifications = useNotificationStore((s) => s.notifications);
  const removeNotification = useNotificationStore((s) => s.removeNotification);

  return (
    <ErrorBoundary>
      <Suspense fallback={<Loading message="Loading..." fullScreen />}>
        <KeyboardShortcuts />

        <Routes>
          {/* Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/share/:shareToken" element={<SharedConversation />} />

          {/* Protected Routes */}
          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/chat" element={<Protected><Chat /></Protected>} />
          <Route path="/documents" element={<Protected><Documents /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
          <Route path="/debug" element={<AdminProtected><DebugDashboard /></AdminProtected>} />
          <Route path="/admin" element={<AdminProtected><AdminDashboard /></AdminProtected>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Notifications */}
        <NotificationCenter
          notifications={notifications}
          onDismiss={removeNotification}
        />
      </Suspense>
    </ErrorBoundary>
  );
}