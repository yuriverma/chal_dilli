import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import LoadingPage from "./pages/Homepage.jsx";
import ChattingPage from "./pages/ChattingPage";

function AppContent() {
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  return (
    <>
      {loading ? (
        <LoadingPage />
      ) : (
        <Routes>
          <Route path="/" element={<ChattingPage />} />
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

