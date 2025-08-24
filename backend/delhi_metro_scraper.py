#!/usr/bin/env python3
"""
Delhi Metro Real Scraper
Actually scrapes Delhi Metro official website for real-time data
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DelhiMetroScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Delhi Metro official URLs
        self.metro_urls = [
            "https://www.delhimetrorail.com/",
            "https://delhimetrorail.com/",
            "https://dmrc.org/"
        ]
        
        # Metro line information (base data)
        self.metro_lines = {
            "Red Line": {"route": "Dilshad Garden - Rithala", "stations": 21},
            "Yellow Line": {"route": "Samaypur Badli - HUDA City Centre", "stations": 37},
            "Blue Line": {"route": "Dwarka Sector 21 - Noida Electronic City", "stations": 50},
            "Green Line": {"route": "Inderlok - Brigadier Hoshiar Singh", "stations": 23},
            "Violet Line": {"route": "Kashmere Gate - Raja Nahar Singh", "stations": 16},
            "Pink Line": {"route": "Majlis Park - Shiv Vihar", "stations": 38},
            "Magenta Line": {"route": "Janakpuri West - Botanical Garden", "stations": 25},
            "Grey Line": {"route": "Dwarka - Dhansa Bus Stand", "stations": 9},
            "Airport Express": {"route": "New Delhi - Dwarka Sector 21", "stations": 6}
        }
    
    def scrape_metro_website(self, url: str) -> dict:
        """Scrape Delhi Metro official website"""
        try:
            logger.info(f"Scraping Delhi Metro website: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for status information
            status_info = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "title": soup.title.string if soup.title else "No title found"
            }
            
            # Look for specific status indicators
            status_text = soup.get_text().lower()
            
            # Check for operational status keywords
            operational_keywords = ["operational", "running", "normal", "regular"]
            disruption_keywords = ["disruption", "delay", "maintenance", "closed", "suspended"]
            
            operational_count = sum(1 for keyword in operational_keywords if keyword in status_text)
            disruption_count = sum(1 for keyword in disruption_keywords if keyword in status_text)
            
            if disruption_count > operational_count:
                status_info["overall_status"] = "Disruptions detected"
            else:
                status_info["overall_status"] = "Operational"
            
            # Look for alerts or announcements
            alerts = []
            
            # Common alert containers
            alert_selectors = [
                '.alert', '.announcement', '.notice', '.status',
                '[class*="alert"]', '[class*="notice"]', '[class*="status"]'
            ]
            
            for selector in alert_selectors:
                alert_elements = soup.select(selector)
                for element in alert_elements[:3]:  # Get first 3 alerts
                    alert_text = element.get_text().strip()
                    if alert_text and len(alert_text) > 10:
                        alerts.append(alert_text)
            
            status_info["alerts"] = alerts[:5]  # Keep first 5 alerts
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def scrape_all_metro_sites(self) -> dict:
        """Scrape all Delhi Metro websites"""
        logger.info("Scraping all Delhi Metro websites...")
        
        results = {}
        for url in self.metro_urls:
            try:
                result = self.scrape_metro_website(url)
                results[url] = result
                time.sleep(2)  # Be respectful to servers
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results[url] = {"error": str(e)}
        
        return results
    
    def get_metro_status(self) -> dict:
        """Get comprehensive Metro status"""
        logger.info("Getting Delhi Metro status...")
        
        # Scrape all websites
        website_results = self.scrape_all_metro_sites()
        
        # Analyze results
        operational_sites = 0
        total_alerts = []
        overall_status = "Unknown"
        
        for url, result in website_results.items():
            if "error" not in result:
                operational_sites += 1
                if result.get("overall_status") == "Operational":
                    overall_status = "Operational"
                total_alerts.extend(result.get("alerts", []))
        
        # Determine overall status
        if operational_sites == 0:
            overall_status = "Data unavailable"
        elif overall_status == "Unknown":
            overall_status = "Operational"  # Default assumption
        
        # Create comprehensive status
        metro_status = {
            "status": overall_status,
            "alerts": total_alerts[:10],  # Keep latest 10 alerts
            "last_updated": datetime.now().isoformat(),
            "websites_scraped": len(website_results),
            "operational_websites": operational_sites,
            "lines": {}
        }
        
        # Add line information
        for line_name, line_info in self.metro_lines.items():
            metro_status["lines"][line_name] = {
                "status": "Operational",  # Default status
                "route": line_info["route"],
                "stations": line_info["stations"],
                "last_checked": datetime.now().isoformat()
            }
        
        # Check for specific line disruptions in alerts
        for alert in total_alerts:
            alert_lower = alert.lower()
            for line_name in self.metro_lines.keys():
                if line_name.lower() in alert_lower:
                    if any(word in alert_lower for word in ["delay", "disruption", "maintenance", "closed"]):
                        metro_status["lines"][line_name]["status"] = "Disruption"
                        metro_status["lines"][line_name]["alert"] = alert
        
        logger.info(f"Metro status: {overall_status} with {len(total_alerts)} alerts")
        return metro_status
    
    def get_line_specific_info(self, line_name: str) -> dict:
        """Get specific information about a Metro line"""
        if line_name not in self.metro_lines:
            return {"error": "Line not found"}
        
        line_info = self.metro_lines[line_name]
        status = self.get_metro_status()
        
        return {
            "line": line_name,
            "route": line_info["route"],
            "stations": line_info["stations"],
            "status": status["lines"].get(line_name, {}).get("status", "Unknown"),
            "alert": status["lines"].get(line_name, {}).get("alert", None),
            "last_updated": status["last_updated"]
        }

# ========== TEST FUNCTION ==========
def test_metro_scraper():
    """Test the Delhi Metro scraper"""
    print("🚇 Testing Delhi Metro Real Scraper...")
    
    scraper = DelhiMetroScraper()
    
    print("\n🔍 Scraping Delhi Metro websites...")
    results = scraper.scrape_all_metro_sites()
    
    print("\n📊 Website Scraping Results:")
    for url, result in results.items():
        print(f"\nURL: {url}")
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Status: {result.get('overall_status', 'Unknown')}")
            print(f"📄 Title: {result.get('title', 'No title')}")
            print(f"🚨 Alerts: {len(result.get('alerts', []))}")
            for alert in result.get('alerts', [])[:2]:
                print(f"   - {alert[:100]}...")
    
    print("\n🚇 Getting Metro Status...")
    status = scraper.get_metro_status()
    
    print(f"\n📊 Overall Status: {status['status']}")
    print(f"🌐 Websites Scraped: {status['websites_scraped']}")
    print(f"✅ Operational Websites: {status['operational_websites']}")
    print(f"🚨 Total Alerts: {len(status['alerts'])}")
    
    print("\n🚇 Line Status:")
    for line_name, line_info in status['lines'].items():
        print(f"  - {line_name}: {line_info['status']} ({line_info['route']})")
        if 'alert' in line_info:
            print(f"    Alert: {line_info['alert'][:80]}...")
    
    print(f"\n🕐 Last Updated: {status['last_updated']}")
    print("\n✅ Delhi Metro Scraper Test Complete!")

if __name__ == "__main__":
    test_metro_scraper()
