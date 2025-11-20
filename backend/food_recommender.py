"""
Food Recommender System for Chal Delhi
Provides location-based restaurant recommendations using haversine distance.
"""

import pandas as pd
import numpy as np
import math
import os
import json
from typing import List, Dict, Optional, Tuple

# Import map utilities
try:
    from .maps_utils import reverse_geocode, fetch_osm_nearby_restaurants
except ImportError:
    # Handle case when running as script
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from maps_utils import reverse_geocode, fetch_osm_nearby_restaurants

# Constants
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'food_data.csv')
EARTH_RADIUS_KM = 6371.0
MIN_RADIUS_KM = 0.1
MAX_RADIUS_KM = 50.0

# Load and preprocess data once on import
def _load_and_preprocess_data():
    """Load CSV and preprocess data."""
    df = pd.read_csv(CSV_PATH)
    
    # Drop rows with missing name or city
    df = df.dropna(subset=['name', 'city'])
    
    # Parse rating as float, rating_count as int
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0.0)
    df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce').fillna(0).astype(int)
    
    # Normalize area and name to lowercase trimmed strings
    df['area'] = df['area'].astype(str).str.lower().str.strip()
    df['name'] = df['name'].astype(str).str.lower().str.strip()
    df['city'] = df['city'].astype(str).str.strip()
    
    # Keep rows with latitude and longitude when available
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Convert coordinates to float
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Ensure rating_count is int
    df['rating_count'] = df['rating_count'].astype(int)
    
    return df

# Load data on import
_df = _load_and_preprocess_data()

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in degrees
        lat2, lon2: Latitude and longitude of second point in degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_KM * c

def find_nearest(lat: float, lon: float, radius_km: float = 5, max_results: int = 50) -> List[Dict]:
    """
    Find restaurants within radius of given coordinates.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_km: Search radius in kilometers (clamped to 0.1-50)
        max_results: Maximum number of results to return
    
    Returns:
        List of dictionaries with restaurant data and computed distance
    """
    # Clamp radius
    radius_km = max(MIN_RADIUS_KM, min(MAX_RADIUS_KM, radius_km))
    
    results = []
    
    for _, row in _df.iterrows():
        try:
            distance = haversine_distance(lat, lon, row['latitude'], row['longitude'])
            
            if distance <= radius_km:
                result = {
                    'name': row['name'],
                    'area': row['area'],
                    'city': row['city'],
                    'rating': float(row['rating']) if pd.notna(row['rating']) else 0.0,
                    'rating_count': int(row['rating_count']) if pd.notna(row['rating_count']) else 0,
                    'cost_for_two': float(row['cost_for_two']) if pd.notna(row['cost_for_two']) else None,
                    'telephone': str(row['telephone']) if pd.notna(row['telephone']) and str(row['telephone']) != '#ERROR!' else None,
                    'address': str(row['address']) if pd.notna(row['address']) else None,
                    'famous_food': str(row['famous_food']) if pd.notna(row['famous_food']) else None,
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'distance_km': distance,
                    'source': 'csv',
                    'zomato_url': str(row['Zomato link']) if pd.notna(row.get('Zomato link')) and str(row.get('Zomato link', '')).strip() else None
                }
                results.append(result)
        except (ValueError, TypeError):
            continue
    
    # Sort by distance
    results.sort(key=lambda x: x['distance_km'])
    
    return results[:max_results]

def recommend_for_location(lat: float, lon: float, radius_km: float = 5) -> Dict:
    """
    Get two recommendations for a location: safe_pick and local_favourite.
    STRICT LOGIC: CSV is primary, OSM only if CSV has 0 results.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_km: Search radius in kilometers
    
    Returns:
        Dictionary with 'safe_pick' and 'local_favourite' recommendations
    """
    # Step 1: Filter CSV rows using haversine distance <= radius_km
    csv_candidates = find_nearest(lat, lon, radius_km, max_results=100)
    
    # Mark all CSV candidates with source='csv'
    for candidate in csv_candidates:
        candidate['source'] = 'csv'
    
    # Step 2: If results >= 3 → USE ONLY CSV
    if len(csv_candidates) >= 3:
        candidates = csv_candidates
    else:
        # Step 3: If results < 3 → reverse_geocode and filter CSV by area
        area_name_lower = None
        area_candidates = []
        
        area_name = reverse_geocode(lat, lon)
        if area_name:
            area_name_lower = area_name.lower().strip()
            # Filter CSV by area name
            for _, row in _df.iterrows():
                if pd.notna(row['area']) and str(row['area']).lower().strip() == area_name_lower:
                    try:
                        distance = haversine_distance(lat, lon, row['latitude'], row['longitude'])
                        # Only add if not already in csv_candidates (deduplicate)
                        existing_names = {c['name'].lower() for c in csv_candidates}
                        if row['name'].lower() not in existing_names:
                            result = {
                                'name': row['name'],
                                'area': row['area'],
                                'city': row['city'],
                                'rating': float(row['rating']) if pd.notna(row['rating']) else 0.0,
                                'rating_count': int(row['rating_count']) if pd.notna(row['rating_count']) else 0,
                                'cost_for_two': float(row['cost_for_two']) if pd.notna(row['cost_for_two']) else None,
                                'telephone': str(row['telephone']) if pd.notna(row['telephone']) and str(row['telephone']) != '#ERROR!' else None,
                                'address': str(row['address']) if pd.notna(row['address']) else None,
                                'famous_food': str(row['famous_food']) if pd.notna(row['famous_food']) else None,
                                'latitude': float(row['latitude']),
                                'longitude': float(row['longitude']),
                                'distance_km': distance,
                                'source': 'csv',
                                'zomato_url': str(row['Zomato link']) if pd.notna(row.get('Zomato link')) and str(row.get('Zomato link', '')).strip() else None
                            }
                            area_candidates.append(result)
                    except (ValueError, TypeError):
                        continue
        
        # Merge CSV candidates with area candidates
        candidates = csv_candidates + area_candidates
        
        # Step 4: If still < 3 results AND CSV has 0 results → call Overpass fallback
        if len(csv_candidates) == 0 and len(area_candidates) == 0:
            radius_m = int(radius_km * 1000)
            osm_restaurants = fetch_osm_nearby_restaurants(lat, lon, radius_m=min(radius_m, 2000))
            
            for osm_rest in osm_restaurants:
                # Calculate distance
                distance = haversine_distance(lat, lon, osm_rest['lat'], osm_rest['lon'])
                
                # Add OSM restaurant
                candidates.append({
                    'name': osm_rest['name'],
                    'area': area_name_lower if area_name_lower else 'unknown',
                    'city': 'Delhi NCR',
                    'rating': 0.0,
                    'rating_count': 0,
                    'cost_for_two': None,
                    'telephone': None,
                    'address': None,
                    'famous_food': None,
                    'latitude': osm_rest['lat'],
                    'longitude': osm_rest['lon'],
                    'distance_km': distance,
                    'source': 'osm',
                    'zomato_url': None
                })
    
    # If still no candidates, return None for both
    if not candidates:
        return {
            'safe_pick': None,
            'local_favourite': None
        }
    
    # Step 5: Apply ranking rules to final merged list
    # safe_pick: highest rating, tie-break: higher rating_count, then shorter distance
    safe_pick = max(candidates, key=lambda x: (
        x['rating'],
        x['rating_count'],
        -x['distance_km']
    ))
    
    # local_favourite: highest rating_count, tie-break: higher rating, then shorter distance
    local_favourite = max(candidates, key=lambda x: (
        x['rating_count'],
        x['rating'],
        -x['distance_km']
    ))
    
    # Step 6: Format recommendations with EXACT field list
    def format_recommendation(rec: Dict) -> Dict:
        return {
            'name': str(rec['name']),
            'area': str(rec['area']),
            'city': str(rec['city']),
            'rating': float(rec['rating']),
            'rating_count': int(rec['rating_count']),
            'cost_for_two': float(rec['cost_for_two']) if rec.get('cost_for_two') is not None else None,
            'telephone': str(rec['telephone']) if rec.get('telephone') is not None else None,
            'address': str(rec['address']) if rec.get('address') is not None else None,
            'famous_food': str(rec['famous_food']) if rec.get('famous_food') is not None else None,
            'latitude': float(rec['latitude']),
            'longitude': float(rec['longitude']),
            'distance_km': round(float(rec['distance_km']), 2),
            'source': str(rec.get('source', 'csv')),
            'zomato_url': str(rec['zomato_url']) if rec.get('zomato_url') is not None else None
        }
    
    return {
        'safe_pick': format_recommendation(safe_pick),
        'local_favourite': format_recommendation(local_favourite)
    }

def recommend_for_text_query(query: str, city: str = "Delhi") -> Dict:
    """
    Attempt to parse area from query and recommend by area.
    
    Args:
        query: Text query (attempts to match against area column)
        city: City name (default: "Delhi")
    
    Returns:
        Dictionary with recommendations or None if area not found
    """
    query_lower = query.lower().strip()
    
    # Try exact match against area column
    matching_rows = _df[_df['area'] == query_lower]
    
    if len(matching_rows) > 0:
        area = matching_rows.iloc[0]['area']
        return recommend_by_area(area, city)
    
    # If no exact match, return None
    return {
        'safe_pick': None,
        'local_favourite': None
    }

def recommend_by_area(area: str, city: str = "Delhi") -> Dict:
    """
    Get recommendations for a specific area.
    
    Args:
        area: Area name (normalized to lowercase)
        city: City name (default: "Delhi")
    
    Returns:
        Dictionary with 'safe_pick' and 'local_favourite' recommendations
    """
    area_lower = area.lower().strip()
    
    # Filter by city and area
    # Handle city matching - check if city contains "Delhi" or matches exactly
    city_filter = _df['city'].str.contains(city, case=False, na=False)
    area_filter = _df['area'] == area_lower
    
    candidates_df = _df[city_filter & area_filter]
    
    if len(candidates_df) == 0:
        return {
            'safe_pick': None,
            'local_favourite': None
        }
    
    # Convert to list of dicts
    candidates = []
    for _, row in candidates_df.iterrows():
        try:
            rec = {
                'name': row['name'],
                'area': row['area'],
                'city': row['city'],
                'rating': float(row['rating']) if pd.notna(row['rating']) else 0.0,
                'rating_count': int(row['rating_count']) if pd.notna(row['rating_count']) else 0,
                'cost_for_two': float(row['cost_for_two']) if pd.notna(row['cost_for_two']) else None,
                'telephone': str(row['telephone']) if pd.notna(row['telephone']) and str(row['telephone']) != '#ERROR!' else None,
                'address': str(row['address']) if pd.notna(row['address']) else None,
                'famous_food': str(row['famous_food']) if pd.notna(row['famous_food']) else None,
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'distance_km': 0.0,  # No distance for area-based search
                'source': 'csv',
                'zomato_url': str(row['Zomato link']) if pd.notna(row.get('Zomato link')) and str(row.get('Zomato link', '')).strip() else None
            }
            candidates.append(rec)
        except (ValueError, TypeError):
            continue
    
    if not candidates:
        return {
            'safe_pick': None,
            'local_favourite': None
        }
    
    # Select safe_pick and local_favourite using same logic
    safe_pick = max(candidates, key=lambda x: (
        x['rating'],
        x['rating_count'],
        -x['distance_km']
    ))
    
    local_favourite = max(candidates, key=lambda x: (
        x['rating_count'],
        x['rating'],
        -x['distance_km']
    ))
    
    # Format recommendations with EXACT field list
    def format_recommendation(rec: Dict) -> Dict:
        return {
            'name': str(rec['name']),
            'area': str(rec['area']),
            'city': str(rec['city']),
            'rating': float(rec['rating']),
            'rating_count': int(rec['rating_count']),
            'cost_for_two': float(rec['cost_for_two']) if rec.get('cost_for_two') is not None else None,
            'telephone': str(rec['telephone']) if rec.get('telephone') is not None else None,
            'address': str(rec['address']) if rec.get('address') is not None else None,
            'famous_food': str(rec['famous_food']) if rec.get('famous_food') is not None else None,
            'latitude': float(rec['latitude']),
            'longitude': float(rec['longitude']),
            'distance_km': round(float(rec['distance_km']), 2),
            'source': str(rec.get('source', 'csv')),
            'zomato_url': str(rec['zomato_url']) if rec.get('zomato_url') is not None else None
        }
    
    return {
        'safe_pick': format_recommendation(safe_pick),
        'local_favourite': format_recommendation(local_favourite)
    }

if __name__ == '__main__':
    # CLI demonstration with three sample queries for central Delhi
    # Central Delhi coordinates: ~28.651717, 77.221938 (Connaught Place area)
    
    print("=" * 60)
    print("Food Recommender CLI - Sample Queries")
    print("=" * 60)
    
    # Sample 1: Connaught Place
    print("\n1. Recommendations for Connaught Place (28.651717, 77.221938):")
    print("-" * 60)
    result1 = recommend_for_location(28.651717, 77.221938, radius_km=5)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    
    # Sample 2: Rajiv Chowk Metro Station area
    print("\n2. Recommendations for Rajiv Chowk area (28.630000, 77.220000):")
    print("-" * 60)
    result2 = recommend_for_location(28.630000, 77.220000, radius_km=3)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    # Sample 3: India Gate area
    print("\n3. Recommendations for India Gate area (28.612900, 77.229500):")
    print("-" * 60)
    result3 = recommend_for_location(28.612900, 77.229500, radius_km=4)
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)

