"""
OpenStreetMap utilities for food recommender.
Uses free public APIs: Nominatim for geocoding and Overpass for POI queries.
"""

import time
from typing import Dict, List, Optional

import requests

# Rate limiting: Nominatim requires max 1 request per second
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 1.0

def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode coordinates to get area/suburb name using Nominatim.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
    
    Returns:
        Area or suburb name if available, None if request fails
    """
    global _last_request_time
    
    # Rate limiting: wait if needed
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    if time_since_last < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - time_since_last)
    
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": "chal-dilli-app"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        _last_request_time = time.time()
        
        # Extract area or suburb from address components
        address = data.get("address", {})
        
        # Try different keys in order of preference
        area = (
            address.get("suburb") or
            address.get("neighbourhood") or
            address.get("city_district") or
            address.get("quarter") or
            address.get("village") or
            address.get("town")
        )
        
        if area:
            return area.strip()
        
        return None
        
    except (requests.RequestException, KeyError, ValueError) as e:
        return None

def fetch_osm_nearby_restaurants(lat: float, lon: float, radius_m: int = 800) -> List[Dict]:
    """
    Fetch nearby restaurants from OpenStreetMap using Overpass API.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 800)
    
    Returns:
        List of dictionaries with 'name', 'lat', 'lon', 'tags' keys
        Returns empty list if API fails
    """
    # Overpass QL query to find restaurants within radius
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"restaurant|cafe|fast_food|food_court"]["name"](around:{radius_m},{lat},{lon});
      way["amenity"~"restaurant|cafe|fast_food|food_court"]["name"](around:{radius_m},{lat},{lon});
      relation["amenity"~"restaurant|cafe|fast_food|food_court"]["name"](around:{radius_m},{lat},{lon});
    );
    out center meta;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    
    try:
        response = requests.post(url, data=query, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            
            if not name:
                continue
            
            # Get coordinates
            if element.get("type") == "node":
                elem_lat = element.get("lat")
                elem_lon = element.get("lon")
            else:
                # For ways and relations, use center if available
                center = element.get("center", {})
                elem_lat = center.get("lat")
                elem_lon = center.get("lon")
            
            if elem_lat is None or elem_lon is None:
                continue
            
            results.append({
                "name": name,
                "lat": float(elem_lat),
                "lon": float(elem_lon),
                "tags": tags
            })
        
        return results
        
    except (requests.RequestException, KeyError, ValueError) as e:
        return []

