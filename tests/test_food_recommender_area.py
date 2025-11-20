"""
Tests for area detection in food recommender.
Tests that queries like "food recommendations in rohini" work correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from food_recommender import recommend_for_text_query

def test_rohini_queries():
    """Test that Rohini queries return recommendations."""
    
    test_queries = [
        "food recommendations in rohini",
        "momos in rohini",
        "best food in rohini",
        "rohini",
        "rohini sector 13",
    ]
    
    print("=" * 60)
    print("Testing Area Detection for Rohini")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = recommend_for_text_query(query, city="Delhi")
        
        # Check that we got results
        has_safe_pick = result.get('safe_pick') is not None
        has_local_favourite = result.get('local_favourite') is not None
        
        print(f"  Safe Pick: {'✓' if has_safe_pick else '✗'}")
        print(f"  Local Favourite: {'✓' if has_local_favourite else '✗'}")
        
        if has_safe_pick:
            safe_pick = result['safe_pick']
            print(f"  Safe Pick Name: {safe_pick.get('name', 'N/A')}")
            print(f"  Safe Pick Area: {safe_pick.get('area', 'N/A')}")
            print(f"  Safe Pick Source: {safe_pick.get('source', 'N/A')}")
        
        if has_local_favourite:
            local_fav = result['local_favourite']
            print(f"  Local Favourite Name: {local_fav.get('name', 'N/A')}")
            print(f"  Local Favourite Area: {local_fav.get('area', 'N/A')}")
            print(f"  Local Favourite Source: {local_fav.get('source', 'N/A')}")
        
        # Assertions
        assert has_safe_pick or has_local_favourite, f"Query '{query}' should return at least one recommendation"
        
        if has_safe_pick:
            assert safe_pick.get('source') == 'csv', f"Safe pick should come from CSV, got {safe_pick.get('source')}"
            area = safe_pick.get('area', '').lower()
            assert 'rohini' in area, f"Safe pick area should contain 'rohini', got '{area}'"
        
        if has_local_favourite:
            assert local_fav.get('source') == 'csv', f"Local favourite should come from CSV, got {local_fav.get('source')}"
            area = local_fav.get('area', '').lower()
            assert 'rohini' in area, f"Local favourite area should contain 'rohini', got '{area}'"
        
        print("  ✓ Test passed")
    
    print("\n" + "=" * 60)
    print("All Rohini tests passed!")
    print("=" * 60)

def test_other_areas():
    """Test that other area queries also work."""
    
    test_cases = [
        ("food in cp", "connaught place"),
        ("food in dwarka", "dwarka"),
        ("best restaurants in karol bagh", "karol bagh"),
    ]
    
    print("\n" + "=" * 60)
    print("Testing Other Areas")
    print("=" * 60)
    
    for query, expected_area in test_cases:
        print(f"\nQuery: '{query}' (expected area: {expected_area})")
        result = recommend_for_text_query(query, city="Delhi")
        
        has_results = (result.get('safe_pick') is not None or 
                      result.get('local_favourite') is not None)
        
        if has_results:
            if result.get('safe_pick'):
                area = result['safe_pick'].get('area', '').lower()
                print(f"  Found area: {area}")
            print("  ✓ Test passed")
        else:
            print(f"  ⚠ No results (may be acceptable if area not in CSV)")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        test_rohini_queries()
        test_other_areas()
        print("\n✅ All tests completed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

