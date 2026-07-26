"""
TheSportsDB GraphQL investigation
=================================
Official TheSportsDB exposes **REST (v1 JSON / v2 premium)** only.
There is **no official GraphQL** endpoint as of 2026.

Community projects have wrapped REST in GraphQL (e.g. archived
jsBlackBelt/TheSportsDB Apollo server) — those require you to host
the wrapper yourself and still hit REST upstream.

This module:
  - Documents the finding
  - Provides a tiny optional GraphQL client hook (SPORTSDB_GRAPHQL_URL)
  - Falls back to REST helpers used by api_client

Typical REST event fields (schema-ish):
  idEvent, strEvent, dateEvent, strTime,
  strHomeTeam, strAwayTeam, intHomeScore, intAwayScore,
  strStatus, strProgress, strVenue, strHomeTeamBadge, strAwayTeamBadge
"""
from __future__ import annotations
import os
from typing import Any, Dict, Optional

import requests

REST_BASE = "https://www.thesportsdb.com/api/v1/json/123"


def graphql_configured() -> bool:
    return bool((os.environ.get("SPORTSDB_GRAPHQL_URL") or "").strip())


def graphql_query(query: str, variables: Optional[dict] = None) -> Optional[dict]:
    """POST to a self-hosted GraphQL wrapper if SPORTSDB_GRAPHQL_URL is set."""
    url = (os.environ.get("SPORTSDB_GRAPHQL_URL") or "").strip()
    if not url:
        return None
    try:
        r = requests.post(
            url,
            json={"query": query, "variables": variables or {}},
            timeout=8,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


def rest_team_next_events(team_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{REST_BASE}/eventsnext.php", params={"id": team_id}, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def rest_team_last_events(team_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{REST_BASE}/eventslast.php", params={"id": team_id}, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None
