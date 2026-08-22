"""
Area to coordinates mapping for Delhi areas.
Used for food recommendations when user mentions area names.
"""

# Common Delhi areas with approximate centroids (lat, lon)
AREA_COORDINATES = {
    # Major areas
    "vasant kunj": (28.5444, 77.1633),
    "dwarka": (28.5642, 77.0589),
    "dwarka sector": (28.5642, 77.0589),
    "connaught place": (28.6315, 77.2167),
    "cp": (28.6315, 77.2167),
    "rajiv chowk": (28.6315, 77.2167),
    "saket": (28.5245, 77.2010),
    "lajpat nagar": (28.5675, 77.2430),
    "karol bagh": (28.6517, 77.1917),
    "khan market": (28.6001, 77.2274),
    "chandni chowk": (28.6562, 77.2410),
    "greater kailash": (28.5500, 77.2400),
    "gk": (28.5500, 77.2400),
    "greater kailash 1": (28.5500, 77.2400),
    "gk1": (28.5500, 77.2400),
    "greater kailash 2": (28.5500, 77.2400),
    "gk2": (28.5500, 77.2400),
    "rohini": (28.7500, 77.1000),
    "pitampura": (28.7000, 77.1500),
    "rajouri garden": (28.6500, 77.1200),
    "janakpuri": (28.6200, 77.0800),
    "janakpuri west": (28.6200, 77.0800),
    "hauz khas": (28.5400, 77.2000),
    "defence colony": (28.5700, 77.2300),
    "south extension": (28.5700, 77.2200),
    "south ex": (28.5700, 77.2200),
    "noida": (28.5355, 77.3910),
    "gurgaon": (28.4595, 77.0266),
    "gurugram": (28.4595, 77.0266),
    "faridabad": (28.4089, 77.3178),
    "aerocity": (28.5562, 77.1000),
    "delhi aerocity": (28.5562, 77.1000),
    "airport": (28.5562, 77.1000),
    "igi airport": (28.5562, 77.1000),
    "indirapuram": (28.6400, 77.3700),
    "vasundhara": (28.6500, 77.3800),
    "mayur vihar": (28.6000, 77.3000),
    "laxmi nagar": (28.6400, 77.2800),
    "preet vihar": (28.6417, 77.2947),
    "kashmere gate": (28.6692, 77.2285),
    "new delhi": (28.6139, 77.2090),
    "old delhi": (28.6562, 77.2410),
    "paharganj": (28.6400, 77.2100),
    "daryaganj": (28.6500, 77.2400),
    "civil lines": (28.6800, 77.2200),
    "model town": (28.7200, 77.2000),
    "ashok vihar": (28.7000, 77.1800),
    "rohini sector": (28.7500, 77.1000),
    "dwarka sector 21": (28.5642, 77.0589),
    "dwarka sector 22": (28.5642, 77.0589),
    "dwarka sector 23": (28.5642, 77.0589),
    "sector 18": (28.6200, 77.3700),  # Noida
    "sector 15": (28.6000, 77.3500),  # Noida
    "sector 12": (28.5800, 77.3300),  # Noida
    "dlf phase": (28.4595, 77.0266),  # Gurgaon
    "dlf phase 2": (28.4595, 77.0266),
    "dlf phase 4": (28.4595, 77.0266),
    "cyber city": (28.4595, 77.0266),  # Gurgaon
    "mg road": (28.4595, 77.0266),  # Gurgaon
}

def get_area_coordinates(area_name: str):
    """
    Get coordinates for an area name.
    
    Args:
        area_name: Area name (case-insensitive)
    
    Returns:
        Tuple of (lat, lon) or None if not found
    """
    area_lower = area_name.lower().strip()
    
    # Direct lookup
    if area_lower in AREA_COORDINATES:
        return AREA_COORDINATES[area_lower]
    
    # Try partial matches for sector numbers
    if "sector" in area_lower:
        # Extract sector number if present
        import re
        sector_match = re.search(r'sector\s*(\d+)', area_lower)
        if sector_match:
            sector_num = sector_match.group(1)
            # Check if it's a known sector area
            if "dwarka" in area_lower:
                return AREA_COORDINATES.get("dwarka")
            elif "noida" in area_lower or "sector" in area_lower:
                # Default to Noida sector area
                return AREA_COORDINATES.get("noida")
    
    # Try fuzzy matching for common variations
    area_variations = {
        "vasant kunj": ["vasantkunj", "vasant kunj"],
        "dwarka": ["dwarka sector", "dwarka sec"],
        "connaught place": ["cp", "connaught", "rajiv chowk"],
        "saket": ["saket metro", "saket area"],
        "lajpat nagar": ["lajpat", "lajpat nagar metro"],
        "greater kailash": ["gk", "greater kailash 1", "gk1", "greater kailash 2", "gk2"],
        "hauz khas": ["hauz khas metro", "hauz khas village"],
        "south extension": ["south ex", "south extension part 1", "south extension part 2"],
    }
    
    for key, variations in area_variations.items():
        if any(var in area_lower for var in variations) or area_lower in variations:
            return AREA_COORDINATES.get(key)
    
    return None

def extract_area_from_query(query: str) -> tuple:
    """
    Extract area name from a food query.
    
    Args:
        query: User query text
    
    Returns:
        Tuple of (area_name, coordinates) or (None, None)
        Special case: ("around_me", None) for "around me" queries
    """
    query_lower = query.lower()
    
    # Check for "around me" or "near me" - return special marker
    if any(phrase in query_lower for phrase in ["around me", "near me", "nearby", "close to me"]):
        return ("around_me", None)
    
    # Common patterns for area mentions
    area_keywords = [
        "near", "in", "around", "at", "mein", "ke paas", "ke pass"
    ]
    
    # Check for explicit area mentions
    for area_name, coords in AREA_COORDINATES.items():
        # Check if area name appears in query
        if area_name in query_lower:
            return (area_name, coords)
        
        # Check for variations
        area_parts = area_name.split()
        if len(area_parts) > 1:
            # Check if all parts of area name are in query
            if all(part in query_lower for part in area_parts):
                return (area_name, coords)
    
    # Check for "near X" or "in X" patterns
    import re
    for keyword in area_keywords:
        pattern = rf'{keyword}\s+([a-z\s]+?)(?:\s|$|,|\.|\?)'
        match = re.search(pattern, query_lower)
        if match:
            potential_area = match.group(1).strip()
            # Skip if it's "me"
            if potential_area.lower() == "me":
                continue
            coords = get_area_coordinates(potential_area)
            if coords:
                return (potential_area, coords)
    
    # Check for area at start or end of query
    words = query_lower.split()
    for i, word in enumerate(words):
        # Skip common words
        if word in ["me", "my", "the", "a", "an", "near", "in", "at", "around"]:
            continue
        # Check single word
        coords = get_area_coordinates(word)
        if coords:
            return (word, coords)
        
        # Check two-word combinations
        if i < len(words) - 1:
            two_word = f"{word} {words[i+1]}"
            coords = get_area_coordinates(two_word)
            if coords:
                return (two_word, coords)
    
    return (None, None)

