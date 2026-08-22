#!/usr/bin/env python3
"""
Enhanced Metro Router for CHAL DILLI
Integrates real GTFS data with language detection and nearby recommendations
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from metro_router import MetroRouter
from gate_lookup import get_best_gate_for_station, format_gate_suggestion

# Get absolute project root path
_BASE_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _BASE_DIR / "data"

class EnhancedMetroRouter:
    def __init__(self, gtfs_dir: str = None):
        """Initialize with GTFS data directory"""
        # Resolve GTFS path relative to this file if not provided
        if gtfs_dir is None:
            gtfs_dir = str(_DATA_DIR / "DMRC_GTFS (1)")
        self.gtfs_dir = gtfs_dir
        self.metro_router = None
        
        # Common station aliases to improve matching
        self.station_aliases: Dict[str, str] = {
            "aerocity": "delhi aerocity",
            "aero city": "delhi aerocity",
            "delhi aerocity": "delhi aerocity",
            "igi airport": "igi airport",
            "airport": "igi airport",
            "cp": "rajiv chowk",
            "connaught place": "rajiv chowk",
            "janakpuri west": "janak puri west",
            "janakpuri w": "janak puri west",
            "janak puri w": "janak puri west",
            "dwarka mor": "dwarka mor",
            "dwarka morh": "dwarka mor",
            "aiims": "aiims",
            "kashmere gate": "kashmere gate",
            "new delhi": "new delhi",
        }
        
        self._load_router()
        
        # Language detection patterns
        self.hindi_patterns = [
            r'[\u0900-\u097F]',  # Devanagari script
            r'\b(jaana|jao|jaiye|pahunch|pahuchna|station|stn|metro|line|route|jaaye|jaun|jaaun)\b',
            r'\b(kahan|kaise|kya|kaun|kis|kisne|kisko|kiski|kiski|kisne)\b',
            r'\b(mein|se|ko|ka|ki|ke|par|pe|se|tak|aur|ya|phir|fir|hai|hoga)\b'
        ]
        
        # Common Delhi destinations with coordinates for nearby recommendations
        self.destinations = {
            "connaught place": {"lat": 28.6315, "lon": 77.2167, "type": "commercial"},
            "cp": {"lat": 28.6315, "lon": 77.2167, "type": "commercial"},
            "chandni chowk": {"lat": 28.6562, "lon": 77.2410, "type": "historic"},
            "red fort": {"lat": 28.6562, "lon": 77.2410, "type": "historic"},
            "qutub minar": {"lat": 28.5245, "lon": 77.1855, "type": "historic"},
            "india gate": {"lat": 28.6129, "lon": 77.2295, "type": "monument"},
            "dwarka": {"lat": 28.5642, "lon": 77.0589, "type": "residential"},
            "airport": {"lat": 28.5562, "lon": 77.1000, "type": "transport"},
            "khan market": {"lat": 28.6001, "lon": 77.2274, "type": "food"},
            "dilli haat": {"lat": 28.5689, "lon": 77.2090, "type": "cultural"},
            "kashmere gate": {"lat": 28.6692, "lon": 77.2285, "type": "transport"},
            "rajiv chowk": {"lat": 28.6315, "lon": 77.2167, "type": "commercial"},
            "central secretariat": {"lat": 28.6129, "lon": 77.2090, "type": "government"},
            "noida": {"lat": 28.5355, "lon": 77.3910, "type": "commercial"},
            "gurgaon": {"lat": 28.4595, "lon": 77.0266, "type": "commercial"},
            "faridabad": {"lat": 28.4089, "lon": 77.3178, "type": "industrial"}
        }
    
    def _load_router(self):
        """Load the Metro router with GTFS data"""
        try:
            gtfs_path = Path(self.gtfs_dir)
            if gtfs_path.exists():
                self.metro_router = MetroRouter(str(gtfs_path))
                print(f"✅ Metro router loaded with GTFS data from {self.gtfs_dir}")
            else:
                print(f"⚠️ GTFS directory not found: {self.gtfs_dir}")
                print("Using fallback routing system...")
        except Exception as e:
            print(f"❌ Error loading Metro router: {e}")
            print("Using fallback routing system...")
    
    def detect_language(self, text: str) -> str:
        """Detect if text is Hindi, English, or Hinglish"""
        text_lower = text.lower()
        
        # Check for Hindi patterns
        hindi_score = 0
        for pattern in self.hindi_patterns:
            if re.search(pattern, text_lower):
                hindi_score += 1
        
        # Count Devanagari characters
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
        
        if devanagari_count > 0:
            return "hindi"
        elif hindi_score >= 2:
            return "hinglish"
        else:
            return "english"
    
    # Filler words that show up glued to the source when a user writes
    # "route dwarka to saket" or "fastest metro dwarka se cp".
    _LEADING_FILLER = (
        "please", "bhai", "yaar", "tell me", "the", "best", "fastest",
        "cheapest", "shortest", "metro route", "bus route", "route", "way",
        "path", "delhi metro", "metro", "train", "mujhe", "muje",
        # interrogatives / verbs that regex capture groups drag along
        "which", "what", "kaun si", "kaun", "kis", "how", "kaise",
        "line", "goes", "go", "leads", "connects", "reach", "get to", "jaana",
    )

    def normalize_station_name(self, name: str) -> str:
        """Map common aliases and clean station names for better matching"""
        n = name.strip().lower()
        # Remove trailing punctuation and helper words
        n = re.sub(r'[?!.,]+$', '', n).strip()
        for word in [" metro station", " station", " hai", " hoga", " please", " ka", " ki", " ke"]:
            if n.endswith(word):
                n = n[: -len(word)].strip()
        # Remove the word 'station' if user added it
        n = n.replace(" metro station", "").replace(" station", "").strip()
        # Strip leading filler so "route dwarka" resolves to "dwarka".
        # Loop because queries stack them: "tell me the fastest metro route ...".
        changed = True
        while changed:
            changed = False
            for filler in self._LEADING_FILLER:
                if n == filler:
                    return ""
                if n.startswith(filler + " "):
                    n = n[len(filler) + 1:].strip()
                    changed = True
        if n in self.station_aliases:
            return self.station_aliases[n]
        return n
    
    def extract_route_query(self, query: str) -> Optional[Dict]:
        """Extract source and destination from query"""
        query_lower = query.lower()
        
        # Common route patterns (ordered, more specific first)
        route_patterns = [
            r'(?:from|se)\s+([^?]+?)\s+(?:to|tak)\s+([^?]+)',
            # "X se Y tak" — source precedes "se", destination ends at "tak"
            r'([^?]+?)\s+se\s+([^?]+?)\s+tak\b',
            # "between X and Y"
            r'\bbetween\s+([^?]+?)\s+and\s+([^?]+)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:kaise|kese|how)\s+(?:jaana|jana|go|reach|pahunch|pahunche|jau|jao|jaiye|jaaye|jaye|jaun|jaaun)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:ka|kya)\s+(?:route|line|metro)',
            r'(?:how to|kaise|kahan se|kahan tak|route|way|path)\s+(?:go|jaana|jao|jaiye|reach|pahunch|jaaye|jaun|jaaun)\s+(?:to|tak|mein)\s+([^?]+)',
            # "which line goes to X" and the longer "which metro line goes to X"
            r'(?:which|kaun|kaun\s+si|kis)\s+(?:metro\s+)?(?:line|metro|route)\s+(?:goes|leads|connects|jaati|jati)?\s*(?:to|tak)\s+([^?]+)',
            # "how to reach/get to X", "kaise pahunche X"
            r'(?:how\s+(?:do\s+i\s+|can\s+i\s+)?(?:to\s+)?(?:reach|get\s+to|go\s+to))\s+([^?]+)',
            # Generic "X to Y". The original was `([^to]+?)` — a negated
            # character class banning the letters 't' and 'o', not the word
            # "to" — so it silently failed on most real queries.
            r'([^?]+?)\s+(?:to|tak)\s+([^?]+)',
            r'(?:how|kaise)\s+(?:to|tak)\s+([^?]+)',
            r'([^?]+)\s+(?:kaise|kese|how)\s+(?:jaana|jana|go|reach|pahunch|pahunche|jau|jao|jaiye|jaaye|jaye|jaun|jaaun)',
            r'([^?]+)\s+(?:ke liye|for)\s+(?:kaun|which)\s+(?:line|route)',
            # Last resort: plain "X se Y" without verb
            r'\b([^?]+?)\s+(?:se|from)\s+([^?]+?)\b'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if isinstance(matches[0], tuple) and len(matches[0]) == 2:  # from X to Y or X se Y
                    src_raw = matches[0][0]
                    dst_raw = matches[0][1]
                    src = self.normalize_station_name(src_raw).strip()
                    dst = self.normalize_station_name(dst_raw).strip()
                    # A pattern can match but leave nothing usable once filler
                    # words are stripped — fall through to the next pattern
                    # instead of returning an unresolvable empty station.
                    if not src or not dst:
                        continue
                    return {"from": src, "to": dst}
                else:  # just destination
                    dest = self.normalize_station_name(matches[0]).strip()
                    if not dest:
                        continue
                    return {"from": "current location", "to": dest}

        return None
    
    def get_route_response(self, query: str, language: str = "auto") -> Dict:
        """Get route response in the detected language"""
        if language == "auto":
            language = self.detect_language(query)
        
        route_info = self.extract_route_query(query)
        if not route_info:
            return self._get_general_metro_response(language)
        
        # Try to get route using Metro router
        if self.metro_router:
            try:
                # Primary: low-fare preference (discourage Airport Express)
                primary = self.metro_router.human_route(
                    route_info["from"], route_info["to"], smart_card=True, airport_penalty_min=9.0
                )
                alt = None
                # Alternative: fastest (no extra penalty)
                alt_candidate = self.metro_router.human_route(
                    route_info["from"], route_info["to"], smart_card=True, airport_penalty_min=0.0
                )
                if (
                    "error" not in primary and "error" not in alt_candidate and
                    (
                        primary.get("uses_airport_express", False) != alt_candidate.get("uses_airport_express", False)
                        or primary.get("duration_min") != alt_candidate.get("duration_min")
                    )
                ):
                    alt = alt_candidate
                
                if "error" in primary:
                    return self._get_fallback_route_response(route_info, language)
                
                return self._format_dual_route_response(primary, alt, language)
                
            except Exception as e:
                print(f"Error in Metro routing: {e}")
                return self._get_fallback_route_response(route_info, language)
        else:
            return self._get_fallback_route_response(route_info, language)
    
    def _format_dual_route_response(self, primary: Dict, alt: Optional[Dict], language: str) -> Dict:
        """Format primary (low fare) and optional alternative (faster) route."""
        def format_route(r: Dict, idx_prefix: str="") -> str:
            lines = []
            if language == "hindi":
                lines.append(f"{idx_prefix}Dur: ~{r['duration_min']} min • Dist: {r['distance_km']} km • Fare: ₹{r['estimated_fare']}")
            elif language == "hinglish":
                lines.append(f"{idx_prefix}Time: ~{r['duration_min']} min • Distance: {r['distance_km']} km • Fare: ₹{r['estimated_fare']}")
            else:
                lines.append(f"{idx_prefix}~{r['duration_min']} min • {r['distance_km']} km • Fare ₹{r['estimated_fare']}")
            for i, s in enumerate(r["segments"], 1):
                if language == "english":
                    lines.append(f"{i}. Take {s['line']} — {s['from']} → {s['to']}")
                else:
                    lines.append(f"{i}. {s['line']} — {s['from']} → {s['to']}")
            if r.get("uses_airport_express"):
                lines.append("Note: Uses Airport Express (higher fare).")
            return "\n".join(lines)
        
        header = {
            "hindi": f"Bhai, {primary['from']} se {primary['to']} tak ka route:",
            "hinglish": f"Bhai, {primary['from']} se {primary['to']} ka best low-fare route:",
            "english": f"Best low-fare route from {primary['from']} to {primary['to']}:"
        }[language if language in ["hindi","hinglish","english"] else "hinglish"]
        
        response = [header, format_route(primary)]
        if alt and alt != primary:
            alt_title = {
                "hindi": "\n\nAlternative faster route:",
                "hinglish": "\n\nAlternative (faster):",
                "english": "\n\nAlternative (faster):"
            }[language if language in ["hindi","hinglish","english"] else "hinglish"]
            response.append(alt_title)
            response.append(format_route(alt))
        
        # Add gate information for source and destination stations
        try:
            # Get gate for source station
            source_gate = get_best_gate_for_station(primary.get("from", ""))
            if source_gate:
                gate_text = format_gate_suggestion(source_gate, language)
                response.append(gate_text)
            
            # Get gate for destination station
            dest_gate = get_best_gate_for_station(primary.get("to", ""))
            if dest_gate:
                gate_text = format_gate_suggestion(dest_gate, language)
                response.append(gate_text)
        except Exception as e:
            # Silently fail - gate information is optional
            print(f"Note: Could not add gate information: {e}")
        
        final = "\n".join(response)
        
        return {
            "response": final,
            "route_data": primary,
            "language": language,
            "has_route": True
        }
    
    def _get_fallback_route_response(self, route_info: Dict, language: str) -> Dict:
        """Get fallback route response when GTFS data is not available"""
        dest = route_info["to"]

        # Destination-only query ("which line goes to saket"). We can't route
        # without an origin, so ask for one instead of the old dead-end
        # "coming soon" message.
        if route_info.get("from") == "current location":
            prompt = {
                "hindi": f"{dest.title()} tak ka route bata sakta hoon — bas batao kahan se chal rahe ho? Jaise: \"rajiv chowk se {dest} kaise jaana hai\".",
                "hinglish": f"Bhai, {dest.title()} tak ka pura route bata dunga — bas ye batao ki chal kahan se rahe ho? Jaise: \"rajiv chowk se {dest}\".",
                "english": f"I can route you to {dest.title()} — which station are you starting from? For example: \"from Rajiv Chowk to {dest}\".",
            }[language if language in ("hindi", "hinglish", "english") else "hinglish"]
            return {
                "response": prompt,
                "route_data": {"to": dest},
                "language": language,
                "has_route": False,
            }


        # Use our existing destination mapping
        if dest in self.destinations:
            dest_info = self.destinations[dest]
            
            if language == "hindi":
                response = f"Bhai, {dest.title()} ke liye best route:\n"
                response += f"Type: {dest_info['type']}\n"
                response += f"Coordinates: {dest_info['lat']}, {dest_info['lon']}\n"
                response += "Exact route calculation coming soon!\n"
                response += "Nearby recommendations add karne wale hain! 🍕🎉"
                
            elif language == "hinglish":
                response = f"Bhai, {dest.title()} ke liye route:\n"
                response += f"Type: {dest_info['type']}\n"
                response += "Exact route calculation coming soon!\n"
                
            else:  # english
                response = f"Route to {dest.title()}:\n"
                response += f"Type: {dest_info['type']}\n"
                response += "Exact route calculation coming soon!\n"
            
            return {
                "response": response,
                "route_data": {"to": dest, "type": dest_info['type']},
                "language": language,
                "has_route": True
            }
        
        # Generic response
        if language == "hindi":
            response = f"Bhai, {dest} ke liye route calculation coming soon!"
        elif language == "hinglish":
            response = f"Bhai, {dest} ke liye exact route calculation coming soon!"
        else:
            response = f"Route calculation for {dest} coming soon!"
        
        return {
            "response": response,
            "route_data": {"to": dest},
            "language": language,
            "has_route": False
        }
    
    def _get_general_metro_response(self, language: str) -> Dict:
        """Get general Metro information response"""
        if language == "hindi":
            response = "Delhi Metro ke baare mein kuch specific pucho! Route, fare, ya station?"
        elif language == "hinglish":
            response = "Delhi Metro ke baare mein kuch specific pucho! Route, fare, ya station?"
        else:
            response = "Ask me something specific about Delhi Metro! Route, fare, or station?"
        
        return {
            "response": response,
            "route_data": None,
            "language": language,
            "has_route": False
        }

# Test function
def test_enhanced_router():
    """Test the enhanced Metro router"""
    print("🚇 Testing Enhanced Metro Router...")
    
    router = EnhancedMetroRouter()
    
    test_queries = [
        "Dwarka se Kashmere Gate kaise jaaye?",
        "Dwarka se Rajiv Chowk kaise jaaye?",
        "dwarka se kashmere gate?",
        "dwarka se kashmere gate",
        "How to go to Connaught Place?",
        "Connaught Place kaise jaana hai?",
        "Which line goes to Qutub Minar?",
        "Qutub Minar ke liye kaun si line?",
        "From Dwarka to Airport",
        "Dwarka se Airport kaise jaana hai?",
        "aerocity se janakpuri west kaise jaana hai?"
    ]
    
    for query in test_queries:
        print(f"\n🧑 User: {query}")
        result = router.get_route_response(query)
        print(f"🤖 CHAL DILLI: {result['response']}")
        print(f"Language: {result['language']}")
        print(f"Has Route: {result['has_route']}")

if __name__ == "__main__":
    test_enhanced_router()
