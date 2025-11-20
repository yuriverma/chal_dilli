#!/usr/bin/env python3
"""
Unit tests for metro intent detection and route extraction
Tests that both Hinglish and English metro queries work correctly.
"""

import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from chal_dilli_enhanced import ChalDilliEnhanced
from enhanced_metro_router import EnhancedMetroRouter

class TestMetroIntent(unittest.TestCase):
    """Test cases for metro intent detection and extraction"""
    
    def setUp(self):
        """Set up test instances"""
        self.chal_dilli = ChalDilliEnhanced()
        self.router = EnhancedMetroRouter()
    
    def test_hinglish_metro_queries(self):
        """Test that Hinglish metro queries are detected and routed correctly"""
        test_queries = [
            "dwarka se kashmere gate kaise jaana hai",
            "dwarka se kashmere gate tak",
            "rajiv chowk se hauz khas kaise jaaye",
            "dwarka sector 21 se hauz khas tak metro",
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                # Should be detected as metro query
                self.assertTrue(
                    self.chal_dilli._is_metro_query(query),
                    f"Query '{query}' should be detected as metro query"
                )
                
                # Should extract route
                route_info = self.router.extract_route_query(query)
                self.assertIsNotNone(
                    route_info,
                    f"Should extract route from '{query}'"
                )
                if route_info:
                    self.assertIn('from', route_info)
                    self.assertIn('to', route_info)
                    self.assertGreater(len(route_info['from']), 0)
                    self.assertGreater(len(route_info['to']), 0)
                
                # Should NOT be detected as bus query
                self.assertFalse(
                    self.chal_dilli._is_bus_query(query),
                    f"Query '{query}' should NOT be detected as bus query"
                )
                
                # Should NOT be detected as food query
                self.assertFalse(
                    self.chal_dilli._is_food_query(query),
                    f"Query '{query}' should NOT be detected as food query"
                )
    
    def test_english_metro_queries(self):
        """Test that English metro queries are detected and routed correctly"""
        test_queries = [
            "route from dwarka to kashmere gate",
            "metro from dwarka to kashmere gate",
            "how to go from dwarka to kashmere gate by metro",
            "fastest metro from dwarka to hauz khas",
            "metro route between rajiv chowk and hauz khas",
            "route dwarka sector 21 to hauz khas",
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                # Should be detected as metro query
                self.assertTrue(
                    self.chal_dilli._is_metro_query(query),
                    f"Query '{query}' should be detected as metro query"
                )
                
                # Should extract route
                route_info = self.router.extract_route_query(query)
                self.assertIsNotNone(
                    route_info,
                    f"Should extract route from '{query}'"
                )
                if route_info:
                    self.assertIn('from', route_info)
                    self.assertIn('to', route_info)
                    self.assertGreater(len(route_info['from']), 0)
                    self.assertGreater(len(route_info['to']), 0)
                
                # Should NOT be detected as bus query
                self.assertFalse(
                    self.chal_dilli._is_bus_query(query),
                    f"Query '{query}' should NOT be detected as bus query"
                )
                
                # Should NOT be detected as food query
                self.assertFalse(
                    self.chal_dilli._is_food_query(query),
                    f"Query '{query}' should NOT be detected as food query"
                )
    
    def test_metro_route_extraction_quality(self):
        """Test that route extraction produces valid station names"""
        test_cases = [
            {
                "query": "route from dwarka to kashmere gate",
                "expected_from": "dwarka",
                "expected_to": "kashmere gate"
            },
            {
                "query": "metro from rajiv chowk to hauz khas",
                "expected_from": "rajiv chowk",
                "expected_to": "hauz khas"
            },
            {
                "query": "dwarka se kashmere gate kaise jaana hai",
                "expected_from": "dwarka",
                "expected_to": "kashmere gate"
            },
            {
                "query": "route dwarka sector 21 to hauz khas",
                "expected_from": "dwarka sector 21",
                "expected_to": "hauz khas"
            },
        ]
        
        for case in test_cases:
            with self.subTest(query=case["query"]):
                route_info = self.router.extract_route_query(case["query"])
                self.assertIsNotNone(route_info, f"Should extract route from '{case['query']}'")
                
                if route_info:
                    # Check that extracted names contain expected keywords
                    from_normalized = route_info['from'].lower()
                    to_normalized = route_info['to'].lower()
                    
                    # Source should contain expected keywords
                    expected_from_parts = case["expected_from"].lower().split()
                    self.assertTrue(
                        any(part in from_normalized for part in expected_from_parts),
                        f"Extracted 'from' '{route_info['from']}' should contain '{case['expected_from']}'"
                    )
                    
                    # Destination should contain expected keywords
                    expected_to_parts = case["expected_to"].lower().split()
                    self.assertTrue(
                        any(part in to_normalized for part in expected_to_parts),
                        f"Extracted 'to' '{route_info['to']}' should contain '{case['expected_to']}'"
                    )
    
    def test_bus_queries_not_matched_as_metro(self):
        """Test that bus/DTC queries are NOT detected as metro queries"""
        bus_queries = [
            "dtc bus from dwarka to cp",
            "bus route from dwarka to kashmere gate",
            "dtc from dwarka to rajiv chowk",
            "only bus from dwarka to hauz khas",
        ]
        
        for query in bus_queries:
            with self.subTest(query=query):
                # Should be detected as bus query
                self.assertTrue(
                    self.chal_dilli._is_bus_query(query),
                    f"Query '{query}' should be detected as bus query"
                )
                
                # Should NOT be detected as metro query
                self.assertFalse(
                    self.chal_dilli._is_metro_query(query),
                    f"Query '{query}' should NOT be detected as metro query"
                )
    
    def test_food_queries_not_matched_as_metro(self):
        """Test that food queries are NOT detected as metro queries"""
        food_queries = [
            "food recommendations in rohini",
            "best food near dwarka",
            "momos in hauz khas",
            "restaurants near rajiv chowk",
        ]
        
        for query in food_queries:
            with self.subTest(query=query):
                # Should be detected as food query
                self.assertTrue(
                    self.chal_dilli._is_food_query(query),
                    f"Query '{query}' should be detected as food query"
                )
                
                # Should NOT be detected as metro query
                self.assertFalse(
                    self.chal_dilli._is_metro_query(query),
                    f"Query '{query}' should NOT be detected as metro query"
                )
    
    def test_metro_route_response_generation(self):
        """Test that metro queries generate route responses"""
        test_queries = [
            "dwarka se kashmere gate kaise jaana hai",
            "route from dwarka to kashmere gate",
            "metro from dwarka to kashmere gate",
            "how to go from dwarka to kashmere gate by metro",
            "fastest metro from dwarka to hauz khas",
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                # Generate response
                response = self.chal_dilli.generate_response(query)
                
                # Response should be non-empty
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 20, f"Response for '{query}' should be meaningful")
                
                # Response should NOT be a generic "unknown" response
                self.assertNotIn("sorry", response.lower()[:50], 
                               f"Response for '{query}' should not be a generic sorry message")
                
                # Response should contain route-related content (metro, route, station names, etc.)
                response_lower = response.lower()
                has_route_content = any(
                    keyword in response_lower 
                    for keyword in ["route", "metro", "line", "station", "min", "km", "fare"]
                )
                self.assertTrue(
                    has_route_content,
                    f"Response for '{query}' should contain route-related content"
                )

if __name__ == '__main__':
    unittest.main()

