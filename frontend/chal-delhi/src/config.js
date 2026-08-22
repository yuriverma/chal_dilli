// Central API configuration.
//
// Set these in a .env file (see .env.example) or in your host's build settings.
// Vite only exposes vars prefixed with VITE_, and it inlines them at BUILD
// time — changing them requires a rebuild, not just a restart.

// The Python "brain" (chat, routing, food, events).
export const BRAIN_API_URL = (
  import.meta.env.VITE_BRAIN_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

// The auth/user service. Optional: when unset, auth-dependent UI degrades
// instead of firing requests at a dead host.
export const AUTH_API_URL = (import.meta.env.VITE_AUTH_API_URL || "").replace(/\/$/, "");

export const AUTH_ENABLED = Boolean(AUTH_API_URL);

// Event source pages scraped via Parse.bot.
export const DEFAULT_NON_TECH_PAGE =
  import.meta.env.VITE_NON_TECH_EVENTS_URL ||
  "https://in.bookmyshow.com/explore/events-delhi-ncr";

export const DEFAULT_TECH_PAGE =
  import.meta.env.VITE_TECH_EVENTS_URL || "https://unstop.com/hackathons?filters=open";

export const CHAT_ENDPOINT = `${BRAIN_API_URL}/chat`;
export const PARSEBOT_NON_TECH_ENDPOINT = `${BRAIN_API_URL}/api/parse-events-from-url`;
export const PARSEBOT_TECH_ENDPOINT = `${BRAIN_API_URL}/api/parse-technical-events`;
