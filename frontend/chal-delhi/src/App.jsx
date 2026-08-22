import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import LoadingPage from "./pages/Homepage";
import ChattingPage from "./pages/ChattingPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import { AUTH_ENABLED } from "./config";

// Splash duration. Was 5000ms, which is a long time to stare at a loader
// before you can type anything.
const SPLASH_MS = 1800;

/**
 * Gate for pages that assume a logged-in user.
 * When no auth service is configured the app runs open — the chat backend
 * has no concept of users anyway.
 */
function RequireAuth({ children }) {
  if (!AUTH_ENABLED) return children;
  const userId = localStorage.getItem("userId");
  return userId ? children : <Navigate to="/" replace />;
}

function AppContent() {
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (!hasLoaded) {
      const timer = setTimeout(() => {
        setLoading(false);
        setHasLoaded(true);
      }, SPLASH_MS);
      return () => clearTimeout(timer);
    } else {
      setLoading(false);
    }
  }, [location.pathname, hasLoaded]);

  if (loading) return <LoadingPage />;

  return (
    <Routes>
      <Route
        path="/chat"
        element={
          <RequireAuth>
            <ChattingPage />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
      />
      {/* Without an auth service there is nothing to log into — go straight
          to the chat so the app is usable. */}
      <Route
        path="/"
        element={AUTH_ENABLED ? <LoginPage /> : <Navigate to="/chat" replace />}
      />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
