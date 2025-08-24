import React, { useState } from "react";
import bg from "../assets/bg.png";

const LandingPage1 = () => {
  const [messages, setMessages] = useState([]); // chat messages
  const [input, setInput] = useState(""); // input text
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text }),
      });
      const data = await res.json();
      const botMsg = { sender: "bot", text: data.reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Server error. Try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="relative min-h-screen w-full overflow-hidden"
      style={{
        backgroundImage: `url(${bg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Header */}
      <div className="absolute top-8 left-1/2 transform -translate-x-1/2 z-30 text-center">
        <h1 className="text-5xl font-bold text-amber-900">Chal Dilli</h1>
        <p className="text-amber-800 text-lg">The only map Dilliwalas trust</p>
      </div>

      {/* Chat Area */}
      <div className="absolute right-8 top-32 bottom-8 left-96 ml-8 z-20">
        <div
          className="relative w-full h-full rounded-2xl border border-amber-700/30 shadow-xl flex flex-col"
          style={{
            background:
              "linear-gradient(135deg, rgba(139, 69, 19, 0.8), rgba(101, 67, 33, 0.7))",
            backdropFilter: "blur(10px)",
          }}
        >
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg max-w-[70%] ${
                  msg.sender === "user"
                    ? "bg-amber-700 text-white self-end ml-auto"
                    : "bg-amber-300/50 text-black self-start mr-auto"
                }`}
              >
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className="text-amber-200 italic">Bot is typing...</div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-amber-700/30 flex space-x-3">
            <input
              className="flex-1 p-2 rounded-lg border border-amber-600/40 focus:outline-none"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type your message..."
            />
            <button
              onClick={sendMessage}
              className="px-4 py-2 bg-amber-700 text-white rounded-lg hover:bg-amber-600"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage1;

