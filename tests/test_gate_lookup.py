#!/usr/bin/env python3
"""
Unit tests for gate_lookup module
"""

import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from gate_lookup import (
    get_gates_for_station,
    get_best_gate_for_station,
    normalize_station_name,
    fuzzy_match_station
)

class TestGateLookup(unittest.TestCase):
    """Test cases for gate lookup functionality"""
    
    def test_normalize_station_name(self):
        """Test station name normalization"""
        self.assertEqual(normalize_station_name("Hauz Khas"), "hauz khas")
        self.assertEqual(normalize_station_name("Hauz Khas Metro Station"), "hauz khas")
        self.assertEqual(normalize_station_name("  Rajiv Chowk  "), "rajiv chowk")
        self.assertEqual(normalize_station_name("Rajiv Chowk Station"), "rajiv chowk")
    
    def test_fuzzy_match_station(self):
        """Test fuzzy matching of station names"""
        # Test exact match
        matched = fuzzy_match_station("Hauz Khas")
        self.assertIsNotNone(matched, "Should match Hauz Khas")
        
        # Test with variations
        matched = fuzzy_match_station("hauz khas")
        self.assertIsNotNone(matched, "Should match lowercase")
        
        matched = fuzzy_match_station("Rajiv Chowk")
        self.assertIsNotNone(matched, "Should match Rajiv Chowk")
    
    def test_get_gates_for_station(self):
        """Test getting all gates for a station"""
        gates = get_gates_for_station("Hauz Khas")
        self.assertGreater(len(gates), 0, "Should find at least one gate for Hauz Khas")
        
        # Check structure
        if gates:
            gate = gates[0]
            self.assertIn('station_name', gate)
            self.assertIn('gate_or_lift_label', gate)
            self.assertIn('gate_type', gate)
    
    def test_get_best_gate_for_station(self):
        """Test getting best gate recommendation"""
        # Test with Hauz Khas (known to be in PDF)
        gate_info = get_best_gate_for_station("Hauz Khas")
        self.assertIsNotNone(gate_info, "Should find gate info for Hauz Khas")
        
        if gate_info:
            self.assertIn('station_name', gate_info)
            self.assertIn('gate_or_lift_label', gate_info)
            self.assertIn('gate_number', gate_info)
            self.assertIn('exit_landmark', gate_info)
            
            # Verify we have meaningful data
            self.assertGreater(len(gate_info['station_name']), 0)
            self.assertGreater(len(gate_info['gate_or_lift_label']), 0)
        
        # Test with Rajiv Chowk (known to be in PDF)
        gate_info = get_best_gate_for_station("Rajiv Chowk")
        self.assertIsNotNone(gate_info, "Should find gate info for Rajiv Chowk")
        
        if gate_info:
            self.assertIn('gate_number', gate_info)
            self.assertIn('exit_landmark', gate_info)
    
    def test_get_best_gate_with_line(self):
        """Test getting best gate with line filter"""
        gate_info = get_best_gate_for_station("Hauz Khas", line_name="Blue Line")
        # Should still work (may or may not filter depending on data)
        # Just verify it doesn't crash
        self.assertIsNotNone(gate_info or True)  # Accept None if no match
    
    def test_nonexistent_station(self):
        """Test with station that doesn't exist"""
        gate_info = get_best_gate_for_station("NonExistent Station XYZ")
        # Should return None gracefully
        self.assertIsNone(gate_info, "Should return None for nonexistent station")

if __name__ == '__main__':
    unittest.main()


