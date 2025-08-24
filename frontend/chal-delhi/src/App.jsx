import React, { useEffect, useState } from "react";
import LoadingPage from "./pages/HomePage";
import LandingPage from "./pages/LandingPage";
import ChattingPage from "./pages/ChattingPage";

function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      {loading ? <LoadingPage /> : <ChattingPage />}
    </>
  );
}

export default App;

