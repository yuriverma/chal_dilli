#!/usr/bin/env python3
"""
Gate Lookup Module for DMRC Metro Stations
Provides functions to look up accessible gates and lifts for metro stations.
"""

import csv
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "dmrc_gates.csv")

# Load gates data once at import
_gates_data: List[Dict] = []

def _load_gates_data():
    """Load gates data from CSV file."""
    global _gates_data
    if _gates_data:
        return  # Already loaded
    
    if not os.path.exists(CSV_PATH):
        print(f"⚠️ Warning: Gate data CSV not found at {CSV_PATH}")
        print("   Run: python backend/dmrc_gates_parser.py to generate it.")
        return
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            _gates_data = list(reader)
        print(f"✅ Loaded {len(_gates_data)} gate records from {CSV_PATH}")
    except Exception as e:
        print(f"❌ Error loading gate data: {e}")
        _gates_data = []

# Load on import
_load_gates_data()

def normalize_station_name(name: str) -> str:
    """Normalize station name to consistent lowercase trimmed form."""
    if not name:
        return ""
    # Remove common suffixes
    name = re.sub(r'\s+(metro\s+)?station\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+stn\s*$', '', name, flags=re.IGNORECASE)
    # Normalize to lowercase and strip
    return name.lower().strip()

def fuzzy_match_station(query_name: str, threshold: float = 0.7) -> Optional[str]:
    """
    Find best matching station name using fuzzy matching.
    Returns the normalized station name if match found, None otherwise.
    """
    query_normalized = normalize_station_name(query_name)
    if not query_normalized:
        return None
    
    # Get unique station names from data
    unique_stations = {}
    for gate in _gates_data:
        station = normalize_station_name(gate.get('station_name', ''))
        if station and station not in unique_stations:
            unique_stations[station] = gate.get('station_name', '')
    
    # Try exact match first
    if query_normalized in unique_stations:
        return query_normalized
    
    # Try fuzzy matching
    best_match = None
    best_score = 0.0
    
    for normalized, original in unique_stations.items():
        # Calculate similarity
        score = SequenceMatcher(None, query_normalized, normalized).ratio()
        
        # Also check if query is a substring or vice versa
        if query_normalized in normalized or normalized in query_normalized:
            score = max(score, 0.85)  # Boost substring matches
        
        if score > best_score:
            best_score = score
            best_match = normalized
    
    if best_score >= threshold:
        return best_match
    
    return None

def get_gates_for_station(station_name: str, line_name: Optional[str] = None) -> List[Dict]:
    """
    Get all gate records for a station.
    
    Args:
        station_name: Station name (will be fuzzy matched)
        line_name: Optional line name to filter by
    
    Returns:
        List of gate record dictionaries
    """
    if not _gates_data:
        return []
    
    # Find matching station
    matched_station = fuzzy_match_station(station_name)
    if not matched_station:
        return []
    
    # Filter gates for this station
    gates = []
    for gate in _gates_data:
        gate_station = normalize_station_name(gate.get('station_name', ''))
        if gate_station == matched_station:
            # Filter by line if specified
            if line_name:
                gate_line = normalize_station_name(gate.get('line_name', ''))
                query_line = normalize_station_name(line_name)
                if gate_line != query_line:
                    continue
            gates.append(gate)
    
    return gates

def get_best_gate_for_station(station_name: str, line_name: Optional[str] = None) -> Optional[Dict]:
    """
    Get the best recommended gate or lift for Divyangjan.
    
    Rules:
    1. Prefer entries that clearly mention lift availability
    2. If multiple candidates exist, pick the lowest gate number
    3. Return both gate number and exit landmark
    
    Args:
        station_name: Station name (will be fuzzy matched)
        line_name: Optional line name to filter by
    
    Returns:
        Dictionary with gate information or None if not found
    """
    gates = get_gates_for_station(station_name, line_name)
    if not gates:
        return None
    
    # Score gates based on lift availability and gate number
    def score_gate(gate: Dict) -> tuple:
        # Higher score is better
        has_lift = gate.get('has_lift_inside_gate', 'false').lower()
        gate_num_str = gate.get('gate_number', '')
        
        # Lift availability score (prefer true > descriptive > false)
        lift_score = 0
        if has_lift == 'true':
            lift_score = 3
        elif has_lift and has_lift != 'false' and len(has_lift) > 5:
            lift_score = 2  # Descriptive text
        else:
            lift_score = 1
        
        # Gate number score (prefer lower numbers, but "main" is special)
        gate_num_score = 999  # Default high number
        if gate_num_str.lower() == 'main':
            gate_num_score = 0  # Main gate is preferred
        elif gate_num_str.isdigit():
            gate_num_score = int(gate_num_str)
        
        # Return tuple for sorting (higher lift_score first, then lower gate_num_score)
        return (-lift_score, gate_num_score)
    
    # Sort by score
    sorted_gates = sorted(gates, key=score_gate)
    best_gate = sorted_gates[0]
    
    # Format result
    result = {
        'station_name': best_gate.get('station_name', ''),
        'line_name': best_gate.get('line_name', ''),
        'gate_or_lift_label': best_gate.get('gate_or_lift_label', ''),
        'gate_type': best_gate.get('gate_type', 'gate'),
        'gate_number': best_gate.get('gate_number', ''),
        'has_lift': best_gate.get('has_lift_inside_gate', 'false'),
        'exit_landmark': best_gate.get('exit_landmark', ''),
        'notes': best_gate.get('notes', '')
    }
    
    return result

def format_gate_suggestion(gate_info: Dict, language: str = "hinglish") -> str:
    """
    Format gate suggestion text for user response.
    
    Args:
        gate_info: Gate information dictionary from get_best_gate_for_station
        language: Language for response ("hinglish", "hindi", or "english")
    
    Returns:
        Formatted text string
    """
    station = gate_info.get('station_name', '')
    gate_label = gate_info.get('gate_or_lift_label', '')
    landmark = gate_info.get('exit_landmark', '')
    has_lift = gate_info.get('has_lift', 'false').lower()
    
    # Build gate description
    gate_desc = gate_label
    if has_lift == 'true':
        gate_desc += " (lift available)"
    elif has_lift and has_lift != 'false':
        gate_desc += f" ({has_lift})"
    
    # Format based on language
    if language == "hindi":
        if landmark:
            return f"\n\n🚪 {station} par {gate_desc} use karein, {landmark} ki taraf."
        else:
            return f"\n\n🚪 {station} par {gate_desc} use karein."
    elif language == "hinglish":
        if landmark:
            return f"\n\n🚪 {station} par {gate_desc} use karo, {landmark} ki taraf."
        else:
            return f"\n\n🚪 {station} par {gate_desc} use karo."
    else:  # english
        if landmark:
            return f"\n\n🚪 At {station}, use {gate_desc} towards {landmark}."
        else:
            return f"\n\n🚪 At {station}, use {gate_desc}."


