
"""
Delhi Metro API Server
Combines route planning and real-time status scraping into a single FastAPI server
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
import os
import csv
import math
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== UTILITY FUNCTIONS ==================

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def norm(s: str) -> str:
    s = s.lower().strip()
    for token in [" metro station", " metro stn", " station", " (delhi)", "(delhi)"]:
        s = s.replace(token, "")
    s = s.replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    return s

def token_set(s: str) -> set:
    return set([t for t in norm(s).split() if t])

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

# ================== PYDANTIC MODELS ==================

class RouteRequest(BaseModel):
    from_station: str
    to_station: str
    smart_card: Optional[bool] = True

class RouteResponse(BaseModel):
    from_station: str
    to_station: str
    distance_km: float
    estimated_fare: int
    smart_card: bool
    segments: List[Dict]
    human_text: str

class MetroStatus(BaseModel):
    status: str
    alerts: List[str]
    last_updated: str
    websites_scraped: int
    operational_websites: int
    lines: Dict[str, Any]

# ================== METRO ROUTER CLASS ==================

class MetroRouter:
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir
        self._load()

    def _load(self):
        stops_path = os.path.join(self.gtfs_dir, "stops.txt")
        routes_path = os.path.join(self.gtfs_dir, "routes.txt")
        trips_path = os.path.join(self.gtfs_dir, "trips.txt")
        stop_times_path = os.path.join(self.gtfs_dir, "stop_times.txt")

        # Load stops
        self.stops = {}
        self.name_to_stop_ids = defaultdict(list)
        with open(stops_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["stop_id"]
                name = r["stop_name"]
                lat = float(r["stop_lat"]); lon = float(r["stop_lon"])
                self.stops[sid] = {"name": name, "lat": lat, "lon": lon}
                self.name_to_stop_ids[norm(name)].append(sid)

        # Load routes
        self.routes = {}
        with open(routes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rid = r["route_id"]
                self.routes[rid] = {
                    "short_name": r.get("route_short_name") or "",
                    "long_name": r.get("route_long_name") or "",
                    "desc": r.get("route_desc") or "",
                    "type": r.get("route_type") or "",
                }

        # Trips -> route_id
        self.trip_route = {}
        with open(trips_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.trip_route[r["trip_id"]] = r["route_id"]

        # Trip stop sequences
        self.trip_stops = defaultdict(list)
        with open(stop_times_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                tid = r["trip_id"]; sid = r["stop_id"]; seq = int(r["stop_sequence"])
                self.trip_stops[tid].append((seq, sid))
        for tid in list(self.trip_stops.keys()):
            self.trip_stops[tid].sort()

        # Build edges
        self.edge_weight = {}
        self.edge_route_counter = defaultdict(Counter)
        for trip_id, seqs in self.trip_stops.items():
            r_id = self.trip_route[trip_id]
            for i in range(len(seqs)-1):
                a = seqs[i][1]; b = seqs[i+1][1]
                if a == b or a not in self.stops or b not in self.stops: continue
                u, v = (a, b) if a < b else (b, a)
                d = haversine_km(self.stops[u]["lat"], self.stops[u]["lon"],
                                 self.stops[v]["lat"], self.stops[v]["lon"])
                if (u, v) not in self.edge_weight or d < self.edge_weight[(u, v)]:
                    self.edge_weight[(u, v)] = d
                self.edge_route_counter[(u, v)][r_id] += 1

        # adjacency & main route per edge
        self.adj = defaultdict(list)
        self.edge_route_main = {}
        for (u, v), w in self.edge_weight.items():
            self.adj[u].append((v, w)); self.adj[v].append((u, w))
            rid = self.edge_route_counter[(u, v)].most_common(1)[0][0]
            self.edge_route_main[(u, v)] = rid

    def route_display_name(self, route_id: str) -> str:
        r = self.routes.get(route_id, {})
        for key in ["long_name", "short_name", "desc"]:
            if r.get(key): return r[key]
        return route_id

    def find_best_station_id(self, query: str) -> Optional[str]:
        n = norm(query)
        if n in self.name_to_stop_ids:
            return self.name_to_stop_ids[n][0]
        q_tokens = token_set(query)
        best_sid, best_score = None, 0.0
        for sid, info in self.stops.items():
            score = jaccard(q_tokens, token_set(info["name"]))
            if score > best_score:
                best_sid, best_score = sid, score
        return best_sid if best_score >= 0.34 else None

    def edge_key(self, u: str, v: str):
        return (u, v) if u < v else (v, u)

    def dijkstra(self, src: str, dst: str):
        import heapq
        INF = 1e18
        dist = defaultdict(lambda: INF); parent = {}
        dist[src] = 0.0; pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]: continue
            if u == dst: break
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd; parent[v] = u
                    heapq.heappush(pq, (nd, v))
        if dist[dst] == INF:
            return (INF, [])
        path = [dst]
        while path[-1] != src:
            path.append(parent[path[-1]])
        path.reverse()
        return (dist[dst], path)

    def path_segments(self, path: List[str]):
        if len(path) < 2: return []
        segs = []
        cur_route = None; cur_start = path[0]; cur_stops = [path[0]]
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            r_id = self.edge_route_main.get(self.edge_key(u, v))
            if cur_route is None: cur_route = r_id
            if r_id != cur_route:
                segs.append({"route_id": cur_route, "from": cur_start, "to": path[i], "stops": cur_stops[:]})
                cur_route = r_id; cur_start = path[i]; cur_stops = [path[i]]
            cur_stops.append(v)
        segs.append({"route_id": cur_route, "from": cur_start, "to": path[-1], "stops": cur_stops[:]})
        return segs

    def path_uses_airport_express(self, segs):
        for s in segs:
            name = self.route_display_name(s["route_id"]).lower()
            if "airport" in name:
                return True
        return False

    def estimate_fare(self, distance_km: float, uses_airport_express: bool, smart_card: bool=True) -> int:
        FARE_SLABS = [(2,10),(5,20),(12,30),(21,40),(32,50),(10**9,60)]
        base = 60
        for limit, fare in FARE_SLABS:
            if distance_km <= limit:
                base = fare; break
        if uses_airport_express and base < 70:
            base = max(base, 70)
        if smart_card:
            base = int((base * 0.9)//1)
        return int(base)

    def human_route(self, src_name: str, dst_name: str, smart_card: bool=True):
        src_id = self.find_best_station_id(src_name)
        dst_id = self.find_best_station_id(dst_name)
        if not src_id: return {"error": f"Couldn't find station matching '{src_name}'"}
        if not dst_id: return {"error": f"Couldn't find station matching '{dst_name}'"}
        if src_id == dst_id: return {"message": f"You're already at {self.stops[src_id]['name']} 😄"}
        total_km, path = self.dijkstra(src_id, dst_id)
        if not path: return {"error":"No route found between the stations."}
        segs = self.path_segments(path)
        uses_ael = self.path_uses_airport_express(segs)
        est_fare = self.estimate_fare(total_km, uses_ael, smart_card=smart_card)

        lines = [f"Best route ({total_km:.1f} km • est. fare ₹{est_fare}{' with Smart Card' if smart_card else ''}):"]
        for idx, s in enumerate(segs, start=1):
            rname = self.route_display_name(s["route_id"]) or "Metro Line"
            start_name = self.stops[s["from"]]["name"]; end_name = self.stops[s["to"]]["name"]
            hop_count = len(s["stops"])-1
            if idx == 1:
                lines.append(f"{idx}. Board {rname} at {start_name}, go {hop_count} stop(s) → alight at {end_name}.")
            else:
                lines.append(f"{idx}. Interchange at {start_name} → {rname}, ride {hop_count} stop(s) → {end_name}.")
        if uses_ael:
            lines.append("Note: Route uses Airport Express Line — fares may be higher (up to ~₹70).")

        return {
            "from": self.stops[src_id]["name"],
            "to": self.stops[dst_id]["name"],
            "distance_km": round(total_km,2),
            "estimated_fare": est_fare,
            "smart_card": smart_card,
            "segments": [{
                "line": self.route_display_name(s["route_id"]),
                "from": self.stops[s["from"]]["name"],
                "to": self.stops[s["to"]]["name"],
                "stops": [self.stops[x]["name"] for x in s["stops"]]
            } for s in segs],
            "human_text": "\n".join(lines)
        }

# ================== METRO SCRAPER CLASS ==================

class DelhiMetroScraper:
    def __init__(self):
        self.metro_urls = [
            "https://www.delhimetrorail.com/",
            "https://delhimetrorail.com/",
            "https://dmrc.org/"
        ]
        
        self.metro_lines = {
            "Red Line": {"route": "Dilshad Garden - Rithala", "stations": 21},
            "Yellow Line": {"route": "Samaypur Badli - HUDA City Centre", "stations": 37},
            "Blue Line": {"route": "Dwarka Sector 21 - Noida Electronic City", "stations": 50},
            "Green Line": {"route": "Inderlok - Brigadier Hoshiar Singh", "stations": 23},
            "Violet Line": {"route": "Kashmere Gate - Raja Nahar Singh", "stations": 16},
            "Pink Line": {"route": "Majlis Park - Shiv Vihar", "stations": 38},
            "Magenta Line": {"route": "Janakpuri West - Botanical Garden", "stations": 25},
            "Grey Line": {"route": "Dwarka - Dhansa Bus Stand", "stations": 9},
            "Airport Express": {"route": "New Delhi - Dwarka Sector 21", "stations": 6}
        }

    async def scrape_metro_website(self, session: aiohttp.ClientSession, url: str) -> dict:
        """Async scrape Delhi Metro official website"""
        try:
            logger.info(f"Scraping Delhi Metro website: {url}")
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                content = await response.text()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                status_info = {
                    "url": url,
                    "status_code": response.status,
                    "content_length": len(content),
                    "title": soup.title.string if soup.title else "No title found"
                }
                
                # Look for specific status indicators
                status_text = soup.get_text().lower()
                
                # Check for operational status keywords
                operational_keywords = ["operational", "running", "normal", "regular"]
                disruption_keywords = ["disruption", "delay", "maintenance", "closed", "suspended"]
                
                operational_count = sum(1 for keyword in operational_keywords if keyword in status_text)
                disruption_count = sum(1 for keyword in disruption_keywords if keyword in status_text)
                
                if disruption_count > operational_count:
                    status_info["overall_status"] = "Disruptions detected"
                else:
                    status_info["overall_status"] = "Operational"
                
                # Look for alerts or announcements
                alerts = []
                alert_selectors = [
                    '.alert', '.announcement', '.notice', '.status',
                    '[class*="alert"]', '[class*="notice"]', '[class*="status"]'
                ]
                
                for selector in alert_selectors:
                    alert_elements = soup.select(selector)
                    for element in alert_elements[:3]:
                        alert_text = element.get_text().strip()
                        if alert_text and len(alert_text) > 10:
                            alerts.append(alert_text)
                
                status_info["alerts"] = alerts[:5]
                return status_info
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"url": url, "error": str(e)}

    async def scrape_all_metro_sites(self) -> dict:
        """Async scrape all Delhi Metro websites"""
        logger.info("Scraping all Delhi Metro websites...")
        
        results = {}
        async with aiohttp.ClientSession(
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        ) as session:
            tasks = []
            for url in self.metro_urls:
                task = self.scrape_metro_website(session, url)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, response in enumerate(responses):
                url = self.metro_urls[i]
                if isinstance(response, Exception):
                    results[url] = {"error": str(response)}
                else:
                    results[url] = response
        
        return results

    async def get_metro_status(self) -> dict:
        """Get comprehensive Metro status"""
        logger.info("Getting Delhi Metro status...")
        
        # Scrape all websites
        website_results = await self.scrape_all_metro_sites()
        
        # Analyze results
        operational_sites = 0
        total_alerts = []
        overall_status = "Unknown"
        
        for url, result in website_results.items():
            if "error" not in result:
                operational_sites += 1
                if result.get("overall_status") == "Operational":
                    overall_status = "Operational"
                total_alerts.extend(result.get("alerts", []))
        
        # Determine overall status
        if operational_sites == 0:
            overall_status = "Data unavailable"
        elif overall_status == "Unknown":
            overall_status = "Operational"
        
        # Create comprehensive status
        metro_status = {
            "status": overall_status,
            "alerts": total_alerts[:10],
            "last_updated": datetime.now().isoformat(),
            "websites_scraped": len(website_results),
            "operational_websites": operational_sites,
            "lines": {}
        }
        
        # Add line information
        for line_name, line_info in self.metro_lines.items():
            metro_status["lines"][line_name] = {
                "status": "Operational",
                "route": line_info["route"],
                "stations": line_info["stations"],
                "last_checked": datetime.now().isoformat()
            }
        
        # Check for specific line disruptions in alerts
        for alert in total_alerts:
            alert_lower = alert.lower()
            for line_name in self.metro_lines.keys():
                if line_name.lower() in alert_lower:
                    if any(word in alert_lower for word in ["delay", "disruption", "maintenance", "closed"]):
                        metro_status["lines"][line_name]["status"] = "Disruption"
                        metro_status["lines"][line_name]["alert"] = alert
        
        logger.info(f"Metro status: {overall_status} with {len(total_alerts)} alerts")
        return metro_status

# ================== FASTAPI APPLICATION ==================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global router
    
    # Updated paths based on your actual folder structure
    possible_paths = [
        os.path.join(os.getcwd(), "data", "DMRC_GTFS"),  # Most likely path
        os.path.join(os.path.dirname(os.getcwd()), "data", "DMRC_GTFS"),  # If running from backend folder
        os.path.join(os.getcwd(), "DMRC_GTFS"),
        "./data/DMRC_GTFS",
        "../data/DMRC_GTFS",  # If running from backend subfolder
        "data/DMRC_GTFS",
        "DMRC_GTFS"
    ]
    
    gtfs_path = None
    
    # Check each possible path
    for path in possible_paths:
        if os.path.exists(path):
            # Check if it contains the required GTFS files
            required_files = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
            if all(os.path.exists(os.path.join(path, file)) for file in required_files):
                gtfs_path = path
                logger.info(f"🔍 Found GTFS data at: {path}")
                break
            else:
                logger.info(f"📁 Directory exists but missing GTFS files: {path}")
    
    if gtfs_path:
        try:
            router = MetroRouter(gtfs_path)
            logger.info(f"✅ MetroRouter initialized successfully with official DMRC data from: {gtfs_path}")
            logger.info(f"📊 Loaded {len(router.stops)} metro stations")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MetroRouter: {e}")
            logger.error(f"Error details: {str(e)}")
            router = None
    else:
        logger.error(f"❌ GTFS directory not found in any of these locations:")
        for path in possible_paths:
            logger.error(f"   - {path} (exists: {os.path.exists(path)})")
        
        # Show current directory contents
        logger.info(f"📂 Current directory: {os.getcwd()}")
        logger.info("📂 Current directory contents:")
        try:
            for item in os.listdir(os.getcwd()):
                item_path = os.path.join(os.getcwd(), item)
                if os.path.isdir(item_path):
                    logger.info(f"   📁 {item}/")
                else:
                    logger.info(f"   📄 {item}")
        except Exception as e:
            logger.error(f"Could not list directory contents: {e}")
        
        router = None
    
    yield  # Server runs here
    
    # Shutdown (cleanup if needed)
    pass

app = FastAPI(
    title="Delhi Metro API",
    description="API for Delhi Metro route planning and real-time status",
    version="1.0.0",
    lifespan=lifespan  
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
router = None
scraper = DelhiMetroScraper()

# Startup logic moved to lifespan function above

# ================== API ENDPOINTS ==================

@app.get("/")
async def root():
    return {
        "message": "Delhi Metro API",
        "version": "1.0.0",
        "endpoints": {
            "route": "/api/route",
            "status": "/api/status",
            "stations": "/api/stations",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "router": "available" if router else "unavailable",
            "scraper": "available"
        }
    }

@app.post("/api/route", response_model=Dict)
async def get_route(request: RouteRequest):
    """Get route between two metro stations"""
    if not router:
        raise HTTPException(status_code=503, detail="Route planning service unavailable. GTFS data not loaded.")
    
    try:
        result = router.human_route(
            request.from_station,
            request.to_station,
            request.smart_card
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        if "message" in result:
            return {"message": result["message"]}
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/status")
async def get_metro_status():
    """Get current Delhi Metro status"""
    try:
        status = await scraper.get_metro_status()
        return status
    except Exception as e:
        logger.error(f"Error getting metro status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/stations")
async def get_stations(search: Optional[str] = Query(None, description="Search for stations")):
    """Get list of metro stations, optionally filtered by search term"""
    if not router:
        raise HTTPException(status_code=503, detail="Route planning service unavailable. GTFS data not loaded.")
    
    try:
        stations = []
        for stop_id, stop_info in router.stops.items():
            if not search or search.lower() in stop_info["name"].lower():
                stations.append({
                    "id": stop_id,
                    "name": stop_info["name"],
                    "lat": stop_info["lat"],
                    "lon": stop_info["lon"]
                })
        
        # Limit results
        stations = stations[:50] if search else stations[:100]
        
        return {
            "stations": stations,
            "total": len(stations),
            "search": search
        }
    
    except Exception as e:
        logger.error(f"Error getting stations: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/lines")
async def get_metro_lines():
    """Get information about all metro lines"""
    return {
        "lines": scraper.metro_lines,
        "total_lines": len(scraper.metro_lines)
    }

# ================== MAIN ==================

if __name__ == "__main__":
    print("🚇 Starting Delhi Metro API Server...")
    uvicorn.run(
        "main:app",  # Change this to your filename if different
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )