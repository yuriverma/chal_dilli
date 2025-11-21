#!/usr/bin/env python3
"""
ParseBot URL Wrapper (with Playwright)

A FastAPI service that:
1. Accepts a URL
2. Uses Playwright (headless Chromium) to fetch fully rendered HTML
3. Sends that HTML to Parse.bot's parse_events_from_html endpoint
4. Returns the parsed events (optionally with debug info)

Quick start:

1. Install dependencies:

   pip install fastapi uvicorn requests playwright
   playwright install chromium

2. Set your ParseBot API key in PARSEBOT_API_KEY below.

3. Run the server:

   uvicorn parsebot_from_url:app --reload --port 8000

4. Test with curl:

   curl -X POST http://localhost:8000/api/parse-events-from-url \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://in.bookmyshow.com/events/rambo-circus/ET00332998",
       "debug": true
     }'
"""

import time
from typing import Any, Dict, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Optional Playwright import - will fail gracefully if not installed
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None

# ============================================================================
# Configuration
# ============================================================================

# TODO: put your real ParseBot API key here
PARSEBOT_API_KEY = "cbd3aaa1-7c92-4e8a-9f4e-17e857ff3845"
PARSEBOT_URL = (
    "https://api.parse.bot/scraper/"
    "8316d1dd-be67-469a-9aa4-708ac5172714/parse_events_from_html"
)

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="ParseBot URL Wrapper")

# ============================================================================
# Request Models
# ============================================================================


class UrlPayload(BaseModel):
    """Request body for /api/parse-events-from-url"""

    url: str
    debug: Optional[bool] = False


# ============================================================================
# Helper Functions
# ============================================================================


def fetch_full_html(url: str, max_retries: int = 2) -> str:
    """
    Use Playwright to fetch fully rendered HTML (including JS execution).

    This helps bypass basic bot protections like Cloudflare that block
    plain HTTP clients such as `requests`.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts (default: 2)
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Playwright is not installed. Please install it with: pip install playwright && playwright install chromium",
        )
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()
                
                # Try "load" first (more reliable than networkidle for sites with continuous activity)
                # If that fails, fall back to "domcontentloaded"
                try:
                    page.goto(url, wait_until="load", timeout=90_000)  # 90 seconds
                except Exception as load_error:
                    # Fallback: try with domcontentloaded (faster, less strict)
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
                    except Exception as dom_error:
                        # Last resort: just navigate without waiting
                        page.goto(url, timeout=90_000)
                
                # Wait a bit for any dynamic content to load
                page.wait_for_timeout(2000)  # 2 seconds
                
                html = page.content()
                browser.close()
                
                # Verify we got some content
                if html and len(html) > 100:
                    return html
                else:
                    raise Exception("Page content is too short or empty")
                    
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** attempt)
                continue
            else:
                # All retries exhausted
                raise HTTPException(
                    status_code=502,
                    detail=f"Playwright error while fetching URL after {max_retries + 1} attempts: {str(last_error)}. The site may be slow or blocking requests.",
                )
    
    # Should never reach here, but just in case
    raise HTTPException(
        status_code=502,
        detail=f"Failed to fetch URL: {str(last_error)}",
    )


def call_parsebot(html: str, debug: bool = False) -> Dict[str, Any]:
    """
    Send HTML content to Parse.bot API and return parsed events.

    Args:
        html: HTML content string to send
        debug: If True, include debug information in response

    Returns:
        If debug=False: parsed JSON from Parse.bot
        If debug=True: dict with parsebot_status, parsebot_json, parsebot_text_sample, and debug info
    """
    if not PARSEBOT_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="PARSEBOT_API_KEY is not set in parsebot_from_url.py",
        )

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": PARSEBOT_API_KEY,
    }
    body = {"html_content": html}

    try:
        response = requests.post(
            PARSEBOT_URL,
            headers=headers,
            json=body,
            timeout=60,  # Increased timeout to 60 seconds for slower responses
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call Parse.bot: {str(exc)}",
        )

    if response.status_code != 200:
        # Forward ParseBot's error
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    try:
        parsed_json = response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Parse.bot returned non-JSON response: {str(exc)}",
        )

    if debug:
        return {
            "parsebot_status": response.status_code,
            "parsebot_json": parsed_json,
            "parsebot_text_sample": response.text[:2000],
            "debug": {
                "html_length": len(html),
                "html_head_sample": html[:500],
            },
        }

    # When debug=False, just return the parsed JSON (contains `events` and `count`)
    return parsed_json


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"ok": True}


@app.post("/api/parse-events-from-url")
def parse_events_from_url(payload: UrlPayload) -> Dict[str, Any]:
    """
    Fetch HTML from URL (via Playwright) and send to Parse.bot for event extraction.

    Steps:
    1. Fetch the page HTML using a real browser (Playwright)
    2. Send HTML to Parse.bot parse_events_from_html endpoint
    3. Return parsed events (with optional debug info)
    """
    # Step 1: Fetch fully rendered HTML
    html = fetch_full_html(payload.url)

    # Step 2: Send HTML to Parse.bot and return result
    return call_parsebot(html, bool(payload.debug))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("parsebot_from_url:app", host="0.0.0.0", port=8000, reload=True)
