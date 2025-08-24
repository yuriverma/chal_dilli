#!/usr/bin/env python3
"""
Enhanced Metro Router for CHAL DILLI
Integrates real GTFS data with language detection and nearby recommendations
"""

import re
from typing import Dict, List, Optional, Tuple
from metro_router import MetroRouter
import os

class EnhancedMetroRouter:
    def __init__(self, gtfs_dir: str = "../data/DMRC_GTFS (1)"):
        """Initialize with GTFS data directory"""
        self.gtfs_dir = gtfs_dir
        self.metro_router = None
        self._load_router()
        
        # Language detection patterns
        self.hindi_patterns = [
            r'[\u0900-\u097F]',  # Devanagari script
            r'\b(jaana|jao|jaiye|pahunch|pahuchna|station|stn|metro|line|route)\b',
            r'\b(kahan|kaise|kya|kaun|kis|kisne|kisko|kiski|kiski|kisne)\b',
            r'\b(mein|se|ko|ka|ki|ke|par|pe|se|tak|aur|ya|phir|fir)\b'
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
            if os.path.exists(self.gtfs_dir):
                self.metro_router = MetroRouter(self.gtfs_dir)
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
    
    def extract_route_query(self, query: str) -> Optional[Dict]:
        """Extract source and destination from query"""
        query_lower = query.lower()
        
        # Common route patterns
        route_patterns = [
            r'(?:from|se)\s+([^?]+?)\s+(?:to|tak)\s+([^?]+)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:kaise|how)\s+(?:jaana|go|reach|pahunch|jau|jaiye)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:ka|kya)\s+(?:route|line|metro)',
            r'(?:how to|kaise|kahan se|kahan tak|route|way|path)\s+(?:go|jaana|jao|jaiye|reach|pahunch)\s+(?:to|tak|mein)\s+([^?]+)',
            r'(?:which|kaun|kis)\s+(?:line|metro|route)\s+(?:goes|leads|connects)\s+(?:to|tak)\s+([^?]+)',
            r'([^to]+?)\s+(?:to|tak)\s+([^?]+)',
            r'(?:how|kaise)\s+(?:to|tak)\s+([^?]+)',
            r'([^?]+)\s+(?:kaise|how)\s+(?:jaana|go|reach|pahunch|jau|jaiye)',
            r'([^?]+)\s+(?:ke liye|for)\s+(?:kaun|which)\s+(?:line|route)',
            r'([^?]+?)\s+(?:se|from)\s+([^?]+?)\s+(?:kaise|how)\s+(?:jaana|go|reach|pahunch|jau|jaiye)\s+(?:hai|hoga)'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if len(matches[0]) == 2:  # from X to Y
                    return {"from": matches[0][0].strip(), "to": matches[0][1].strip()}
                else:  # just destination
                    dest = matches[0].strip()
                    # Try to find a common source
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
                route_result = self.metro_router.human_route(
                    route_info["from"], 
                    route_info["to"]
                )
                
                if "error" in route_result:
                    return self._get_fallback_route_response(route_info, language)
                
                return self._format_route_response(route_result, language)
                
            except Exception as e:
                print(f"Error in Metro routing: {e}")
                return self._get_fallback_route_response(route_info, language)
        else:
            return self._get_fallback_route_response(route_info, language)
    
    def _format_route_response(self, route_result: Dict, language: str) -> Dict:
        """Format route response in the specified language"""
        if language == "hindi":
            response = f"Bhai, {route_result['from']} se {route_result['to']} tak ka best route:\n"
            response += f"Distance: {route_result['distance_km']} km\n"
            response += f"Fare: ₹{route_result['estimated_fare']} (Smart Card se ₹{int(route_result['estimated_fare'] * 0.9)})\n\n"
            
            for i, segment in enumerate(route_result['segments'], 1):
                response += f"{i}. {segment['line']} le sakte ho\n"
                response += f"   Board: {segment['from']}\n"
                response += f"   Alight: {segment['to']}\n\n"
            
            response += "Nearby recommendations add karne wale hain! 🍕🎉"
            
        elif language == "hinglish":
            response = f"Bhai, {route_result['from']} se {route_result['to']} tak ka route:\n"
            response += f"Distance: {route_result['distance_km']} km\n"
            response += f"Fare: ₹{route_result['estimated_fare']} (Smart Card discount available)\n\n"
            
            for i, segment in enumerate(route_result['segments'], 1):
                response += f"{i}. {segment['line']} le sakte ho\n"
                response += f"   Board: {segment['from']}\n"
                response += f"   Alight: {segment['to']}\n\n"
            
            response += "Coming soon: Nearby food and events! 🍕🎉"
            
        else:  # english
            response = f"Best route from {route_result['from']} to {route_result['to']}:\n"
            response += f"Distance: {route_result['distance_km']} km\n"
            response += f"Fare: ₹{route_result['estimated_fare']} (₹{int(route_result['estimated_fare'] * 0.9)} with Smart Card)\n\n"
            
            for i, segment in enumerate(route_result['segments'], 1):
                response += f"{i}. Take {segment['line']}\n"
                response += f"   Board at: {segment['from']}\n"
                response += f"   Alight at: {segment['to']}\n\n"
            
            response += "Coming soon: Nearby food and events recommendations! 🍕🎉"
        
        return {
            "response": response,
            "route_data": route_result,
            "language": language,
            "has_route": True
        }
    
    def _get_fallback_route_response(self, route_info: Dict, language: str) -> Dict:
        """Get fallback route response when GTFS data is not available"""
        dest = route_info["to"]
        
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
                response += "Coming soon: Nearby food and events! 🍕🎉"
                
            else:  # english
                response = f"Route to {dest.title()}:\n"
                response += f"Type: {dest_info['type']}\n"
                response += "Exact route calculation coming soon!\n"
                response += "Coming soon: Nearby food and events recommendations! 🍕🎉"
            
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
        "How to go to Connaught Place?",
        "Connaught Place kaise jaana hai?",
        "Which line goes to Qutub Minar?",
        "Qutub Minar ke liye kaun si line?",
        "From Dwarka to Airport",
        "Dwarka se Airport kaise jaana hai?"
    ]
    
    for query in test_queries:
        print(f"\n🧑 User: {query}")
        result = router.get_route_response(query)
        print(f"🤖 CHAL DILLI: {result['response']}")
        print(f"Language: {result['language']}")
        print(f"Has Route: {result['has_route']}")

if __name__ == "__main__":
    test_enhanced_router()
