import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import LoadingPage from "./pages/Homepage";
import ChattingPage from "./pages/ChattingPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

function AppContent() {
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (!hasLoaded) {
      const timer = setTimeout(() => {
        setLoading(false);
        setHasLoaded(true);
      }, 5000);
      return () => clearTimeout(timer);
    } else {
      setLoading(false);
    }
  }, [location.pathname, hasLoaded]);
// trigger netlify build

  return (
    <>
      {loading ? (
        <LoadingPage />
      ) : (
        <Routes>
          <Route path="/chat" element={<ChattingPage />} />
          <Route path="/" element={<LoginPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Routes>
      )}
    </>
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