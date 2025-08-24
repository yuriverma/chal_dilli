import React, { useState } from 'react';
import "../App.css";
import bg from "../assets/bg.png";

const ChattingPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    // show user msg immediately
    const userMessage = { user: input, bot: null };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });
      const data = await res.json();

      // add bot reply
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { user: input, bot: data.response },
      ]);
    } catch (err) {
      console.error("Error:", err);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { user: input, bot: "⚠️ Backend not reachable" },
      ]);
    }

    setInput("");
  };

  return (
    <div
      className="relative min-h-screen w-full overflow-hidden"
      style={{
        backgroundImage: `url(${bg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Title */}
      <div className="absolute top-8 left-1/2 transform -translate-x-1/2 z-30">
        <h1 className="text-5xl font-bold text-amber-900 text-center mb-2">
          Chal Dilli
        </h1>
        <p className="text-amber-800 text-center text-lg">
          The only map Dilliwalas trust
        </p>
      </div>

      {/* Left Sidebar (Recent Qs dummy for now) */}
      <div className="absolute left-8 top-32 bottom-8 w-80 z-20">
        <div className="relative w-full h-full rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, rgba(139, 69, 19, 0.8), rgba(101, 67, 33, 0.7))',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div className="p-6 border-b border-amber-700/30">
            <h2 className="text-xl font-bold text-amber-100 mb-2">Recent Questions</h2>
            <p className="text-amber-200/80 text-sm">Your Delhi exploration history</p>
          </div>
          <div className="p-4 h-full overflow-y-auto custom-scrollbar text-amber-200/80 text-sm">
            {messages.slice(-6).map((m, i) => (
              <div key={i} className="mb-2">{m.user}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Panel */}
      <div className="absolute right-8 top-32 bottom-8 left-96 ml-8 z-20">
        <div className="relative w-full h-full rounded-2xl border border-amber-700/30 shadow-xl flex flex-col"
          style={{
            background: 'linear-gradient(135deg, rgba(139, 69, 19, 0.8), rgba(101, 67, 33, 0.7))',
            backdropFilter: 'blur(10px)',
          }}
        >
          {/* Header */}
          <div className="p-6 border-b border-amber-700/30">
            <h2 className="text-xl font-bold text-amber-100">Chat with CHAL DILLI</h2>
            <p className="text-amber-200/80 text-sm mt-1">Ask me anything about Delhi!</p>
          </div>

          {/* Chat messages */}
          <div className="flex-1 p-6 space-y-4 overflow-y-auto">
            {messages.map((m, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-end">
                  <div className="max-w-[70%] bg-amber-800/40 rounded-lg px-4 py-2 text-amber-50 text-sm">
                    {m.user}
                  </div>
                </div>
                {m.bot && (
                  <div className="flex justify-start">
                    <div className="max-w-[75%] bg-amber-900/60 border border-amber-700/30 rounded-lg px-4 py-2 text-amber-50 text-sm">
                      {m.bot}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-amber-700/30">
            <div className="flex items-center bg-amber-900/40 border border-amber-700/30 rounded-full px-4 py-2">
              <input
                type="text"
                placeholder="Ask about Delhi..."
                className="flex-1 bg-transparent text-amber-100 placeholder-amber-300/70 outline-none text-sm"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              />
              <button
                onClick={sendMessage}
                className="ml-2 bg-orange-600/80 text-orange-100 hover:bg-orange-500/90 px-4 py-2 rounded-full text-sm font-medium"
              >
                ▶
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Ambient dots (keep aesthetic) */}
      <div className="absolute inset-0 z-5 pointer-events-none">
        {Array.from({ length: 15 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-amber-400/30 rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${3 + Math.random() * 2}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default ChattingPage;

