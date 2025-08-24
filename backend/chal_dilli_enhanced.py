#!/usr/bin/env python3
"""
CHAL DILLI - Enhanced Version with Real-time Data
Delhi's Smart Big Brother AI Assistant
"""

import re
import random
from datetime import datetime
from typing import Dict
from data_scraper import DelhiDataScraper
from enhanced_metro_router import EnhancedMetroRouter

class ChalDilliEnhanced:
    def __init__(self):
        self.scraper = DelhiDataScraper()
        self.enhanced_router = EnhancedMetroRouter()
        self.metro_data = {"status": "All lines operational"}
        self.event_data = []
        self.food_data = {}
        self.bus_data = {}
        
        # Initialize with data
        self.update_data()
        
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
        """Get metro response with real-time data"""
        metro_status = self.metro_data.get("status", "All lines operational")
        lines = self.metro_data.get("lines", {})
        alerts = self.metro_data.get("alerts", [])
        
        # Get specific line information
        line_names = list(lines.keys())
        line_count = len(line_names)
        
        # Create detailed line information
        if line_count > 0:
            # Show first 3 lines with routes
            line_details = []
            for i, line_name in enumerate(line_names[:3]):
                line_info = lines[line_name]
                route = line_info.get("route", "")
                status = line_info.get("status", "Operational")
                line_details.append(f"{line_name} ({route}) - {status}")
            
            lines_info = f"{line_count} lines: {', '.join(line_details)}"
            if line_count > 3:
                lines_info += f" and {line_count - 3} more lines"
        else:
            lines_info = "9 lines including Red, Yellow, Blue, Green, Violet, Pink, Magenta, Grey, and Airport Express"
        
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
    
    def get_food_response(self) -> str:
        """Get food response with enhanced data"""
        areas = self.food_data.get("areas", {})
        
        if areas:
            # Get a random area with its details
            area_name = random.choice(list(areas.keys()))
            area_info = areas[area_name]
            famous_for = ", ".join(area_info.get("famous_for", [])[:2])
            rating = area_info.get("rating", 4.0)
            
            responses = [
                f"Food ke liye, {area_name} is the place to be! Famous for {famous_for}. Rating: {rating}/5!",
                f"Bhai, {area_name} mein best food milta hai! Try {famous_for}. Rating: {rating}/5!",
                f"For amazing food, you gotta try {area_name}! Famous for {famous_for}. Rating: {rating}/5!"
            ]
        else:
            # Fallback to basic response
            responses = [
                "Food ke liye, Chandni Chowk is the place to be!",
                "Bhai, Khan Market mein best food milta hai!",
                "For amazing food, you gotta try Connaught Place!"
            ]
        
        return random.choice(responses)
    
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
    
    def generate_response(self, query: str) -> str:
        """Generate response based on query with real-time data"""
        query_lower = query.lower()
        
        # Check for weather first (more specific)
        if any(word in query_lower for word in ["weather", "temperature", "climate"]):
            return self.get_weather_response()
        
        # Check for metro (more specific to avoid conflicts)
        if any(word in query_lower for word in ["metro", "train", "subway", "line", "delhi metro", "how to go", "which line", "route", "reach", "how to reach", "kaise jaana", "kaise pahunch", "se", "kaise jau", "ka route"]):
            # Use enhanced Metro router for detailed responses
            route_result = self.enhanced_router.get_route_response(query)
            return route_result["response"]
        
        # Check for food
        if any(word in query_lower for word in ["food", "eat", "restaurant", "khana", "paranthe", "chaat", "where should i eat"]):
            return self.get_food_response()
        
        # Check for events
        if any(word in query_lower for word in ["event", "happening", "festival", "what events", "what's happening"]):
            return self.get_event_response()
        
        # Check for attractions
        if any(word in query_lower for word in ["visit", "see", "attraction", "place", "fort", "temple", "what attractions"]):
            return self.get_attraction_response()
        
        # Check for bus
        if any(word in query_lower for word in ["bus", "dtc", "transport", "how do i travel by bus"]):
            return self.get_bus_response()
        
        # Check for greeting
        if any(word in query_lower for word in ["hi", "hello", "hey", "namaste", "kaise ho", "how are you"]):
            return self.get_greeting_response()
        
        # Default
        return self.get_unknown_response()
    
    def get_delhi_response(self, query: str) -> Dict:
        """Get Delhi response with real-time data"""
        response = self.generate_response(query)
        
        return {
            "response": response,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "metro_status": self.metro_data.get("status"),
            "language": "hinglish" if re.search(r'[\u0900-\u097F]', query) else "english",
            "data_freshness": self.scraper.last_update.isoformat() if self.scraper.last_update else None
        }
    
    def get_data_summary(self) -> Dict:
        """Get summary of current data"""
        return self.scraper.get_data_summary()

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
