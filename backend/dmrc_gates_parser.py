#!/usr/bin/env python3
"""
DMRC Divyangjan Gates Parser
Parses the official DMRC Divyangjan Entry/Exit Gates PDF and generates a clean CSV dataset.
"""

import csv
import os
import re
from typing import Dict, List, Optional

import pdfplumber

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "..", "data", "dmrc_divyang_gates.pdf")
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "dmrc_gates.csv")

# Line name patterns (case-insensitive)
LINE_PATTERNS = [
    r"RED\s+LINE",
    r"YELLOW\s+LINE",
    r"BLUE\s+LINE",
    r"GREEN\s+LINE",
    r"VIOLET\s+LINE",
    r"PINK\s+LINE",
    r"MAGENTA\s+LINE",
    r"GREY\s+LINE",
    r"AIRPORT\s+EXPRESS",
    r"RAPID\s+METRO"
]

def normalize_line_name(text: str) -> Optional[str]:
    """Extract and normalize line name from text."""
    text_upper = text.upper().strip()
    for pattern in LINE_PATTERNS:
        match = re.search(pattern, text_upper)
        if match:
            line = match.group(0).strip()
            # Normalize to title case
            return line.title().replace(" ", " ")
    return None

def extract_gate_number(gate_text: str) -> tuple:
    """
    Extract gate number and type from gate text.
    Returns: (gate_number, gate_type)
    gate_number can be a number or "main"
    gate_type can be "gate", "lift", or "main_gate"
    """
    gate_text = str(gate_text).strip()
    if not gate_text or gate_text.lower() in ["nan", "none", ""]:
        return (None, None)
    
    gate_lower = gate_text.lower()
    
    # Check for lift
    lift_match = re.search(r"lift\s*(?:no\.?|number)?\s*(\d+)", gate_lower)
    if lift_match:
        return (lift_match.group(1), "lift")
    
    # Check for gate number
    gate_match = re.search(r"gate\s*(?:no\.?|number)?\s*(\d+)", gate_lower)
    if gate_match:
        return (gate_match.group(1), "gate")
    
    # Check for main gate
    if "main" in gate_lower and "gate" in gate_lower:
        return ("main", "main_gate")
    
    # Check if it's just a number (assume it's a gate)
    num_match = re.search(r"^(\d+)$", gate_text)
    if num_match:
        return (num_match.group(1), "gate")
    
    # Default: treat as gate with original text
    return (gate_text, "gate")

def has_lift_availability(text: str) -> str:
    """Check if lift availability is mentioned in the text."""
    if not text or str(text).lower() in ["nan", "none", ""]:
        return "false"
    
    text_lower = str(text).lower()
    
    # Check for explicit lift mentions
    if "lift" in text_lower:
        if any(word in text_lower for word in ["yes", "available", "present", "hai", "hoga"]):
            return "true"
        if any(word in text_lower for word in ["no", "not", "nahi", "na"]):
            return "false"
        # If lift is mentioned but unclear, return descriptive text
        return text.strip()[:50]  # Return first 50 chars as description
    
    return "false"

def parse_pdf() -> List[Dict]:
    """Parse the PDF and extract gate information."""
    gates = []
    current_line = None
    
    print(f"Reading PDF from: {PDF_PATH}")
    
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF file not found: {PDF_PATH}")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}...")
            text = page.extract_text()
            
            # Check for line name in page text
            if text:
                line_match = normalize_line_name(text)
                if line_match:
                    current_line = line_match
                    print(f"  Found line: {current_line}")
            
            # Extract tables from page
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                # Skip header row (usually first row)
                # Try to identify header row by checking for column names
                start_idx = 0
                header_keywords = ["station", "gate", "lift", "location", "landmark", "s/n", "s or n"]
                
                for i, row in enumerate(table[:3]):  # Check first 3 rows
                    if row and any(keyword in str(row).lower() for keyword in header_keywords):
                        start_idx = i + 1
                        break
                
                # Process data rows
                for row_idx, row in enumerate(table[start_idx:], start=start_idx):
                    if not row or len(row) < 2:
                        continue
                    
                    # Skip empty rows
                    if all(not cell or str(cell).strip() == "" for cell in row):
                        continue
                    
                    # Extract columns (adjust indices based on actual PDF structure)
                    # Typical structure: S/N, Station, Gate/Lift, Lift Availability, Location/Landmark
                    try:
                        # Column 0: S/N (usually just a number, can skip)
                        # Column 1: Station name
                        # Column 2: Gate/Lift number
                        # Column 3: Lift availability (may be in gate column or separate)
                        # Column 4+: Location/Landmark
                        
                        station_name = None
                        gate_or_lift_label = None
                        has_lift = "false"
                        exit_landmark = None
                        notes = None
                        
                        # Skip header rows
                        row_str = " ".join([str(c) for c in row if c]).lower()
                        if any(keyword in row_str for keyword in ["s/n", "s or n", "entry / exit gate", "location of"]):
                            continue
                        
                        # Find station name (usually in column 1 or 2)
                        # Skip column 0 which is usually S/N
                        for col_idx in range(1, min(4, len(row))):
                            cell = str(row[col_idx]).strip() if col_idx < len(row) and row[col_idx] else ""
                            if not cell or cell.lower() in ["nan", "none", ""]:
                                continue
                            
                            # Skip if it's clearly a gate/lift label
                            if any(keyword in cell.lower() for keyword in ["gate no", "lift no", "gate number", "lift number"]):
                                if not gate_or_lift_label:
                                    gate_or_lift_label = cell
                                continue
                            
                            # Skip if it's just a number (likely S/N column)
                            if cell.isdigit() and len(cell) < 4:
                                continue
                            
                            # Likely station name
                            if not station_name and len(cell) > 2:
                                station_name = cell
                            elif station_name and len(cell) > 2:
                                # Check if it's a gate/lift label
                                if any(keyword in cell.lower() for keyword in ["gate", "lift", "no", "number"]):
                                    if not gate_or_lift_label:
                                        gate_or_lift_label = cell
                                else:
                                    # Might be part of station name (e.g., "Netaji Subhash Place (L-1)")
                                    station_name = f"{station_name} {cell}".strip()
                            break
                        
                        # Find gate/lift label
                        if not gate_or_lift_label:
                            for col_idx in range(2, min(5, len(row))):
                                cell = str(row[col_idx]).strip() if col_idx < len(row) and row[col_idx] else ""
                                if cell and any(keyword in cell.lower() for keyword in ["gate", "lift", "no", "number", "main"]):
                                    gate_or_lift_label = cell
                                    break
                        
                        # Find lift availability (might be in same column as gate or separate)
                        for col_idx in range(2, min(5, len(row))):
                            cell = str(row[col_idx]).strip() if col_idx < len(row) and row[col_idx] else ""
                            if cell and "lift" in cell.lower():
                                has_lift = has_lift_availability(cell)
                                break
                        
                        # Find exit landmark (usually last column or second-to-last)
                        for col_idx in range(len(row) - 1, max(2, len(row) - 4), -1):
                            cell = str(row[col_idx]).strip() if col_idx < len(row) and row[col_idx] else ""
                            if cell and len(cell) > 5 and cell.lower() not in ["nan", "none", ""]:
                                if not exit_landmark:
                                    exit_landmark = cell
                                else:
                                    # Combine if multiple landmark columns
                                    exit_landmark = f"{cell}, {exit_landmark}"
                                break
                        
                        # Skip if station name looks like a gate label
                        if station_name and any(keyword in station_name.lower() for keyword in ["gate no", "lift no"]):
                            # This is likely a gate label, not station name
                            if not gate_or_lift_label:
                                gate_or_lift_label = station_name
                            station_name = None
                        
                        # Only add if we have at least station name and gate/lift info
                        if station_name and gate_or_lift_label and len(station_name) > 3:
                            gate_number, gate_type = extract_gate_number(gate_or_lift_label)
                            
                            gate_record = {
                                "line_name": current_line or "UNKNOWN",
                                "station_name": station_name.strip(),
                                "gate_or_lift_label": gate_or_lift_label.strip(),
                                "gate_type": gate_type or "gate",
                                "gate_number": str(gate_number) if gate_number else "",
                                "has_lift_inside_gate": has_lift,
                                "exit_landmark": exit_landmark.strip() if exit_landmark else "",
                                "notes": notes.strip() if notes else ""
                            }
                            
                            gates.append(gate_record)
                            print(f"    Extracted: {station_name} - {gate_or_lift_label}")
                    
                    except Exception as e:
                        print(f"    Error processing row {row_idx}: {e}")
                        continue
    
    print(f"\nTotal gates extracted: {len(gates)}")
    return gates

def write_csv(gates: List[Dict]):
    """Write gates data to CSV file."""
    if not gates:
        print("No gates to write!")
        return
    
    # CSV columns
    columns = [
        "line_name",
        "station_name",
        "gate_or_lift_label",
        "gate_type",
        "gate_number",
        "has_lift_inside_gate",
        "exit_landmark",
        "notes"
    ]
    
    # Remove existing CSV if it exists (idempotent)
    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)
        print(f"Removed existing CSV: {CSV_PATH}")
    
    # Write new CSV
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(gates)
    
    print(f"✅ Written {len(gates)} gate records to: {CSV_PATH}")

def main():
    """Main function to parse PDF and generate CSV."""
    print("=" * 60)
    print("DMRC Divyangjan Gates Parser")
    print("=" * 60)
    
    try:
        gates = parse_pdf()
        write_csv(gates)
        print("\n✅ Parsing complete!")
        print(f"   CSV file: {CSV_PATH}")
        print(f"   Total records: {len(gates)}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

