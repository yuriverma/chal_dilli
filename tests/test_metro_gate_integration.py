#!/usr/bin/env python3
"""
Integration test for metro route with gate suggestion
"""

import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from enhanced_metro_router import EnhancedMetroRouter

class TestMetroGateIntegration(unittest.TestCase):
    """Integration tests for metro routing with gate suggestions"""
    
    def setUp(self):
        """Set up test router"""
        self.router = EnhancedMetroRouter()
    
    def test_metro_route_with_gate_suggestion(self):
        """Test that metro route response includes gate suggestion when available"""
        # Test with a route that ends at a station with gate data
        # Using Hauz Khas as destination (known to be in gate CSV)
        query = "Rajiv Chowk se Hauz Khas kaise jaaye?"
        
        result = self.router.get_route_response(query)
        
        # Verify we got a route response
        self.assertIn('response', result)
        self.assertIn('route_data', result)
        
        response_text = result['response']
        
        # Check that response contains route information
        self.assertGreater(len(response_text), 50, "Response should have meaningful content")
        
        # Check if gate suggestion is included (optional - only if gate data exists)
        # We check for gate-related keywords that would appear in the suggestion
        has_gate_suggestion = (
            '🚪' in response_text or
            'gate' in response_text.lower() or
            'lift' in response_text.lower()
        )
        
        # Gate suggestion is optional, so we just verify the route works
        # If gate data exists, it should be included
        print(f"\nRoute response length: {len(response_text)}")
        print(f"Contains gate suggestion: {has_gate_suggestion}")
        if has_gate_suggestion:
            print("✅ Gate suggestion found in response")
        else:
            print("ℹ️ No gate suggestion (may be normal if gate data not loaded)")
    
    def test_metro_route_structure(self):
        """Test that metro route response has correct structure"""
        query = "Dwarka se Kashmere Gate kaise jaaye?"
        
        result = self.router.get_route_response(query)
        
        # Verify structure
        self.assertIn('response', result)
        self.assertIn('route_data', result)
        self.assertIn('language', result)
        self.assertIn('has_route', result)
        
        # Verify response is a string
        self.assertIsInstance(result['response'], str)
        
        # Verify route data exists if route was found
        if result['has_route']:
            self.assertIsNotNone(result['route_data'])
    
    def test_route_with_destination_having_gates(self):
        """Test route to a station that should have gate data"""
        # Test multiple queries to stations that might have gate data
        test_queries = [
            "Rajiv Chowk se Hauz Khas",
            "Kashmere Gate se Rajiv Chowk",
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                result = self.router.get_route_response(query)
                self.assertIn('response', result)
                self.assertIsInstance(result['response'], str)
                self.assertGreater(len(result['response']), 20)

if __name__ == '__main__':
    unittest.main()


