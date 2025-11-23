import React, { useState, useEffect} from 'react';
import bg2 from "../assets/bg2.mp4";

// const PARSEBOT_NON_TECH_ENDPOINT = "http://localhost:8000/api/parse-events-from-url";
const PARSEBOT_NON_TECH_ENDPOINT = "https://web-production-ca761.up.railway.app/api/parse-events-from-url";

// const PARSEBOT_TECH_ENDPOINT = "http://localhost:8000/api/parse-technical-events";
const PARSEBOT_TECH_ENDPOINT = "https://web-production-ca761.up.railway.app/api/parse-technical-events";

const DEFAULT_NON_TECH_PAGE = "https://in.bookmyshow.com/events/rambo-circus/ET00332998";
const DEFAULT_TECH_PAGE = "https://unstop.com/hackathons?filters=open";

const GENERAL_EVENT_KEYWORDS = [
  "event",
  "events",
  "what's happening",
  "happening",
  "upcoming",
  "things to do"
];

const TECH_EVENT_KEYWORDS = [
  "technical event",
  "technical events",
  "tech event",
  "tech-events",
  "tech-event",
  "tech events",
  "hackathon",
  "hackathons",
  "coding event",
  "coding events",
  "programming event",
  "programming events",
  "developer event",
  "developer events",
  "unstop",
  "tech fest",
  "techfest",
  "engineering event",
  "robotics competition",
  "ai conference"
];

const NON_TECH_EVENT_KEYWORDS = [
  "non technical",
  "non-technical",
  "non tech",
  "non-tech",
  "concert",
  "concerts",
  "music show",
  "music shows",
  "festivals",
  "festival",
  "standup",
  "stand-up",
  "comedy",
  "gig",
  "gigs",
  "party",
  "parties",
  "exhibition",
  "exhibitions",
  "cultural event",
  "cultural events",
  "bookmyshow"
];

const getEventIntent = (text = "") => {
  const query = text.toLowerCase();
  const mentionsGeneral = GENERAL_EVENT_KEYWORDS.some((keyword) => query.includes(keyword));
  const mentionsTech = TECH_EVENT_KEYWORDS.some((keyword) => query.includes(keyword));
  const mentionsNonTech = NON_TECH_EVENT_KEYWORDS.some((keyword) => query.includes(keyword));

  if (!mentionsGeneral && !mentionsTech && !mentionsNonTech) {
    return { tech: false, nonTech: false };
  }

  if (mentionsGeneral && !mentionsTech && !mentionsNonTech) {
    return { tech: true, nonTech: true };
  }

  return {
    tech: mentionsTech,
    nonTech: mentionsNonTech
  };
};

const extractNonTechEventList = (payload) => {
  if (!payload) return null;
  if (Array.isArray(payload.events)) return payload.events;
  if (Array.isArray(payload.parsebot_json?.events)) return payload.parsebot_json.events;
  if (Array.isArray(payload.parsebot_json?.data?.events)) return payload.parsebot_json.data.events;
  return null;
};

const extractTechEventList = (payload) => {
  if (!payload) return null;
  if (Array.isArray(payload.events)) return payload.events;
  if (Array.isArray(payload.data?.events)) return payload.data.events;
  if (Array.isArray(payload.results)) return payload.results;
  if (Array.isArray(payload.parsebot_json?.events)) return payload.parsebot_json.events;
  if (Array.isArray(payload.parsebot_json?.data?.events)) return payload.parsebot_json.data.events;
  return null;
};

const LoadingDots = () => (
  <div className="flex space-x-2 items-center">
    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
  </div>
);

const ChattingPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  // const [userName] = useState("Krish Batra");
  // const [userEmail] = useState("krish@chaldilli.com");
  const [userName, setUserName] = useState("Krish Batra");
const [userEmail, setUserEmail] = useState("krish@chaldilli.com");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { user: input, bot: null };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    const eventIntent = getEventIntent(input);

    try {
      // const res = await fetch("http://127.0.0.1:8000/chat", {
        const res = await fetch("https://web-production-ca761.up.railway.app/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });
      const data = await res.json();
      let nonTechPayload = null;
      let nonTechEvents = null;
      let techPayload = null;
      let techEvents = null;

      if (eventIntent.nonTech) {
        try {
          const eventRes = await fetch(PARSEBOT_NON_TECH_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              url: DEFAULT_NON_TECH_PAGE,
              debug: true,
            }),
          });
          nonTechPayload = await eventRes.json();
          nonTechEvents = extractNonTechEventList(nonTechPayload);
        } catch (eventError) {
          console.error("Non-technical event fetch error:", eventError);
        }
      }

      if (eventIntent.tech) {
        try {
          const techRes = await fetch(PARSEBOT_TECH_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              page_url: DEFAULT_TECH_PAGE,
            }),
          });
          techPayload = await techRes.json();
          techEvents = extractTechEventList(techPayload);
        } catch (techError) {
          console.error("Technical event fetch error:", techError);
        }
      }

      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          user: input,
          bot: data.response,
          recommendations: data.recommendations || null,
          nonTechEvents,
          techEvents,
          rawNonTechEvents: nonTechPayload,
          rawTechEvents: techPayload,
        },
      ]);
    } catch (err) {
      console.error("Error:", err);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { user: input, bot: "⚠️ Backend not reachable" },
      ]);
    } finally {
      setIsLoading(false);
    }

    setInput("");
  };

  useEffect(() => {
  const fetchUserDetails = async () => {
    try {
      const userId = localStorage.getItem("userId");
      if (!userId) return; // nothing to show if not logged in

      const res = await fetch(`https://cd-back-hnlv.onrender.com/api/users/${userId}`);
      if (!res.ok) {
        throw new Error("Failed to fetch user details");
      }

      const data = await res.json();
      if (data && data.user) {
        setUserName(data.user.full_name);
        setUserEmail(data.user.email);
      }
    } catch (err) {
      console.error("Error fetching user details for header:", err);
    }
  };

  fetchUserDetails();
}, []);


  return (
     <div className="relative min-h-screen w-full overflow-hidden">
  {/* Background Video */}
  <video
    src={bg2}
    autoPlay
    loop
    muted
    playsInline
    className="absolute top-0 left-0 w-full h-full object-cover -z-10"
  />
      {/* Header */}
      <div className="absolute top-2 md:top-4 left-1/2 transform -translate-x-1/2 z-30 px-4 text-center">
        <h1 className="text-4xl md:text-7xl font-bold text-black mb-1 md:mb-2">
          Chal Dilli
        </h1>
        <p className="text-black text-center text-sm md:text-lg font-semibold whitespace-nowrap">
          The only sathi for a Dilli vasi !!
        </p>  
      </div>

      {/* Hamburger Menu Button - Mobile Only */}
      <button
        onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
        className="lg:hidden absolute top-2 left-4 z-40 bg-amber-900/60 backdrop-blur-sm border border-amber-700/30 rounded-lg p-2 shadow-lg hover:bg-amber-900/80 transition-colors"
      >
        <div className="w-6 h-5 flex flex-col justify-between">
          <span className="block w-full h-0.5 bg-amber-100"></span>
          <span className="block w-full h-0.5 bg-amber-100"></span>
          <span className="block w-full h-0.5 bg-amber-100"></span>
        </div>
      </button>

      {/* Mobile Sidebar Overlay */}
      {isMobileSidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-35"
          onClick={() => setIsMobileSidebarOpen(false)}
        ></div>
      )}

      {/* Left Sidebar - Desktop and Mobile */}
      <div className={`${isMobileSidebarOpen ? 'fixed' : 'hidden'} lg:block absolute left-4 xl:left-8 top-28 xl:top-32 bottom-8 w-64 xl:w-80 z-40 lg:z-20`}>
        <div className="relative w-full h-full rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden flex flex-col"
          style={{
            background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div className="p-4 xl:p-6 border-b border-amber-700/30">
            <h2 className="text-lg xl:text-xl font-bold text-amber-100 mb-2">Recent Questions</h2>
            <p className="text-amber-200/80 text-xs xl:text-sm">Your Delhi exploration history</p>
          </div>
          <div className="flex-1 p-3 xl:p-4 overflow-y-auto space-y-2">
            {messages.slice(-6).map((m, i) => (
              <div 
                key={i} 
                className="bg-amber-900/40 hover:bg-amber-800/60 border border-amber-700/30 rounded-lg px-3 py-2 text-amber-100 text-xs xl:text-sm cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.02]"
              >
                {m.user}
              </div>
            ))}
          </div>
          
          {/* User Info at Bottom */}
          <div className="border-t border-amber-700/30 p-4 bg-amber-900/40 cursor-pointer hover:bg-amber-900/60 transition-colors" onClick={() => window.location.href = '/profile'}>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-white font-bold text-base flex-shrink-0">
                {userName.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-amber-100 font-medium text-sm truncate">{userName}</p>
                <p className="text-amber-200/70 text-xs truncate">{userEmail}</p>
              </div>
            </div>
          </div>
          
        </div>
      </div>

      {/* Chat Panel - Responsive */}
      <div className="absolute top-24 md:top-32 bottom-4 md:bottom-8 left-4 right-4 lg:left-72 xl:left-96 lg:right-8 xl:ml-8 z-20">
        <div className="relative w-full h-full rounded-xl md:rounded-2xl border border-amber-700/30 shadow-xl flex flex-col"
          style={{
            background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
            backdropFilter: 'blur(10px)',
          }}
        >
          {/* Header */}
          <div className="p-3 md:p-6 border-b border-amber-700/30">
            <h2 className="text-base md:text-xl font-bold text-amber-100">Chat with CHAL DILLI</h2>
            <p className="text-amber-200/80 text-xs md:text-sm mt-1">Ask me anything about Delhi!</p>
          </div>

          {/* Chat messages */}
          <div className="flex-1 p-3 md:p-6 space-y-3 md:space-y-4 overflow-y-auto">
            {messages.map((m, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-end">
                  <div className="max-w-[85%] md:max-w-[70%] bg-amber-800/40 rounded-lg px-3 md:px-4 py-2 text-amber-50 text-xs md:text-sm">
                    {m.user}
                  </div>
                </div>
                {m.bot && (
                  <div className="flex justify-start">
                    <div className="max-w-[90%] md:max-w-[75%] bg-amber-900/60 border border-amber-700/30 rounded-lg px-3 md:px-4 py-2 text-amber-50 text-xs md:text-sm whitespace-pre-wrap">
                      {m.bot}
                      {m.recommendations && (
                        <div className="mt-3 space-y-2 pt-2 border-t border-amber-700/30">
                          {m.recommendations.safe_pick && m.recommendations.safe_pick.zomato_url && (
                            <div>
                              <a
                                href={m.recommendations.safe_pick.zomato_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-block bg-red-600 hover:bg-red-700 text-white text-xs font-medium px-3 py-1.5 rounded-full transition-colors"
                              >
                                🍽️ Zomato - {m.recommendations.safe_pick.name}
                              </a>
                            </div>
                          )}
                          {m.recommendations.local_favourite && m.recommendations.local_favourite.zomato_url && 
                           m.recommendations.local_favourite.name !== m.recommendations.safe_pick?.name && (
                            <div>
                              <a
                                href={m.recommendations.local_favourite.zomato_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-block bg-red-600 hover:bg-red-700 text-white text-xs font-medium px-3 py-1.5 rounded-full transition-colors"
                              >
                                🍽️ Zomato - {m.recommendations.local_favourite.name}
                              </a>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {m.nonTechEvents && m.nonTechEvents.length > 0 && (
                        <div className="mt-4 space-y-3 pt-3 border-t border-amber-700/30">
                          <p className="text-amber-200 text-xs tracking-wide uppercase">🎉 Non-technical events (BookMyShow)</p>
                          {m.nonTechEvents.slice(0, 3).map((eventItem, idx) => {
                            const title = eventItem.title || eventItem.name || `Event ${idx + 1}`;
                            const date = eventItem.date || eventItem.start_date || eventItem.event_date;
                            const venue = eventItem.venue || eventItem.location || eventItem.city;
                            const link = eventItem.url || eventItem.event_url;
                            return (
                              <div key={`nontech-${idx}`} className="bg-amber-950/40 border border-amber-800/40 rounded-lg p-3 space-y-1 text-xs">
                                <p className="font-semibold text-amber-100">{title}</p>
                                {date && <p className="text-amber-200/80">📅 {date}</p>}
                                {venue && <p className="text-amber-200/80">📍 {venue}</p>}
                                {link && (
                                  <a
                                    href={link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-block text-amber-200 underline underline-offset-4"
                                  >
                                    View details
                                  </a>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {!m.nonTechEvents && m.rawNonTechEvents && (
                        <div className="mt-4 pt-3 border-t border-amber-700/30">
                          <p className="text-amber-200 text-xs tracking-wide uppercase mb-2">🎟️ Non-technical event details</p>
                          <pre className="text-[11px] leading-tight whitespace-pre-wrap break-words text-amber-100/90">
                            {JSON.stringify(m.rawNonTechEvents, null, 2)}
                          </pre>
                        </div>
                      )}
                      {m.techEvents && m.techEvents.length > 0 && (
                        <div className="mt-4 space-y-3 pt-3 border-t border-amber-700/30">
                          <p className="text-amber-200 text-xs tracking-wide uppercase">🛠️ Technical events & hackathons</p>
                          {m.techEvents.slice(0, 3).map((eventItem, idx) => {
                            const title = eventItem.title || eventItem.name || eventItem.event_name || `Hackathon ${idx + 1}`;
                            const date = eventItem.date || eventItem.start_date || eventItem.deadline || eventItem.event_date;
                            const venue = eventItem.venue || eventItem.location || eventItem.mode || eventItem.city;
                            const link = eventItem.url || eventItem.event_url || eventItem.link;
                            return (
                              <div key={`tech-${idx}`} className="bg-amber-950/40 border border-amber-800/40 rounded-lg p-3 space-y-1 text-xs">
                                <p className="font-semibold text-amber-100">{title}</p>
                                {date && <p className="text-amber-200/80">📅 {date}</p>}
                                {venue && <p className="text-amber-200/80">📍 {venue}</p>}
                                {link && (
                                  <a
                                    href={link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-block text-amber-200 underline underline-offset-4"
                                  >
                                    View details
                                  </a>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {!m.techEvents && m.rawTechEvents && (
                        <div className="mt-4 pt-3 border-t border-amber-700/30">
                          <p className="text-amber-200 text-xs tracking-wide uppercase mb-2">🧑‍💻 Technical event details</p>
                          <pre className="text-[11px] leading-tight whitespace-pre-wrap break-words text-amber-100/90">
                            {JSON.stringify(m.rawTechEvents, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading State */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[90%] md:max-w-[75%] bg-amber-900/60 border border-amber-700/30 rounded-lg px-3 md:px-4 py-3 text-amber-50 text-xs md:text-sm">
                  <div className="flex items-center space-x-3">
                    <LoadingDots />
                    <span className="text-amber-200/90">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-3 md:p-4 border-t border-amber-700/30">
            <div className="flex items-center bg-amber-900/40 border border-amber-700/30 rounded-full px-3 md:px-4 py-2">
              <input
                type="text"
                placeholder="Ask about Delhi..."
                className="flex-1 bg-transparent text-amber-100 placeholder-amber-300/70 outline-none text-xs md:text-sm"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isLoading && sendMessage()}
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading}
                className="ml-2 bg-orange-600/80 text-orange-100 hover:bg-orange-500/90 disabled:bg-orange-800/50 disabled:cursor-not-allowed px-3 md:px-4 py-1.5 md:py-2 rounded-full text-xs md:text-sm font-medium transition-colors"
              >
                ▶
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Ambient dots */}
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