"""
MaxPreps integration (best-effort).

MaxPreps does not publish a free official public API.
- Third-party scrapers/APIs (e.g. Parse.bot) require paid keys.
- Internal gateway URLs change and may block bots.

This module:
1) Tries polite search-page discovery for a school URL
2) Returns structured link rows for schedules/scores
3) Uses tenacity exponential backoff on HTTP attempts

Never scrape behind logins or violate ToS aggressively.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SOSBY-SportsHub/3.4 (educational; +https://share.streamlit.io)",
    "Accept": "text/html,application/json",
})

# Known school search patterns
SEARCH_URL = "https://www.maxpreps.com/search/default.aspx?type=school&search={q}&state={st}&or=name"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.4, max=4.0),
    retry=retry_if_exception_type((requests.RequestException,)),
    reraise=True,
)
def _get(url: str, timeout: float = 8.0) -> requests.Response:
    resp = SESSION.get(url, timeout=timeout)
    if resp.status_code == 429:
        raise requests.RequestException("MaxPreps rate limited")
    if resp.status_code >= 500:
        raise requests.RequestException(f"MaxPreps server {resp.status_code}")
    return resp


def school_search_links(school: str, state: str = "oh", sport_hint: str = "") -> List[dict]:
    """Return navigable MaxPreps / related links for a high school program."""
    q = quote_plus(school)
    st = (state or "oh").lower()
    sport_q = quote_plus(f"{school} {sport_hint}".strip())
    links = [
        {
            "name": f"MaxPreps search: {school}",
            "url": SEARCH_URL.format(q=q, st=st),
            "source": "maxpreps-search",
        },
        {
            "name": f"MaxPreps Google: {school} {sport_hint}".strip(),
            "url": f"https://www.google.com/search?q=site:maxpreps.com+{sport_q}",
            "source": "maxpreps-google",
        },
    ]
    # Optional: hit search page to extract first school path (best-effort)
    try:
        r = _get(SEARCH_URL.format(q=q, st=st))
        if r.status_code == 200 and r.text:
            # look for /oh/ school paths
            found = re.findall(r'href="(https://www\.maxpreps\.com/[^"]+)"', r.text)
            for href in found[:5]:
                if "/oh/" in href or school.split()[0].lower() in href.lower():
                    links.insert(0, {
                        "name": "MaxPreps school page",
                        "url": href.split("?")[0],
                        "source": "maxpreps-html",
                    })
                    break
    except Exception:
        pass
    return links


def as_schedule_rows(school: str, state: str = "oh", sport_hint: str = "") -> List[dict]:
    rows = []
    for item in school_search_links(school, state, sport_hint):
        rows.append({
            "id": item["url"],
            "name": item["name"],
            "date": "",
            "status": "MaxPreps",
            "status_state": "pre",
            "detail": item["url"],
            "home_team": school,
            "home_score": "–",
            "away_team": sport_hint or "HS",
            "away_score": "–",
            "venue": "",
            "broadcast": None,
            "source": item.get("source") or "maxpreps",
        })
    return rows


def as_standings_rows(school: str, state: str = "oh", sport_hint: str = "") -> List[dict]:
    rows = [{
        "Team": school,
        "W": "—",
        "L": "—",
        "PCT": "—",
        "GB": "—",
        "STRK": f"MaxPreps / {sport_hint or 'HS'}",
    }]
    for item in school_search_links(school, state, sport_hint):
        rows.append({
            "Team": item["name"],
            "W": "link",
            "L": "",
            "PCT": "",
            "GB": "",
            "STRK": item["url"],
        })
    return rows
