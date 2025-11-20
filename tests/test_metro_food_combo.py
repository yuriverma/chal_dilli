#!/usr/bin/env python3
"""
Tests for Metro Route + Destination Food Combo Feature
Ensures metro routes include food recommendations at destination
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from chal_dilli_enhanced import ChalDilliEnhanced

def test_metro_food_combo():
    """Test that metro routes include food recommendations"""
    print("=" * 60)
    print("Testing Metro Route + Food Combo Feature")
    print("=" * 60)
    
    chal_dilli = ChalDilliEnhanced()
    
    # Test queries
    test_queries = [
        "dwarka to hauz khas metro",
        "how to go from saket to cp",
        "metro from rajouri garden to hauz khas",
        "dwarka se rajiv chowk kaise jaaye",
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        response = chal_dilli.generate_response(query)
        print(f"\nResponse:\n{response}")
        
        # Assertions
        assert response, "Response should not be empty"
        assert len(response) > 0, "Response should have content"
        
        # Check that it contains metro route information
        metro_indicators = ["route", "min", "km", "Fare", "fare", "Take", "line", "Line"]
        has_metro_info = any(indicator in response for indicator in metro_indicators)
        assert has_metro_info, f"Response should contain metro route info. Response: {response[:200]}"
        
        # Check that it contains food recommendations
        food_indicators = ["Safe pick", "Local favourite", "rating", "Zomato"]
        has_food_info = any(indicator in response for indicator in food_indicators)
        assert has_food_info, f"Response should contain food recommendations. Response: {response[-300:]}"
        
        # Check that food section appears after metro route
        # (food keywords should appear later in the response)
        metro_keywords_pos = []
        food_keywords_pos = []
        
        for keyword in metro_indicators:
            pos = response.find(keyword)
            if pos != -1:
                metro_keywords_pos.append(pos)
        
        for keyword in food_indicators:
            pos = response.find(keyword)
            if pos != -1:
                food_keywords_pos.append(pos)
        
        if metro_keywords_pos and food_keywords_pos:
            max_metro_pos = max(metro_keywords_pos)
            min_food_pos = min(food_keywords_pos)
            assert min_food_pos > max_metro_pos, "Food recommendations should appear after metro route"
        
        # Check that gate suggestion is present (if available)
        gate_indicators = ["🚪", "gate", "Gate", "use karo", "use karein"]
        has_gate_info = any(indicator in response for indicator in gate_indicators)
        # Gate suggestion is optional, so we don't assert it
        
        results.append({
            "query": query,
            "has_metro_route": has_metro_info,
            "has_food_recommendations": has_food_info,
            "has_gate_suggestion": has_gate_info,
            "response_length": len(response),
            "food_appears_after_metro": min_food_pos > max_metro_pos if (metro_keywords_pos and food_keywords_pos) else None
        })
        
        print(f"\n✅ Test passed for: {query}")
        print(f"   - Metro route: {'✅' if has_metro_info else '❌'}")
        print(f"   - Food recommendations: {'✅' if has_food_info else '❌'}")
        print(f"   - Gate suggestion: {'✅' if has_gate_info else '⚠️ (optional)'}")
    
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for result in results:
        print(f"\nQuery: {result['query']}")
        print(f"  Metro route: {result['has_metro_route']}")
        print(f"  Food recommendations: {result['has_food_recommendations']}")
        print(f"  Gate suggestion: {result['has_gate_suggestion']}")
        print(f"  Response length: {result['response_length']} chars")
    
    print(f"\n✅ All tests passed!")
    return results

def test_metro_logic_unchanged():
    """Test that metro routing logic is unchanged"""
    print("\n" + "=" * 60)
    print("Testing Metro Logic Unchanged")
    print("=" * 60)
    
    chal_dilli = ChalDilliEnhanced()
    
    # Test that metro router still works
    query = "dwarka to hauz khas metro"
    route_result = chal_dilli.enhanced_router.get_route_response(query)
    
    assert route_result, "Route result should not be None"
    assert "response" in route_result, "Route result should have 'response' key"
    assert route_result.get("has_route") == True, "Route should be found"
    
    print("✅ Metro routing logic is unchanged")
    return True

def test_food_logic_unchanged():
    """Test that food recommendation logic is unchanged"""
    print("\n" + "=" * 60)
    print("Testing Food Logic Unchanged")
    print("=" * 60)
    
    from food_recommender import recommend_for_location, recommend_by_area
    
    # Test location-based recommendation
    result1 = recommend_for_location(28.5400, 77.2000, radius_km=3)  # Hauz Khas area
    assert result1 is not None, "Food recommendation should return result"
    assert "safe_pick" in result1 or "local_favourite" in result1, "Should have at least one recommendation"
    
    # Test area-based recommendation
    result2 = recommend_by_area("hauz khas", city="Delhi")
    assert result2 is not None, "Area-based recommendation should return result"
    
    print("✅ Food recommendation logic is unchanged")
    return True

def test_dtc_logic_unchanged():
    """Test that DTC routing logic is unchanged"""
    print("\n" + "=" * 60)
    print("Testing DTC Logic Unchanged")
    print("=" * 60)
    
    chal_dilli = ChalDilliEnhanced()
    
    # Test that DTC queries still work (if DTC router is available)
    if chal_dilli.dtc_router:
        query = "dtc bus route from dwarka to kashmere gate"
        response = chal_dilli.generate_response(query)
        
        # Should not contain food recommendations for DTC queries
        assert "Safe pick" not in response or "DTC" in response, "DTC queries should not have food recommendations"
        print("✅ DTC routing logic is unchanged")
    else:
        print("⚠️ DTC router not available, skipping test")
    
    return True

if __name__ == "__main__":
    try:
        # Run all tests
        test_results = test_metro_food_combo()
        test_metro_logic_unchanged()
        test_food_logic_unchanged()
        test_dtc_logic_unchanged()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

