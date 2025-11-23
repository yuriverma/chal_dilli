




import React, { useEffect, useRef, useState } from 'react';
import bg2 from "../assets/bg2.MP4";

const LandingPage = () => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showStartScreen, setShowStartScreen] = useState(true);

  const handleStartExperience = () => {
    setShowStartScreen(false);
    if (audioRef.current) {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(error => {
        console.log("Audio play failed:", error);
      });
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !audioRef.current.muted;
      setIsMuted(!isMuted);
    }
  };

  useEffect(() => {
    // Cleanup: pause audio when component unmounts
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  return (
    <div className="min-h-screen w-full relative overflow-hidden font-mono">
      {/* Background Video */}
      <video
        src={bg2}
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover -z-10"
      />

      {/* Background Audio */}
      <audio
        ref={audioRef}
        loop
        preload="auto"
      >
        <source src="/bg_music.m4a" type="audio/mp4" />
        Your browser does not support the audio element.
      </audio>

      {/* Start Experience Overlay */}
      {showStartScreen && (
        <div className="absolute inset-0 bg-black/80 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-white mb-6">Welcome to Chal Dilli</h2>
            <button
              onClick={handleStartExperience}
              className="px-8 py-4 bg-amber-500 hover:bg-amber-600 text-white text-xl font-bold rounded-lg transition-all transform hover:scale-105 shadow-lg"
            >
              Delhi mein aapka Swagat hai
            </button>
            {/* <p className="text-white/70 mt-4 text-sm">Click to enable audio</p> */}
          </div>
        </div>
      )}

      {/* Overlay for better text readability */}
      <div className="absolute inset-0 bg-black/40 z-0" />

      {/* Mute/Unmute Button */}
      {isPlaying && (
        <button
          onClick={toggleMute}
          className="absolute top-6 right-6 z-40 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full transition-all backdrop-blur-sm"
          aria-label={isMuted ? "Unmute" : "Mute"}
        >
          {isMuted ? (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          )}
        </button>
      )}

      {/* Main Title - Centered */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-30">
        <h1 className="text-7xl font-bold text-white text-center mb-4">
          <span className="inline-block overflow-hidden whitespace-nowrap animate-typing">
            Chal Dilli
            <br />
            चल दिल्ली
            <br />
            ਚਲ ਦਿੱਲੀ
            <br />
            چل دہلی
          </span>
        </h1>
        <p className="text-white text-center text-2xl">DILWALE SE PUCHO DILLI KA RASTA</p>
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

      <style jsx>{`
        @keyframes typing {
          from {
            width: 0;
          }
          to {
            width: 100%;
          }
        }
        .animate-typing {
          animation: typing 2s steps(10, end) forwards;

          
        }
      `}</style>
    </div>
  );
};

export default LandingPage;
