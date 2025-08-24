import React from 'react';
import bg from "../assets/bg.png"

const LandingPage = () => {
  return (
    <div
      className="min-h-screen w-full relative overflow-hidden font-mono"
      style={{
        backgroundImage: `url(${bg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Overlay for better text readability */}
      <div className="absolute inset-0 bg-black/40 z-0" />

      {/* Main Title */}
      <div className="absolute top-8 left-1/2 transform -translate-x-1/2 z-30">
        <h1 className="text-5xl font-bold text-amber-900 text-center mb-2">Chal Dilli</h1>
        <p className="text-amber-800 text-center text-lg">The only map Dilliwalas trust</p>
      </div>

      {/* Terminal Boot Content */}
      <div className="relative z-10 px-12 pt-32 text-amber-100 text-sm space-y-3">
        <p><span className="text-amber-600">19:12:51</span> INCOMING HTTP REQUEST DETECTED ...</p>
        <p><span className="text-amber-600">19:12:54</span> SERVICE WAKING UP ...</p>

        <div
          className="text-xs text-white border border-white/20 p-4 rounded w-fit leading-tight"
          style={{
            background: 'linear-gradient(135deg, rgba(128, 128, 128, 0.1), rgba(128, 128, 128, 0.05))',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
        >
          <pre>
            {String.raw`
╔═════════════════════════════╗
║                             ║
║     WELCOME TO DIL SE       ║
║         DILLI               ║
║                             ║
╚═════════════════════════════╝`}
          </pre>
        </div>
        

        <p><span className="text-amber-600">19:12:58</span> ALLOCATING COMPUTE RESOURCES ...</p>
        <p><span className="text-amber-600">19:13:01</span> PREPARING INSTANCE FOR INITIALIZATION ...</p>
        <p><span className="text-amber-600">19:13:05</span> STARTING THE INSTANCE ...</p>
        <p><span className="text-amber-600">19:13:11</span> ENVIRONMENT VARIABLES INJECTED ...</p>
        <p><span className="text-amber-600">19:13:14</span> DIL SE DILLI: A local Delhi exploration chatbot</p>
        <p><span className="text-amber-600">19:13:17</span> READY TO CHAT ABOUT DELHI ...</p>

        {/* Additional Delhi-themed terminal messages */}
        {/* <p><span className="text-amber-600">19:13:20</span> LOADING DELHI KNOWLEDGE BASE ...</p>
        <p><span className="text-amber-600">19:13:23</span> ✓ RED FORT DATABASE CONNECTED</p>
        <p><span className="text-amber-600">19:13:25</span> ✓ CHANDNI CHOWK FOOD MAP LOADED</p>
        <p><span className="text-amber-600">19:13:27</span> ✓ METRO ROUTES SYNCHRONIZED</p>
        <p><span className="text-amber-600">19:13:30</span> ✓ LOCAL RECOMMENDATIONS ENGINE ACTIVE</p>
        <p><span className="text-amber-600">19:13:33</span> SYSTEM READY - ASK ME ABOUT DELHI!</p> */}

        {/* Blinking cursor */}
        <div className="flex items-center mt-4">
          <span className="text-amber-400">$</span>
          <span className="ml-2 text-amber-100">Waiting for your Delhi questions...</span>
          <span className="ml-1 text-amber-400 animate-pulse">|</span>
        </div>
      </div>

      {/* Delhi-themed floating particles */}
      <div className="absolute inset-0 z-5 pointer-events-none">
        {Array.from({ length: 15 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-amber-400/30 rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default LandingPage;