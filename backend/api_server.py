#!/usr/bin/env python3
"""
CHAL DILLI - FastAPI Server
Backend API for Delhi's Smart AI Assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path for imports
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Import ParseBot helpers so we can expose the same endpoint on this main app
try:
    from parsebot_from_url import fetch_full_html, call_parsebot, UrlPayload
    PARSEBOT_AVAILABLE = True
    print("✅ ParseBot non-technical events integration loaded")
except Exception as e:
    PARSEBOT_AVAILABLE = False
    print(f"⚠️ ParseBot integration unavailable: {e}")
    print("   Note: Install playwright with 'pip install playwright && playwright install chromium' to enable non-technical events")

try:
    from parsebot_technical_events import (
        TechnicalEventsPayload,
        call_technical_events_parsebot,
    )
    PARSEBOT_TECH_AVAILABLE = True
except Exception as e:
    PARSEBOT_TECH_AVAILABLE = False
    print(f"⚠️ Technical events ParseBot integration unavailable: {e}")

# ========== FASTAPI APP ==========
from contextlib import asynccontextmanager

# Global instance - will be initialized in background
chal_dilli = None

# Lifespan context manager - ensures server starts immediately
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - starts background tasks immediately"""
    # Start initialization BEFORE yield (during startup) but don't await it
    print("=" * 60)
    print("🚀 Server starting, creating background initialization task...")
    print("=" * 60)
    # Create task but don't await - it runs in background
    task = asyncio.create_task(initialize_chal_dilli_background())
    print(f"✅ Background task created: {task}")
    # Yield immediately - server is ready, Render can detect port
    # Initialization continues in background
    yield
    # Cleanup if needed (runs during shutdown)
    pass

# Create app with lifespan
app = FastAPI(
    title="CHAL DILLI API",
    description="Delhi's Smart Big Brother AI Assistant with Real-time Data",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_chal_dilli_background():
    """Initialize CHAL DILLI in background - non-blocking"""
    global chal_dilli
    import time
    start_time = time.time()
    try:
        print("=" * 60)
        print("🔄 Starting CHAL DILLI initialization...")
        print("=" * 60)
        
        from chal_dilli_enhanced import ChalDilliEnhanced
        print("✅ Import successful")
        
        print("🔄 Creating ChalDilliEnhanced instance...")
        # Run initialization in thread pool to avoid blocking event loop
        chal_dilli = await asyncio.to_thread(ChalDilliEnhanced)
        
        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"✅ CHAL DILLI Enhanced initialized successfully in {elapsed:.2f}s")
        print("=" * 60)
        
        # Update data in background task (non-blocking)
        print("🔄 Starting background data update...")
        asyncio.create_task(update_data_background())
    except ImportError as e:
        print("=" * 60)
        print(f"❌ IMPORT ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        chal_dilli = None
    except Exception as e:
        print("=" * 60)
        print(f"❌ INITIALIZATION ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("=" * 60)
        chal_dilli = None

async def update_data_background():
    """Background task to update data after startup"""
    await asyncio.sleep(2)  # Wait 2 seconds for server to be ready
    if chal_dilli:
        try:
            print("=" * 60)
            print("🔄 Starting scraper data update...")
            print("=" * 60)
            # Run update_data in thread pool to avoid blocking
            await asyncio.to_thread(chal_dilli.update_data)
            print("=" * 60)
            print("✅ Background data update completed successfully!")
            print("=" * 60)
        except Exception as e:
            print("=" * 60)
            print(f"❌ Background data update failed: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            print("=" * 60)

# ========== PYDANTIC MODELS ==========
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    query: str
    timestamp: str
    metro_status: str
    language: str
    data_freshness: str
    recommendations: Optional[Dict[str, Any]] = None  # Structured recommendations for food queries

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str


# ========== PARSEBOT / BOOKMYSHOW EVENTS ENDPOINT ==========
if PARSEBOT_AVAILABLE:

    @app.post("/api/parse-events-from-url")
    async def parse_events_from_url(payload: UrlPayload):
        """
        Proxy endpoint: fetch fully rendered HTML via Playwright and send to Parse.bot.
        This mirrors the standalone parsebot_from_url.py behaviour but runs on the main app.
        """
        try:
            # Step 1: Fetch fully rendered HTML in a worker thread so sync Playwright
            # does not run directly inside the main asyncio event loop.
            html = await asyncio.to_thread(fetch_full_html, payload.url)
            # Step 2: Send HTML to Parse.bot and return result (also in thread to handle sync HTTPException)
            result = await asyncio.to_thread(call_parsebot, html, bool(payload.debug))
            return result
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            # Catch any other exceptions and convert to HTTPException
            raise HTTPException(
                status_code=500,
                detail=f"Error processing non-technical events: {str(e)}"
            )

if PARSEBOT_TECH_AVAILABLE:

    @app.post("/api/parse-technical-events")
    async def parse_technical_events(payload: TechnicalEventsPayload):
        """
        Technical events / hackathons endpoint powered by ParseBot (no Playwright needed).
        """
        try:
            # Run in thread pool to avoid blocking and handle sync HTTPException properly
            result = await asyncio.to_thread(call_technical_events_parsebot, payload.page_url)
            return result
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            # Catch any other exceptions and convert to HTTPException
            raise HTTPException(
                status_code=500,
                detail=f"Error processing technical events: {str(e)}"
            )

# ========== API ENDPOINTS ==========
@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """Main chat endpoint for CHAL DILLI - non-blocking"""
    try:
        if chal_dilli is None:
            # Fallback response if initialization failed
            return QueryResponse(
                response="Sorry bhai, system abhi initialize ho raha hai. Thoda wait karo ya phir try karo!",
                query=request.query,
                timestamp=datetime.now().isoformat(),
                metro_status="Initializing",
                language="hinglish",
                data_freshness=datetime.now().isoformat()
            )
        
        # Run get_delhi_response in thread pool with timeout to avoid blocking
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(chal_dilli.get_delhi_response, request.query),
                timeout=10.0  # 10 second timeout
            )
        except asyncio.TimeoutError:
            return QueryResponse(
                response="Sorry bhai, response thoda slow aa raha hai. Please try again!",
                query=request.query,
                timestamp=datetime.now().isoformat(),
                metro_status="Timeout",
                language="hinglish",
                data_freshness=datetime.now().isoformat()
            )
        
        # Ensure response has all required fields
        if not isinstance(response, dict):
            response = {"response": str(response)}
        
        # Fill in missing fields
        response.setdefault("query", request.query)
        response.setdefault("timestamp", datetime.now().isoformat())
        response.setdefault("metro_status", chal_dilli.metro_data.get("status", "All lines operational"))
        response.setdefault("language", "hinglish")
        response.setdefault("data_freshness", datetime.now().isoformat())
        response.setdefault("recommendations", None)
        
        return QueryResponse(**response)
    except Exception as e:
        # Return error response instead of raising exception
        import traceback
        traceback.print_exc()
        return QueryResponse(
            response=f"Sorry bhai, error aaya: {str(e)}. Please try again!",
            query=request.query,
            timestamp=datetime.now().isoformat(),
            metro_status="Error",
            language="hinglish",
            data_freshness=datetime.now().isoformat()
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="CHAL DILLI Enhanced",
        timestamp=datetime.now().isoformat(),
        version="2.0.0"
    )

@app.get("/init-status")
async def init_status():
    """Check initialization status"""
    return {
        "initialized": chal_dilli is not None,
        "status": "ready" if chal_dilli else "initializing",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metro-status")
async def metro_status():
    """Get current metro status"""
    if chal_dilli is None:
        return {"status": "System initializing", "lines": {}}
    return {
        "status": chal_dilli.metro_data.get("status", "All lines operational"),
        "lines": chal_dilli.metro_data.get("lines", {})
    }

@app.get("/metro-routes")
async def metro_routes():
    """Get all metro routes and lines information"""
    if chal_dilli is None:
        return {
            "error": "System initializing",
            "lines": []
        }
    
    lines = chal_dilli.metro_data.get("lines", {})
    
    # Get all metro lines from GTFS if available
    all_routes = []
    if chal_dilli.enhanced_router and chal_dilli.enhanced_router.metro_router:
        try:
            # Get all routes from the router
            routes = chal_dilli.enhanced_router.metro_router.routes
            for route_id, route_info in routes.items():
                route_name = chal_dilli.enhanced_router.metro_router.route_display_name(route_id)
                all_routes.append({
                    "route_id": route_id,
                    "name": route_name or route_info.get("long_name", ""),
                    "short_name": route_info.get("short_name", ""),
                    "description": route_info.get("desc", "")
                })
        except Exception as e:
            print(f"Error getting routes: {e}")
    
    # Fallback to known Delhi Metro lines
    if not all_routes:
        all_routes = [
            {"name": "Red Line", "description": "Rithala to Shaheed Sthal (New Bus Adda)"},
            {"name": "Yellow Line", "description": "Samaypur Badli to HUDA City Centre"},
            {"name": "Blue Line", "description": "Dwarka Sector 21 to Noida Electronic City / Vaishali"},
            {"name": "Green Line", "description": "Inderlok to Brigadier Hoshiar Singh"},
            {"name": "Violet Line", "description": "Kashmere Gate to Raja Nahar Singh"},
            {"name": "Pink Line", "description": "Majlis Park to Shiv Vihar"},
            {"name": "Magenta Line", "description": "Janakpuri West to Botanical Garden"},
            {"name": "Grey Line", "description": "Dwarka to Najafgarh"},
            {"name": "Airport Express Line", "description": "New Delhi to Dwarka Sector 21"}
        ]
    
    return {
        "status": chal_dilli.metro_data.get("status", "All lines operational"),
        "total_lines": len(all_routes),
        "lines": lines,
        "all_routes": all_routes
    }

@app.get("/delhi-info")
async def delhi_info():
    """Get Delhi information"""
    if chal_dilli is None:
        return {
            "metro_lines": 9,
            "food_areas": 0,
            "attractions": 6,
            "bus_routes": 0,
            "events_count": 0,
            "service": "CHAL DILLI Enhanced - Delhi's Smart AI Assistant",
            "data_freshness": "System initializing"
        }
    summary = chal_dilli.get_data_summary()
    return {
        "metro_lines": summary.get("metro", {}).get("lines_count", 9),
        "food_areas": 4,
        "attractions": 6,
        "bus_routes": summary.get("bus", {}).get("routes_count", 0),
        "events_count": summary.get("events", {}).get("count", 0),
        "service": "CHAL DILLI Enhanced - Delhi's Smart AI Assistant",
        "data_freshness": summary.get("last_update", "Unknown")
    }

@app.get("/data-summary")
async def data_summary():
    """Get detailed data summary"""
    if chal_dilli is None:
        return {
            "metro": {"status": "System initializing", "lines_count": 9},
            "bus": {"status": "Unknown", "routes_count": 0},
            "events": {"count": 0},
            "last_update": "System initializing"
        }
    return chal_dilli.get_data_summary()

@app.post("/update-data")
async def update_data():
    """Manually trigger data update"""
    try:
        chal_dilli.update_data()
        return {"status": "success", "message": "Data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    endpoints = {
        "chat": "/chat",
        "health": "/health",
        "metro_status": "/metro-status",
        "metro_routes": "/metro-routes",
        "delhi_info": "/delhi-info",
        "data_summary": "/data-summary",
        "update_data": "/update-data"
    }
    
    # Add ParseBot endpoints if available
    if PARSEBOT_AVAILABLE:
        endpoints["parse_events_from_url"] = "/api/parse-events-from-url"
    if PARSEBOT_TECH_AVAILABLE:
        endpoints["parse_technical_events"] = "/api/parse-technical-events"
    
    return {
        "message": "CHAL DILLI - Delhi's Smart AI Assistant",
        "version": "2.0.0",
        "features": [
            "Real-time Metro Data",
            "DTC Bus Information", 
            "Delhi Events",
            "Food Recommendations",
            "Tourist Attractions"
        ],
        "endpoints": endpoints,
        "parsebot_status": {
            "non_tech_available": PARSEBOT_AVAILABLE,
            "tech_available": PARSEBOT_TECH_AVAILABLE
        }
    }

# ========== RUN SERVER ==========
# Note: Server should be started with: uvicorn backend.api_server:app --host 0.0.0.0 --port $PORT
# DO NOT use uvicorn.run() here - it blocks and prevents proper deployment
