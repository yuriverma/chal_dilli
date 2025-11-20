#!/usr/bin/env python3
"""
CHAL DILLI - FastAPI Server
Backend API for Delhi's Smart AI Assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from chal_dilli_enhanced import ChalDilliEnhanced
import uvicorn
from datetime import datetime

# ========== FASTAPI APP ==========
app = FastAPI(
    title="CHAL DILLI API",
    description="Delhi's Smart Big Brother AI Assistant with Real-time Data",
    version="2.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CHAL DILLI Enhanced with error handling
try:
    chal_dilli = ChalDilliEnhanced()
    print("✅ CHAL DILLI Enhanced initialized successfully")
except Exception as e:
    print(f"⚠️ Warning: Error initializing CHAL DILLI: {e}")
    chal_dilli = None

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

# ========== API ENDPOINTS ==========
@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """Main chat endpoint for CHAL DILLI"""
    try:
        if chal_dilli is None:
            # Fallback response if initialization failed
            return QueryResponse(
                response="Sorry bhai, system thoda busy hai. Please try again in a moment!",
                query=request.query,
                timestamp=datetime.now().isoformat(),
                metro_status="Unknown",
                language="hinglish",
                data_freshness=datetime.now().isoformat()
            )
        
        response = chal_dilli.get_delhi_response(request.query)
        
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
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "metro_status": "/metro-status",
            "metro_routes": "/metro-routes",
            "delhi_info": "/delhi-info",
            "data_summary": "/data-summary",
            "update_data": "/update-data"
        }
    }

# ========== RUN SERVER ==========
if __name__ == "__main__":
    print("🚀 Starting CHAL DILLI Enhanced API Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("🔄 Real-time data integration: ACTIVE")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
