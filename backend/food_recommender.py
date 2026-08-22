"""
Food Recommender System for Chal Delhi
Provides location-based restaurant recommendations using haversine distance.
"""

import pandas as pd
import numpy as np
import math
from pathlib import Path
import json
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

# Import map utilities
try:
    from .maps_utils import reverse_geocode, fetch_osm_nearby_restaurants
except ImportError:
    # Handle case when running as script
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from maps_utils import reverse_geocode, fetch_osm_nearby_restaurants

# Get absolute project root path
_BASE_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _BASE_DIR / "data"

# Constants
CSV_PATH = _DATA_DIR / "food_data.csv"
EARTH_RADIUS_KM = 6371.0
MIN_RADIUS_KM = 0.1
MAX_RADIUS_KM = 50.0

# Load and preprocess data once on import
def _load_and_preprocess_data():
    """Load CSV and preprocess data."""
    df = pd.read_csv(str(CSV_PATH))
    
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

    # Precompute a lowercase searchable blob per row so dish/cuisine filtering
    # is a cheap vectorized string test instead of a per-query row scan.
    # NOTE: the CSV header spells the column "cusine" (sic) — that typo is why
    # cuisine was never used for matching.
    cuisine_col = 'cusine' if 'cusine' in df.columns else 'cuisine'
    df['_haystack'] = (
        df['name'].fillna('').astype(str) + ' | ' +
        df.get(cuisine_col, pd.Series('', index=df.index)).fillna('').astype(str) + ' | ' +
        df['famous_food'].fillna('').astype(str)
    ).str.lower()

    # Cache coordinates as radians once for vectorized haversine.
    df['_lat_rad'] = np.radians(df['latitude'].to_numpy())
    df['_lon_rad'] = np.radians(df['longitude'].to_numpy())

    return df.reset_index(drop=True)

# Load data on import
_df = _load_and_preprocess_data()

# Build area index for Delhi
def _build_area_index():
    """
    Build an index of area names for Delhi with canonical names and variants.
    Returns a dict mapping variant/token -> canonical area name (from CSV).
    """
    # Filter for Delhi areas
    delhi_df = _df[_df['city'].str.contains('Delhi', case=False, na=False)]
    
    # Get unique normalized areas (these are the canonical names from CSV)
    areas = delhi_df['area'].dropna().unique()
    
    # Build index: variant/token -> canonical area name
    area_index = {}
    
    for area in areas:
        area_normalized = area.lower().strip()
        if not area_normalized or area_normalized == 'nan':
            continue
        
        # The area itself is a canonical name - map it to itself
        area_index[area_normalized] = area_normalized
        
        # Extract base name and tokens for matching
        # Split by common separators
        parts = re.split(r'[\s,]+', area_normalized)
        
        # Add individual meaningful parts as variants
        base_words = {'sector', 'phase', 'block', 'market', 'road', 'nagar', 'colony', 
                     'vihar', 'enclave', 'new', 'delhi', 'ncr', 'near', 'opposite'}
        
        for part in parts:
            if part and len(part) > 2 and part not in base_words and not part.isdigit():
                # Map token to canonical area name
                if part not in area_index:
                    area_index[part] = area_normalized
                # Also check if we should prefer a more specific match
                # (e.g., if "rohini" appears in multiple areas, prefer the one with most matches)
        
        # Add n-grams (2-word and 3-word combinations) as variants
        if len(parts) > 1:
            for n in [2, 3]:
                for i in range(len(parts) - n + 1):
                    ngram = ' '.join(parts[i:i+n])
                    if ngram not in area_index:
                        area_index[ngram] = area_normalized
    
    return area_index

# Build area index on import
_area_index = _build_area_index()

# Debug flag (can be enabled for troubleshooting)
_DEBUG_AREA_DETECTION = False

def _debug_log(message: str):
    """Optional debug logging for area detection."""
    if _DEBUG_AREA_DETECTION:
        print(f"[AREA_DEBUG] {message}")

def _similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()

def _extract_area_from_query(query: str) -> Optional[Tuple[str, str]]:
    """
    Extract area name from natural language query.
    
    Args:
        query: User query text
    
    Returns:
        Tuple of (canonical_area_name, match_type) or None if no match found.
        match_type can be 'exact', 'token', 'fuzzy', or 'ngram'
    """
    query_lower = query.lower().strip()
    _debug_log(f"Processing query: '{query}'")
    
    # Step 1: Try exact match
    if query_lower in _area_index:
        canonical = query_lower
        _debug_log(f"Exact match found: '{canonical}'")
        return (canonical, 'exact')
    
    # Step 2: Tokenize query and try token/ngram matching
    # Remove common food/query words
    stop_words = {'food', 'recommendations', 'recommendation', 'best', 'good', 'restaurant', 
                  'restaurants', 'cafe', 'cafes', 'in', 'near', 'around', 'at', 'for', 
                  'the', 'a', 'an', 'and', 'or', 'of', 'to', 'from', 'momos', 'pizza',
                  'chinese', 'north', 'indian', 'south', 'italian', 'fast'}
    
    # Tokenize by splitting on whitespace and punctuation
    tokens = re.findall(r'\b\w+\b', query_lower)
    meaningful_tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    
    _debug_log(f"Meaningful tokens: {meaningful_tokens}")
    
    # Try matching individual tokens
    for token in meaningful_tokens:
        if token in _area_index:
            canonical = _area_index[token]  # Get canonical area name
            _debug_log(f"Token match found: '{token}' -> '{canonical}'")
            return (canonical, 'token')
    
    # Try matching n-grams (2-word and 3-word combinations)
    for n in [2, 3]:
        for i in range(len(meaningful_tokens) - n + 1):
            ngram = ' '.join(meaningful_tokens[i:i+n])
            if ngram in _area_index:
                canonical = _area_index[ngram]
                _debug_log(f"N-gram match found: '{ngram}' -> '{canonical}'")
                return (canonical, 'ngram')
    
    # Step 3: Try fuzzy matching with high confidence threshold
    best_match = None
    best_score = 0.0
    threshold = 0.7  # Require at least 70% similarity
    
    # Check against all canonical area names
    for canonical in _area_index.keys():
        # Try exact match against canonical
        score = _similarity_ratio(query_lower, canonical)
        if score > best_score:
            best_score = score
            best_match = canonical
        
        # Try matching against longest meaningful token
        if meaningful_tokens:
            longest_token = max(meaningful_tokens, key=len)
            if len(longest_token) >= 4:  # Only for substantial tokens
                score = _similarity_ratio(longest_token, canonical)
                if score > best_score:
                    best_score = score
                    best_match = canonical
    
    if best_match and best_score >= threshold:
        _debug_log(f"Fuzzy match found: '{best_match}' (score: {best_score:.2f})")
        return (best_match, 'fuzzy')
    
    _debug_log("No area match found")
    return None

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

DISH_SYNONYMS = {
    "momos": ["momo", "dumpling", "dimsum", "dim sum", "tibetan"],
    "breakfast": ["breakfast", "chole bhature", "poha", "sandwich", "cafe"],
    "paratha": ["paratha", "parantha", "paranthe"],
    "chaat": ["chaat", "golgappa", "pani puri", "tikki", "papdi"],
    "biryani": ["biryani", "biriyani", "mughlai", "hyderabadi"],
    "pizza": ["pizza", "italian"],
    "burger": ["burger", "fast food"],
    "chinese": ["chinese", "noodles", "hakka", "manchurian"],
    "north indian": ["north indian", "punjabi", "mughlai"],
    "south indian": ["south indian", "dosa", "idli", "vada", "uttapam"],
}


def _dish_mask(dish: Optional[str]) -> Optional[np.ndarray]:
    """Boolean mask over _df for rows matching a dish/cuisine, or None."""
    if not dish:
        return None
    terms = DISH_SYNONYMS.get(dish.lower(), [dish.lower()])
    hay = _df['_haystack']
    mask = np.zeros(len(_df), dtype=bool)
    for term in terms:
        mask |= hay.str.contains(re.escape(term), regex=True, na=False).to_numpy()
    return mask


def _row_to_dict(row, distance: float) -> Dict:
    """Convert a dataframe row to the recommendation dict shape."""
    phone = row['telephone']
    return {
        'name': row['name'],
        'area': row['area'],
        'city': row['city'],
        'rating': float(row['rating']) if pd.notna(row['rating']) else 0.0,
        'rating_count': int(row['rating_count']) if pd.notna(row['rating_count']) else 0,
        'cost_for_two': float(row['cost_for_two']) if pd.notna(row['cost_for_two']) else None,
        'telephone': str(phone) if pd.notna(phone) and str(phone) != '#ERROR!' else None,
        'address': str(row['address']) if pd.notna(row['address']) else None,
        'famous_food': str(row['famous_food']) if pd.notna(row['famous_food']) else None,
        'latitude': float(row['latitude']),
        'longitude': float(row['longitude']),
        'distance_km': float(distance),
        'source': 'csv',
        'zomato_url': str(row['Zomato link']) if pd.notna(row.get('Zomato link')) and str(row.get('Zomato link', '')).strip() else None
    }


def find_nearest(lat: float, lon: float, radius_km: float = 5, max_results: int = 50,
                 dish: Optional[str] = None) -> List[Dict]:
    """
    Find restaurants within radius of given coordinates.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_km: Search radius in kilometers (clamped to 0.1-50)
        max_results: Maximum number of results to return
        dish: Optional dish/cuisine to bias towards (e.g. "momos"). If nothing
              within the radius serves it, the filter is dropped rather than
              returning nothing.

    Returns:
        List of dictionaries with restaurant data and computed distance
    """
    # Clamp radius
    radius_km = max(MIN_RADIUS_KM, min(MAX_RADIUS_KM, radius_km))

    # Vectorized haversine over the whole frame — the previous implementation
    # ran df.iterrows() across ~7k rows on every single query.
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    dlat = _df['_lat_rad'].to_numpy() - lat_r
    dlon = _df['_lon_rad'].to_numpy() - lon_r
    a = np.sin(dlat / 2.0) ** 2 + math.cos(lat_r) * np.cos(_df['_lat_rad'].to_numpy()) * np.sin(dlon / 2.0) ** 2
    distances = EARTH_RADIUS_KM * 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    within = distances <= radius_km

    # Prefer rows that actually serve the requested dish; fall back to all
    # nearby rows if that yields nothing.
    dmask = _dish_mask(dish)
    selected = within & dmask if dmask is not None else within
    if not selected.any():
        selected = within

    idx = np.flatnonzero(selected)
    if idx.size == 0:
        return []
    idx = idx[np.argsort(distances[idx], kind="stable")][:max_results]

    results = []
    for i in idx:
        try:
            results.append(_row_to_dict(_df.iloc[i], distances[i]))
        except (ValueError, TypeError):
            continue

    return results

def recommend_for_location(lat: float, lon: float, radius_km: float = 5,
                           dish: Optional[str] = None) -> Dict:
    """
    Get two recommendations for a location: safe_pick and local_favourite.
    STRICT LOGIC: CSV is primary, OSM only if CSV has 0 results.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_km: Search radius in kilometers
        dish: Optional dish/cuisine to prefer (e.g. "momos")

    Returns:
        Dictionary with 'safe_pick' and 'local_favourite' recommendations
    """
    # Step 1: Filter CSV rows using haversine distance <= radius_km
    csv_candidates = find_nearest(lat, lon, radius_km, max_results=100, dish=dish)
    
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

def recommend_for_text_query(query: str, city: str = "Delhi", dish: Optional[str] = None) -> Dict:
    """
    Attempt to parse area from natural language query and recommend by area.
    Improved area detection supports queries like:
    - "food recommendations in rohini"
    - "best food in rohini"
    - "momos in rohini"
    - "rohini sector 9"
    
    Args:
        query: Text query (attempts to extract area name from natural language)
        city: City name (default: "Delhi")
    
    Returns:
        Dictionary with recommendations or None if area not found
    """
    # Extract area from query using improved detection
    area_result = _extract_area_from_query(query)
    
    if area_result:
        canonical_area, match_type = area_result
        _debug_log(f"Using area '{canonical_area}' (match type: {match_type})")
        
        # Get recommendations using the canonical area name
        result = recommend_by_area(canonical_area, city, dish=dish)
        
        # If we got results, return them
        if result.get('safe_pick') or result.get('local_favourite'):
            return result
    
    # If no area match found or no results, return None
    _debug_log("No recommendations found")
    return {
        'safe_pick': None,
        'local_favourite': None
    }

def recommend_by_area(area: str, city: str = "Delhi", dish: Optional[str] = None) -> Dict:
    """
    Get recommendations for a specific area.

    Args:
        area: Area name (normalized to lowercase)
        city: City name (default: "Delhi")
        dish: Optional dish/cuisine to prefer (e.g. "momos")

    Returns:
        Dictionary with 'safe_pick' and 'local_favourite' recommendations
    """
    area_lower = area.lower().strip()

    # Filter by city and area
    # Handle city matching - check if city contains "Delhi" or matches exactly
    city_filter = _df['city'].str.contains(city, case=False, na=False)
    area_filter = _df['area'] == area_lower

    candidates_df = _df[city_filter & area_filter]

    # Narrow to the requested dish when at least one match exists in this area.
    dmask = _dish_mask(dish)
    if dmask is not None and len(candidates_df):
        dish_df = candidates_df[dmask[candidates_df.index]]
        if len(dish_df):
            candidates_df = dish_df

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

