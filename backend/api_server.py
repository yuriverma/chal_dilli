#!/usr/bin/env python3
"""
CHAL DILLI - FastAPI Server
Backend API for Delhi's Smart AI Assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Initialize CHAL DILLI Enhanced
chal_dilli = ChalDilliEnhanced()

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
        response = chal_dilli.get_delhi_response(request.query)
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    return {"status": chal_dilli.metro_data.get("status")}

@app.get("/delhi-info")
async def delhi_info():
    """Get Delhi information"""
    summary = chal_dilli.get_data_summary()
    return {
        "metro_lines": summary["metro"]["lines_count"],
        "food_areas": 4,
        "attractions": 6,
        "bus_routes": summary["bus"]["routes_count"],
        "events_count": summary["events"]["count"],
        "service": "CHAL DILLI Enhanced - Delhi's Smart AI Assistant",
        "data_freshness": summary["last_update"]
    }

@app.get("/data-summary")
async def data_summary():
    """Get detailed data summary"""
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
