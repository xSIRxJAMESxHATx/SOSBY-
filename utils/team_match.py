"""Strict team matching — ESPN id first, distinctive name tokens second."""
from __future__ import annotations
from typing import Dict, List

GENERIC_BLOCKLIST = {
    "football", "basketball", "baseball", "soccer", "hockey", "track",
    "field", "team", "sports", "university", "college", "boys", "girls",
    "mens", "men's", "women", "women's", "varsity", "high", "school",
    "club", "fc", "sc", "united", "city", "the", "and", "game", "match",
    "osu", "state", "ohio",  # too broad alone for CFB scoreboard
}


def match_tokens(team: dict) -> List[str]:
    tokens: List[str] = []
    for k in ("search_name", "odds_team", "short", "name", "mascot"):
        v = (team.get(k) or "").lower().strip()
        if not v:
            continue
        if len(v) > 2 and v not in GENERIC_BLOCKLIST and v not in tokens:
            tokens.append(v)
        for part in v.replace("-", " ").replace("/", " ").split():
            if len(part) > 2 and part not in GENERIC_BLOCKLIST and part not in tokens:
                tokens.append(part)
    # Prefer longer / more specific tokens first
    tokens.sort(key=lambda x: (-len(x), x))
    return tokens


def game_involves_team(game: dict, team: dict, espn_id: str = "") -> bool:
    blob = f"{game.get('name','')} {game.get('home_team','')} {game.get('away_team','')}".lower()
    tid = str(espn_id or team.get("espn_id") or "")
    tokens = match_tokens(team)
    # Strong name evidence
    if tokens and any(tok in blob for tok in tokens[:4]):
        return True
    short = (team.get("short") or "").lower()
    if short and len(short) > 3 and short in blob:
        return True
    return False
