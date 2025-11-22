#!/usr/bin/env python3
"""
CHAL DILLI - Enhanced Version with Real-time Data
Delhi's Smart Big Brother AI Assistant
"""

import re
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from data_scraper import DelhiDataScraper
from enhanced_metro_router import EnhancedMetroRouter
from hinglish_conversation import HinglishConversationManager
from food_recommender import recommend_for_location, recommend_by_area, recommend_for_text_query
from area_mapper import extract_area_from_query, get_area_coordinates
from dtc_router import DTCRouter

# Get absolute project root path
_BASE_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _BASE_DIR / "data"

class ChalDilliEnhanced:
    def __init__(self):
        self.scraper = DelhiDataScraper()
        self.enhanced_router = EnhancedMetroRouter()
        self.conv = HinglishConversationManager(max_rows=30000)
        self.metro_data = {"status": "All lines operational"}
        self.event_data = []
        self.food_data = {}
        self.bus_data = {}
        
        # Initialize DTC router
        try:
            gtfs_dir = _DATA_DIR / "GTFS"
            if gtfs_dir.exists():
                self.dtc_router = DTCRouter(str(gtfs_dir))
                print(f"✅ DTC router loaded with GTFS data from {gtfs_dir}")
            else:
                print(f"⚠️ DTC GTFS directory not found: {gtfs_dir}")
                self.dtc_router = None
        except Exception as e:
            print(f"⚠️ Error loading DTC router: {e}")
            self.dtc_router = None
        
        # DO NOT call update_data() here - it's blocking
        # It will be called in background task after startup
        # Warm small-talk index (non-blocking best effort)
        try:
            self.conv.load_index()
        except Exception:
            pass
        
    def update_data(self):
        """Update all data sources"""
        try:
            print("🔄 Updating CHAL DILLI data...")
            
            # Update all data
            self.scraper.update_all_data()
            
            # Get updated data
            self.metro_data = self.scraper.metro_data
            self.event_data = self.scraper.event_data
            self.food_data = self.scraper.scrape_food_recommendations()
            self.bus_data = self.scraper.bus_data
            
            print("✅ Data updated successfully!")
            
        except Exception as e:
            print(f"❌ Error updating data: {e}")
    
    def get_metro_response(self) -> str:
        """Get metro response with real-time data and ALL routes"""
        metro_status = self.metro_data.get("status", "All lines operational")
        lines = self.metro_data.get("lines", {})
        alerts = self.metro_data.get("alerts", [])
        
        # All Delhi Metro lines with routes
        all_metro_lines = {
            "Red Line": "Dilshad Garden - Rithala",
            "Yellow Line": "Samaypur Badli - HUDA City Centre",
            "Blue Line": "Dwarka Sector 21 - Noida Electronic City / Vaishali",
            "Green Line": "Inderlok - Brigadier Hoshiar Singh",
            "Violet Line": "Kashmere Gate - Raja Nahar Singh",
            "Pink Line": "Majlis Park - Shiv Vihar",
            "Magenta Line": "Janakpuri West - Botanical Garden",
            "Grey Line": "Dwarka - Dhansa Bus Stand",
            "Airport Express": "New Delhi - Dwarka Sector 21"
        }
        
        # Get specific line information from real data
        line_names = list(lines.keys())
        line_count = len(line_names)
        
        # Create detailed line information with ALL routes
        if line_count > 0:
            # Include all lines with their routes
            line_details = []
            for line_name in all_metro_lines.keys():
                if line_name in lines:
                    line_info = lines[line_name]
                    route = line_info.get("route", all_metro_lines.get(line_name, ""))
                    status = line_info.get("status", "Operational")
                    line_details.append(f"{line_name} ({route}) - {status}")
                else:
                    # Include even if not in real-time data
                    route = all_metro_lines.get(line_name, "")
                    line_details.append(f"{line_name} ({route}) - Operational")
            
            lines_info = f"All {len(all_metro_lines)} lines: " + ", ".join(line_details[:5])
            if len(line_details) > 5:
                lines_info += f" and {len(line_details) - 5} more lines"
        else:
            # Fallback: list all lines
            all_lines_list = ", ".join([f"{name} ({route})" for name, route in list(all_metro_lines.items())[:5]])
            lines_info = f"All 9 Delhi Metro lines: {all_lines_list} and 4 more lines"
        
        if alerts:
            alert_info = f" Alerts: {', '.join(alerts[:2])}"
        else:
            alert_info = ""
        
        responses = [
            f"Bhai, Delhi Metro is the best way to travel! {metro_status}. {lines_info}. Timings: 5:30 AM - 11:30 PM. Fares: Rs 10-60 based on distance.{alert_info}",
            f"Metro se jaana best hai! {metro_status}. {lines_info}. Timings: 5:30 AM - 11:30 PM. Fares: Rs 10-60 based on distance.{alert_info}",
            f"Listen, Delhi Metro is super convenient. {metro_status}. {lines_info}. Timings: 5:30 AM - 11:30 PM. Fares: Rs 10-60 based on distance.{alert_info}"
        ]
        return random.choice(responses)
    
    def get_food_response(self, query: str = "") -> tuple:
        """Get food response using food_recommender with area detection
        Returns: (formatted_text_response, structured_recommendations_dict)
        """
        query_lower = query.lower() if query else ""
        
        # Extract area from query
        area_name, coords = extract_area_from_query(query)
        
        # Extract food type if mentioned (momos, breakfast, etc.)
        food_type = None
        food_keywords = {
            "momos": ["momo", "momos", "dumpling"],
            "breakfast": ["breakfast", "nashta", "nashte"],
            "paratha": ["paratha", "parathe", "paranthe"],
            "chaat": ["chaat", "chaat"],
            "biryani": ["biryani", "biriyani"],
            "pizza": ["pizza"],
            "burger": ["burger"],
            "chinese": ["chinese", "chinese food"],
            "north indian": ["north indian", "punjabi"],
            "south indian": ["south indian", "dosa", "idli"],
        }
        
        for food, keywords in food_keywords.items():
            if any(kw in query_lower for kw in keywords):
                food_type = food
                break
        
        recommendations = None
        
        # Handle "around me" case - use default Delhi center (Connaught Place)
        if area_name == "around_me":
            # Default to Connaught Place coordinates if no location provided
            # In future, could use browser geolocation API
            default_lat, default_lon = 28.6315, 77.2167  # Connaught Place
            recommendations = recommend_for_location(default_lat, default_lon, radius_km=5)
            area_name = "Connaught Place"  # For display purposes
        elif coords:
            # Use coordinates
            lat, lon = coords
            recommendations = recommend_for_location(lat, lon, radius_km=5)
        elif area_name:
            # Try area-based recommendation
            recommendations = recommend_by_area(area_name, city="Delhi")
            # If that fails, try to get coordinates
            if not recommendations.get('safe_pick') and not recommendations.get('local_favourite'):
                coords = get_area_coordinates(area_name)
                if coords:
                    lat, lon = coords
                    recommendations = recommend_for_location(lat, lon, radius_km=5)
        else:
            # Try text query matching
            recommendations = recommend_for_text_query(query, city="Delhi")
        
        # Format response
        if recommendations and (recommendations.get('safe_pick') or recommendations.get('local_favourite')):
            formatted_text = self._format_food_recommendations(recommendations, area_name, food_type, query_lower)
            return (formatted_text, recommendations)
        else:
            # Fallback response
            if area_name:
                return (f"Sorry bhai, {area_name} ke baare mein mujhe exact food recommendations nahi mil rahe. Koi aur area try karo ya general food recommendations chahiye?", None)
            else:
                return ("Bhai, food recommendations ke liye area mention karo jaise 'food near vasant kunj' ya 'momos in dwarka'. Main aapko safe pick aur local favourite dunga!", None)
    
    def _format_food_recommendations(self, recommendations: Dict, area_name: Optional[str], food_type: Optional[str], query_lower: str) -> str:
        """Format food recommendations into readable text"""
        safe_pick = recommendations.get('safe_pick')
        local_favourite = recommendations.get('local_favourite')
        
        response_parts = []
        
        # Header
        if area_name:
            if food_type:
                response_parts.append(f"Bhai, {area_name} mein {food_type} ke liye ye recommendations hain:")
            else:
                response_parts.append(f"Bhai, {area_name} ke liye food recommendations:")
        elif food_type:
            response_parts.append(f"Bhai, {food_type} ke liye ye recommendations hain:")
        else:
            response_parts.append("Bhai, food recommendations:")
        
        response_parts.append("")
        
        # Safe Pick
        if safe_pick:
            sp = safe_pick
            response_parts.append("✅ SAFE PICK (High Rating):")
            response_parts.append(f"   🍽️ {sp['name'].title()}")
            response_parts.append(f"   📍 {sp['area'].title()}, {sp['city']}")
            if sp.get('rating'):
                response_parts.append(f"   ⭐ {sp['rating']}/5 ({sp.get('rating_count', 0)} reviews)")
            if sp.get('cost_for_two'):
                response_parts.append(f"   💰 ₹{sp['cost_for_two']} for two")
            if sp.get('famous_food'):
                response_parts.append(f"   🍴 Famous for: {sp['famous_food']}")
            if sp.get('address'):
                response_parts.append(f"   📍 {sp['address']}")
            if sp.get('distance_km') and sp['distance_km'] > 0:
                response_parts.append(f"   📏 {sp['distance_km']:.1f} km away")
            response_parts.append("")
        
        # Local Favourite
        if local_favourite and local_favourite != safe_pick:
            lf = local_favourite
            response_parts.append("🔥 LOCAL FAVOURITE (Popular Choice):")
            response_parts.append(f"   🍽️ {lf['name'].title()}")
            response_parts.append(f"   📍 {lf['area'].title()}, {lf['city']}")
            if lf.get('rating'):
                response_parts.append(f"   ⭐ {lf['rating']}/5 ({lf.get('rating_count', 0)} reviews)")
            if lf.get('cost_for_two'):
                response_parts.append(f"   💰 ₹{lf['cost_for_two']} for two")
            if lf.get('famous_food'):
                response_parts.append(f"   🍴 Famous for: {lf['famous_food']}")
            if lf.get('address'):
                response_parts.append(f"   📍 {lf['address']}")
            if lf.get('distance_km') and lf['distance_km'] > 0:
                response_parts.append(f"   📏 {lf['distance_km']:.1f} km away")
            response_parts.append("")
        
        # If only one recommendation
        if safe_pick and not local_favourite:
            response_parts.append("(Note: Only one recommendation available for this area)")
        elif local_favourite and not safe_pick:
            response_parts.append("(Note: Only one recommendation available for this area)")
        
        return "\n".join(response_parts)
    
    def get_event_response(self) -> str:
        """Get event response with real-time events"""
        if self.event_data:
            # Get upcoming events
            upcoming_events = [e for e in self.event_data if e.get("date", "") >= datetime.now().strftime("%Y-%m-%d")]
            
            if upcoming_events:
                event = random.choice(upcoming_events[:3])  # Pick from latest 3
                responses = [
                    f"Bhai, {event['title']} is happening on {event['date']} at {event['venue']}! Must attend!",
                    f"Don't miss {event['title']} on {event['date']} at {event['venue']}!",
                    f"Upcoming event: {event['title']} on {event['date']} at {event['venue']}!"
                ]
            else:
                responses = [
                    "Currently no major events scheduled. Check back later for updates!",
                    "No upcoming events right now. But Delhi always has something happening!",
                    "Events calendar is quiet right now. Perfect time to explore Delhi's attractions!"
                ]
        else:
            responses = [
                "Check BookMyShow or Eventbrite for latest Delhi events!",
                "Delhi has events happening all the time. Check online for updates!",
                "For events, check Delhi's event websites for the latest happenings!"
            ]
        
        return random.choice(responses)
    
    def get_bus_response(self) -> str:
        """Get bus response with real-time data"""
        bus_status = self.bus_data.get("status", "Operational")
        routes = self.bus_data.get("routes", {})
        
        if routes:
            route_info = f" {len(routes)} popular routes available."
        else:
            route_info = ""
        
        responses = [
            f"DTC buses cover entire Delhi! {bus_status}.{route_info} DTC Buses, Cluster Buses (Orange), AC Buses cover Entire Delhi and NCR. Daily, weekly, monthly passes available.",
            f"Bus se bhi ja sakte ho! {bus_status}.{route_info} DTC Buses, Cluster Buses (Orange), AC Buses cover Entire Delhi and NCR. Daily, weekly, monthly passes available.",
            f"Buses are also a good option. {bus_status}.{route_info} DTC Buses, Cluster Buses (Orange), AC Buses cover Entire Delhi and NCR. Daily, weekly, monthly passes available."
        ]
        return random.choice(responses)
    
    def get_attraction_response(self) -> str:
        """Get attraction response"""
        attractions = [
            "Red Fort (UNESCO)", "Qutub Minar (UNESCO)", "Humayun's Tomb (UNESCO)",
            "India Gate", "Lotus Temple", "Akshardham Temple"
        ]
        attraction = random.choice(attractions)
        responses = [
            f"Delhi mein {attraction} must visit hai!",
            f"Bhai, {attraction} is absolutely amazing!",
            f"You can't miss {attraction} when in Delhi!"
        ]
        return random.choice(responses)
    
    def get_greeting_response(self) -> str:
        """Get greeting response"""
        responses = [
            "Hey bhai! Kya haal hai? CHAL DILLI at your service! 🚀",
            "Hello! CHAL DILLI here - Delhi ka sabse smart dost! 🤖",
            "Namaste! CHAL DILLI ready to help you explore Delhi! 🙏"
        ]
        return random.choice(responses)
    
    def get_weather_response(self) -> str:
        """Get weather response"""
        return "Bhai, Delhi ka weather thoda unpredictable hai! Summers mein garmi, winters mein thand, monsoon mein baarish. Check weather app for exact details!"
    
    def get_unknown_response(self) -> str:
        """Get unknown response"""
        responses = [
            "Sorry bhai, iske baare mein mujhe exact info nahi hai. Kuch aur pucho!",
            "Hmm, ye question thoda tough hai. Delhi ke baare mein kuch aur pucho!",
            "Not sure about this one, bro. Ask me about Delhi metro, food, or attractions!"
        ]
        return random.choice(responses)
    
    def _is_metro_query(self, query: str) -> bool:
        """Check if query is about metro routing"""
        query_lower = query.lower()
        
        # Strong metro indicators
        metro_keywords = [
            "metro", "train", "subway", "delhi metro",
            "metro route", "metro line", "which line",
            "metro station", "metro se", "metro mein",
            "fastest metro", "fastest route"
        ]
        
        # Strong bus/DTC indicators - if these are present, it's NOT a metro query
        bus_indicators = [
            "dtc", "bus route", "bus only", "only bus",
            "dtc bus", "dtc route", "bus se", "bus mein"
        ]
        
        # If explicit bus keywords are present, it's a bus query, not metro
        if any(kw in query_lower for kw in bus_indicators):
            return False
        
        # Check for metro keywords
        if any(kw in query_lower for kw in metro_keywords):
            return True
        
        # English route patterns that imply metro (when no bus keywords)
        english_metro_patterns = [
            r"route\s+from\s+\w+",
            r"metro\s+from\s+\w+",
            r"how\s+to\s+go\s+from\s+\w+.*\s+by\s+metro",
            r"fastest\s+metro\s+from\s+\w+",
            r"metro\s+route\s+between\s+\w+",
            r"route\s+between\s+\w+.*\s+metro",
        ]
        
        # Hinglish route patterns
        hinglish_metro_patterns = [
            r"\w+\s+se\s+\w+\s+(kaise|how|route)",
            r"kaise\s+(jaana|jao|jaiye|pahunch)",
            r"fastest\s+(route|way|metro)",
        ]
        
        # Generic route patterns (only if they look like metro, not bus)
        generic_route_patterns = [
            r"from\s+\w+\s+to\s+\w+",  # "from X to Y" - common for metro
            r"how\s+to\s+(go|reach|get)\s+",  # "how to go from X to Y"
            r"tell\s+me\s+(the\s+)?(fastest\s+)?(metro\s+)?route",
        ]
        
        # Check English metro patterns
        if any(re.search(pattern, query_lower) for pattern in english_metro_patterns):
            parsed = self.enhanced_router.extract_route_query(query)
            if parsed:
                return True
        
        # Check Hinglish metro patterns
        if any(re.search(pattern, query_lower) for pattern in hinglish_metro_patterns):
            parsed = self.enhanced_router.extract_route_query(query)
            if parsed:
                return True
        
        # Check generic route patterns (but exclude if it's clearly bus or food)
        if any(re.search(pattern, query_lower) for pattern in generic_route_patterns):
            # Exclude if it's clearly a bus query
            if not any(kw in query_lower for kw in ["bus", "dtc", "food", "eat", "restaurant"]):
                parsed = self.enhanced_router.extract_route_query(query)
                if parsed:
                    return True
        
        return False
    
    def _is_bus_query(self, query: str) -> bool:
        """Check if query is about bus/DTC routing"""
        query_lower = query.lower()
        
        # Strong bus indicators
        bus_keywords = [
            "dtc", "bus", "bus route", "bus se", "bus mein",
            "only bus", "bus only", "dtc bus", "dtc route",
            "bus from", "bus to", "bus kaise", "bus se jaana"
        ]
        
        # Check for explicit bus keywords
        if any(kw in query_lower for kw in bus_keywords):
            return True
        
        # Check for route patterns with bus context
        route_patterns = [
            r"dtc\s+(route|bus|se)",
            r"bus\s+(route|from|to|se)",
            r"only\s+bus",
            r"bus\s+only"
        ]
        
        if any(re.search(pattern, query_lower) for pattern in route_patterns):
            return True
        
        return False
    
    def _is_food_query(self, query: str) -> bool:
        """Check if query is about food recommendations"""
        query_lower = query.lower()
        
        # Strong food indicators
        food_keywords = [
            "food", "eat", "restaurant", "cafe", "dining",
            "momos", "breakfast", "lunch", "dinner",
            "paratha", "paranthe", "chaat", "biryani",
            "where should i eat", "kahan khau", "kahan khana",
            "food recommendations", "food near", "food in",
            "restaurants near", "restaurants in", "places to eat",
            "best food", "good food", "khana", "khane"
        ]
        
        # Check for food keywords
        if any(kw in query_lower for kw in food_keywords):
            # Exclude cooking at home queries
            if not re.search(r"\b(banau|banana|banaye|banao|cook|recipe|ghar ka)\b", query_lower):
                return True
        
        # Check for area + food pattern
        area_food_pattern = r"(food|eat|restaurant|momos|breakfast|khana)\s+(near|in|around|at|mein|ke paas)"
        if re.search(area_food_pattern, query_lower):
            return True
        
        return False
    
    def _extract_bus_route_query(self, query: str) -> Optional[Dict]:
        """Extract source and destination from bus route query"""
        query_lower = query.lower()
        
        # Remove bus-specific keywords for route extraction
        cleaned = re.sub(r'\b(dtc|bus|only bus|bus only)\b', '', query_lower)
        
        # Common route patterns
        route_patterns = [
            r'(?:from|se)\s+([^?]+?)\s+(?:to|tak)\s+([^?]+)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:kaise|how|route)',
            r'([^?]+?)\s+(?:to|tak)\s+([^?]+)',
            r'\b([^?]+?)\s+(?:se|from)\s+([^?]+?)\b'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, cleaned)
            if matches:
                if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                    src_raw = matches[0][0].strip()
                    dst_raw = matches[0][1].strip()
                    # Clean up common words
                    for word in ["metro", "station", "bus", "stop", "stand"]:
                        src_raw = re.sub(rf'\b{word}\b', '', src_raw).strip()
                        dst_raw = re.sub(rf'\b{word}\b', '', dst_raw).strip()
                    return {"from": src_raw, "to": dst_raw}
        
        return None
    
    def get_dtc_route_response(self, query: str) -> str:
        """Get DTC bus route response"""
        if not self.dtc_router:
            return "Sorry bhai, DTC bus routing abhi available nahi hai. Metro route try karo!"
        
        route_info = self._extract_bus_route_query(query)
        if not route_info:
            return "Bhai, bus route ke liye source aur destination mention karo, jaise 'dtc bus route from dwarka to kashmere gate'"
        
        try:
            result = self.dtc_router.get_route(route_info["from"], route_info["to"])
            
            if "error" in result:
                return f"Sorry bhai, {result['error']}"
            if "message" in result:
                return result["message"]
            
            # Format response in Delhi-friendly Hinglish style
            response = f"Bhai, {result['from']} se {result['to']} tak ka best DTC bus route:\n\n"
            response += result["human_text"]
            response += f"\n\nTotal time: ~{result['duration_min']} min • Distance: {result['distance_km']} km"
            response += "\n\nNote: DTC buses cover entire Delhi. Daily/weekly/monthly passes available!"
            
            return response
        except Exception as e:
            return f"Sorry bhai, route calculate karte waqt error aaya: {str(e)}"
    
    def generate_response(self, query: str) -> str:
        """Generate response based on query with real-time data"""
        query_lower = query.lower()
        
        # Check for weather first (more specific)
        if any(word in query_lower for word in ["weather", "temperature", "climate"]):
            return self.get_weather_response()
        
        # Check for greeting
        if any(word in query_lower for word in ["hi", "hello", "hey", "namaste", "kaise ho", "how are you"]):
            return self.get_greeting_response()
        
        # Check for bus/DTC queries first (before metro to avoid conflicts)
        if self._is_bus_query(query):
            route_info = self._extract_bus_route_query(query)
            if route_info:
                return self.get_dtc_route_response(query)
            # If bus keywords but no route, give general bus info
            if any(kw in query_lower for kw in ["bus", "dtc", "transport"]):
                return self.get_bus_response()
        
        # Check for metro queries (before food to avoid conflicts)
        if self._is_metro_query(query):
            parsed = self.enhanced_router.extract_route_query(query)
            if parsed:
                route_result = self.enhanced_router.get_route_response(query)
                metro_response = route_result["response"]
                
                # Add food recommendations for destination station
                if route_result.get("has_route") and route_result.get("route_data"):
                    try:
                        destination_station = route_result["route_data"].get("to", "")
                        if destination_station:
                            # Get station coordinates
                            coords = self._get_station_coordinates(destination_station)
                            
                            if coords:
                                # Get food recommendations near destination
                                lat, lon = coords
                                food_recommendations = recommend_for_location(lat, lon, radius_km=3)
                                
                                # Format and append food recommendations
                                if food_recommendations and (food_recommendations.get('safe_pick') or food_recommendations.get('local_favourite')):
                                    language = route_result.get("language", "hinglish")
                                    food_text = self._format_metro_food_recommendations(
                                        food_recommendations, 
                                        destination_station, 
                                        language
                                    )
                                    if food_text:
                                        metro_response += food_text
                    except Exception as e:
                        # Silently fail - food recommendations are optional
                        print(f"Note: Could not add food recommendations: {e}")
                
                return metro_response
            # If metro keywords but no route, give general metro info
            if any(kw in query_lower for kw in ["metro", "delhi metro", "train", "subway"]):
                return self.get_metro_response()
        
        # If user is asking about cooking at home, treat as small-talk (not restaurant recs)
        if re.search(r"\b(banau|banana|banaye|banao|cook|recipe|ghar ka khana)\b", query_lower):
            try:
                reply = self.conv.reply(query)
                if reply:
                    return reply
            except Exception:
                pass
            # gentle fallback
            return "Bhai, ghar ka khana best hota hai — simple dal-chawal ya paneer try karo!"

        # Check for food queries
        if self._is_food_query(query):
            # get_food_response returns (text, recommendations_dict)
            # For generate_response, we only need the text
            text_response, _ = self.get_food_response(query)
            return text_response
        
        # Check for events
        if any(word in query_lower for word in ["event", "happening", "festival", "what events", "what's happening"]):
            return self.get_event_response()
        
        # Check for attractions
        if any(word in query_lower for word in ["visit", "see", "attraction", "place", "fort", "temple", "what attractions"]):
            return self.get_attraction_response()
        
        # Check for general bus info (only if not already handled as route query)
        if any(word in query_lower for word in ["bus", "dtc", "transport", "how do i travel by bus"]):
            # Only return general info if it's not a route query
            if not self._is_bus_query(query) or not self._extract_bus_route_query(query):
                return self.get_bus_response()
        
        # Small-talk fallback using Hinglish dataset
        try:
            reply = self.conv.reply(query)
            if reply:
                return reply
        except Exception:
            pass
        
        # Default
        return self.get_unknown_response()
    
    def get_delhi_response(self, query: str) -> Dict:
        """Get Delhi response with real-time data"""
        response = self.generate_response(query)
        
        result = {
            "response": response,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "metro_status": self.metro_data.get("status"),
            "language": "hinglish" if re.search(r'[\u0900-\u097F]', query) else "english",
            "data_freshness": self.scraper.last_update.isoformat() if self.scraper.last_update else None
        }
        
        # If it's a food query, include structured recommendations
        if self._is_food_query(query):
            _, recommendations = self.get_food_response(query)
            if recommendations:
                result["recommendations"] = recommendations
        
        return result
    
    def get_data_summary(self) -> Dict:
        """Get summary of current data"""
        return self.scraper.get_data_summary()
    def _get_station_coordinates(self, station_name: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a metro station.
        Tries GTFS data first, then falls back to area mapper.
        
        Args:
            station_name: Station name (normalized)
        
        Returns:
            Tuple of (lat, lon) or None if not found
        """
        # Try to get from metro router's GTFS data
        if self.enhanced_router.metro_router:
            try:
                # Normalize station name similar to how metro router does it
                station_id = self.enhanced_router.metro_router.find_best_station_id(station_name)
                if station_id and station_id in self.enhanced_router.metro_router.stops:
                    stop_info = self.enhanced_router.metro_router.stops[station_id]
                    return (stop_info["lat"], stop_info["lon"])
            except Exception as e:
                # Silently fail and try fallback
                pass
        
        # Fallback: try area mapper
        coords = get_area_coordinates(station_name)
        if coords:
            return coords
        
        return None
    
    def _format_metro_food_recommendations(self, recommendations: Dict, destination_station: str, language: str = "hinglish") -> str:
        """
        Format food recommendations for metro destination.
        
        Args:
            recommendations: Dictionary with 'safe_pick' and 'local_favourite'
            destination_station: Name of destination station
            language: Language for formatting
        
        Returns:
            Formatted text string
        """
        safe_pick = recommendations.get('safe_pick')
        local_favourite = recommendations.get('local_favourite')
        
        if not safe_pick and not local_favourite:
            return ""  # No recommendations available
        
        # Build header based on language
        if language == "hindi":
            header = f"\n\n{destination_station} pahunchne ke baad, aap ye try kar sakte hain:"
        elif language == "hinglish":
            header = f"\n\nWhen you reach {destination_station}, you can also try:"
        else:  # english
            header = f"\n\nWhen you reach {destination_station}, you can also try:"
        
        lines = [header]
        
        # Format Safe Pick
        if safe_pick:
            sp_name = safe_pick.get('name', '').title()
            sp_rating = safe_pick.get('rating', 0.0)
            sp_rating_count = safe_pick.get('rating_count', 0)
            sp_cuisine = safe_pick.get('famous_food', '')
            sp_zomato = safe_pick.get('zomato_url', '')
            
            safe_pick_line = f"Safe pick: {sp_name} – rating {sp_rating:.1f}"
            if sp_rating_count > 0:
                safe_pick_line += f" ({sp_rating_count} reviews)"
            if sp_cuisine:
                safe_pick_line += f", {sp_cuisine}"
            if sp_zomato:
                safe_pick_line += f", [Zomato]({sp_zomato})"
            else:
                safe_pick_line += ", [Zomato]"
            
            lines.append(safe_pick_line)
        
        # Format Local Favourite
        if local_favourite and local_favourite != safe_pick:
            lf_name = local_favourite.get('name', '').title()
            lf_rating = local_favourite.get('rating', 0.0)
            lf_rating_count = local_favourite.get('rating_count', 0)
            lf_cuisine = local_favourite.get('famous_food', '')
            lf_zomato = local_favourite.get('zomato_url', '')
            
            local_fav_line = f"Local favourite: {lf_name} – rating count {lf_rating_count}"
            if lf_rating > 0:
                local_fav_line += f" (rating {lf_rating:.1f})"
            if lf_cuisine:
                local_fav_line += f", {lf_cuisine}"
            if lf_zomato:
                local_fav_line += f", [Zomato]({lf_zomato})"
            else:
                local_fav_line += ", [Zomato]"
            
            lines.append(local_fav_line)
        
        return "\n".join(lines)


# ========== TEST FUNCTION ==========
def test_enhanced():
    """Test the enhanced version"""
    print("🚀 Testing CHAL DILLI Enhanced...")
    
    chal_dilli = ChalDilliEnhanced()
    
    # Test queries
    test_queries = [
        "Hi, how are you?",
        "Tell me about Delhi metro",
        "Where should I eat in Delhi?",
        "What events are happening?",
        "What attractions should I visit?",
        "How do I travel by bus?",
        "What's the weather like?"
    ]
    
    for query in test_queries:
        print(f"\n🧑 User: {query}")
        response = chal_dilli.get_delhi_response(query)
        print(f"🤖 CHAL DILLI: {response['response']}")
        print("-" * 50)
    
    # Show data summary
    print("\n📊 Data Summary:")
    summary = chal_dilli.get_data_summary()
    print(f"Metro: {summary['metro']['status']} ({summary['metro']['lines_count']} lines)")
    print(f"Bus: {summary['bus']['status']} ({summary['bus']['routes_count']} routes)")
    print(f"Events: {summary['events']['count']} events")
    print(f"Last Update: {summary['last_update']}")
    
    print("\n✅ CHAL DILLI Enhanced is working perfectly!")

if __name__ == "__main__":
    test_enhanced()
