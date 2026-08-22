#!/usr/bin/env python3
"""
ParseBot wrapper for technical events / hackathons (e.g., Unstop listings).
Provides a helper to call ParseBot's get_all_open_events_details scraper.
"""

import os
from typing import Any, Dict

import requests
from fastapi import HTTPException
from pydantic import BaseModel

# ============================================================================
# Configuration
# ============================================================================

# Secrets come from the environment. Falls back to PARSEBOT_API_KEY since both
# scrapers historically shared one key. The old hardcoded value is compromised.
PARSEBOT_TECH_API_KEY = os.getenv(
    "PARSEBOT_TECH_API_KEY", os.getenv("PARSEBOT_API_KEY", "")
)
PARSEBOT_TECH_URL = os.getenv(
    "PARSEBOT_TECH_URL",
    "https://api.parse.bot/scraper/"
    "0603aa4e-995d-4a8c-b59b-45ad1e0ee348/get_all_open_events_details",
)


class TechnicalEventsPayload(BaseModel):
    """Request body for /api/parse-technical-events"""

    page_url: str


def call_technical_events_parsebot(page_url: str) -> Dict[str, Any]:
    """
    Send the hackathon listing page URL to ParseBot and return parsed technical events.
    """
    if not PARSEBOT_TECH_API_KEY or PARSEBOT_TECH_API_KEY == "YOUR_API_KEY_HERE":
        raise HTTPException(
            status_code=503,
            detail="Technical events are unavailable: PARSEBOT_TECH_API_KEY is not configured.",
        )

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": PARSEBOT_TECH_API_KEY,
    }
    body = {"page_url": page_url}

    try:
        response = requests.post(
            PARSEBOT_TECH_URL,
            headers=headers,
            json=body,
            timeout=60,  # Increased timeout to 60 seconds for slower responses
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call Parse.bot technical events scraper: {exc}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    try:
        return response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Parse.bot technical events returned non-JSON response: {exc}",
        )


__all__ = [
    "TechnicalEventsPayload",
    "call_technical_events_parsebot",
]

