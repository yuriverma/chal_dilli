"""
Tests for DTC Bus Router
Tests that DTC routing works correctly with GTFS data.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dtc_router import DTCRouter

def test_dtc_router_loads():
    """Test that DTC router loads GTFS data correctly."""
    print("=" * 60)
    print("Testing DTC Router GTFS Loading")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.normpath(os.path.join(base_dir, "..", "data", "GTFS"))
    
    if not os.path.exists(gtfs_dir):
        print(f"⚠️ GTFS directory not found: {gtfs_dir}")
        print("Skipping DTC router tests")
        return False
    
    try:
        router = DTCRouter(gtfs_dir)
        print(f"✓ DTC router initialized")
        print(f"  Stops loaded: {len(router.stops)}")
        print(f"  Routes loaded: {len(router.routes)}")
        print(f"  Trips loaded: {len(router.trip_route)}")
        print(f"  Edges created: {len(router.edge_weight)}")
        
        assert len(router.stops) > 0, "Should have at least one stop"
        assert len(router.routes) > 0, "Should have at least one route"
        assert len(router.edge_weight) > 0, "Should have at least one edge"
        
        print("✓ All loading assertions passed")
        return True
    except Exception as e:
        print(f"❌ Error loading DTC router: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fuzzy_stop_matching():
    """Test fuzzy stop name matching."""
    print("\n" + "=" * 60)
    print("Testing Fuzzy Stop Name Matching")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.normpath(os.path.join(base_dir, "..", "data", "GTFS"))
    
    if not os.path.exists(gtfs_dir):
        print("⚠️ GTFS directory not found, skipping test")
        return False
    
    try:
        router = DTCRouter(gtfs_dir)
        
        # Test queries that should match
        test_cases = [
            ("dwarka", None),  # Should find a stop with dwarka in name
            ("kashmere gate", None),
            ("cp", None),  # Should match connaught place
            ("connaught place", None),
        ]
        
        for query, expected_stop_id in test_cases:
            print(f"\nQuery: '{query}'")
            stop_id = router.find_best_stop_id(query)
            
            if stop_id:
                stop_info = router.stops[stop_id]
                print(f"  Matched: {stop_info['name']} (ID: {stop_id})")
                print(f"  ✓ Match found")
            else:
                print(f"  ⚠ No match found (may be acceptable if stop not in data)")
        
        print("\n✓ Fuzzy matching test completed")
        return True
    except Exception as e:
        print(f"❌ Error in fuzzy matching test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_computation():
    """Test that route computation works between two known stops."""
    print("\n" + "=" * 60)
    print("Testing Route Computation")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.normpath(os.path.join(base_dir, "..", "data", "GTFS"))
    
    if not os.path.exists(gtfs_dir):
        print("⚠️ GTFS directory not found, skipping test")
        return False
    
    try:
        router = DTCRouter(gtfs_dir)
        
        # Try to find two stops that exist
        # Use first few stops as test cases
        stop_ids = list(router.stops.keys())[:10]
        
        if len(stop_ids) < 2:
            print("⚠️ Not enough stops for route test")
            return False
        
        # Try computing route between first two stops
        src_id = stop_ids[0]
        dst_id = stop_ids[1]
        src_name = router.stops[src_id]["name"]
        dst_name = router.stops[dst_id]["name"]
        
        print(f"\nComputing route from '{src_name}' to '{dst_name}'")
        result = router.get_route(src_name, dst_name)
        
        if "error" in result:
            print(f"  ⚠ Route not found: {result['error']}")
            print("  (This may be acceptable if stops are not connected)")
        elif "message" in result:
            print(f"  ℹ {result['message']}")
        else:
            print(f"  ✓ Route found!")
            print(f"    Distance: {result['distance_km']} km")
            print(f"    Duration: {result['duration_min']} min")
            print(f"    Segments: {len(result['segments'])}")
            for i, seg in enumerate(result['segments'], 1):
                print(f"      {i}. {seg['route']}: {seg['from']} → {seg['to']}")
        
        # Also test with fuzzy matching
        print(f"\nTesting with fuzzy matching:")
        print(f"  Query: 'dwarka' to 'kashmere gate'")
        fuzzy_result = router.get_route("dwarka", "kashmere gate")
        
        if "error" in fuzzy_result:
            print(f"  ⚠ {fuzzy_result['error']}")
        elif "message" in fuzzy_result:
            print(f"  ℹ {fuzzy_result['message']}")
        else:
            print(f"  ✓ Route found with fuzzy matching!")
            print(f"    From: {fuzzy_result['from']}")
            print(f"    To: {fuzzy_result['to']}")
            print(f"    Distance: {fuzzy_result['distance_km']} km")
            print(f"    Duration: {fuzzy_result['duration_min']} min")
        
        print("\n✓ Route computation test completed")
        return True
    except Exception as e:
        print(f"❌ Error in route computation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autocomplete():
    """Test autocomplete functionality."""
    print("\n" + "=" * 60)
    print("Testing Autocomplete")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.normpath(os.path.join(base_dir, "..", "data", "GTFS"))
    
    if not os.path.exists(gtfs_dir):
        print("⚠️ GTFS directory not found, skipping test")
        return False
    
    try:
        router = DTCRouter(gtfs_dir)
        
        test_prefixes = ["dwarka", "kashmere", "cp", "connaught"]
        
        for prefix in test_prefixes:
            print(f"\nAutocomplete for '{prefix}':")
            suggestions = router.autocomplete_stop_names(prefix, limit=5)
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                print(f"  ✓ Found {len(suggestions)} suggestions")
            else:
                print(f"  ⚠ No suggestions found")
        
        print("\n✓ Autocomplete test completed")
        return True
    except Exception as e:
        print(f"❌ Error in autocomplete test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nearest_stop():
    """Test nearest stop lookup."""
    print("\n" + "=" * 60)
    print("Testing Nearest Stop Lookup")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gtfs_dir = os.path.normpath(os.path.join(base_dir, "..", "data", "GTFS"))
    
    if not os.path.exists(gtfs_dir):
        print("⚠️ GTFS directory not found, skipping test")
        return False
    
    try:
        router = DTCRouter(gtfs_dir)
        
        # Test with Connaught Place coordinates (approximate)
        test_lat, test_lon = 28.6315, 77.2167
        
        print(f"\nFinding nearest stop to ({test_lat}, {test_lon})")
        nearest = router.find_nearest_stop(test_lat, test_lon, max_distance_km=10.0)
        
        if nearest:
            print(f"  ✓ Nearest stop: {nearest['name']}")
            print(f"    Distance: {nearest['distance_km']:.2f} km")
            print(f"    Coordinates: ({nearest['lat']}, {nearest['lon']})")
        else:
            print(f"  ⚠ No stop found within 10 km")
        
        print("\n✓ Nearest stop test completed")
        return True
    except Exception as e:
        print(f"❌ Error in nearest stop test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        results = []
        
        results.append(("GTFS Loading", test_dtc_router_loads()))
        results.append(("Fuzzy Matching", test_fuzzy_stop_matching()))
        results.append(("Route Computation", test_route_computation()))
        results.append(("Autocomplete", test_autocomplete()))
        results.append(("Nearest Stop", test_nearest_stop()))
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        for test_name, passed in results:
            status = "✓ PASSED" if passed else "⚠ SKIPPED/FAILED"
            print(f"{test_name}: {status}")
        
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

