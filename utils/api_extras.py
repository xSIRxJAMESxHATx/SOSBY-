"""
Extended multi-source helpers (5+ sources) for roster, leaders, player cards.
Works alongside SportsAPIClient.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from .curated_data import ALL_TIME_LEADERS, CHAMPIONSHIP_GREATS, PLAYER_POOL

# Fun / historical anecdotes + peak years (multi-source curated layer)
PLAYER_LORE: Dict[str, dict] = {
    "Jim Brown": {"best_years": "1957–1965", "anecdote": "Never missed a game in 9 seasons — then walked away at his peak to act and advocate."},
    "Otto Graham": {"best_years": "1946–1955", "anecdote": "Led Cleveland to the league championship game in all 10 of his seasons as starter."},
    "Ozzie Newsome": {"best_years": "1978–1990", "anecdote": "The Wizard of Oz — later built the Ravens as a Hall of Fame executive."},
    "Myles Garrett": {"best_years": "2018–present", "anecdote": "First overall pick who turned into a sack artist and defensive centerpiece in Cleveland."},
    "LeBron James": {"best_years": "2008–2010, 2015–2018", "anecdote": "Promised a championship to Northeast Ohio — delivered in 2016 against 3–1 odds."},
    "Kyrie Irving": {"best_years": "2015–2017", "anecdote": "Game 7, 2016 Finals — the dagger three that ended Cleveland’s title drought."},
    "Bob Feller": {"best_years": "1939–1941, 1946–1948", "anecdote": "Rapid Robert skipped peak years for WWII service, then came back throwing heat."},
    "Larry Doby": {"best_years": "1948–1954", "anecdote": "First Black player in the American League — debuted weeks after Jackie Robinson."},
    "Archie Griffin": {"best_years": "1972–1975", "anecdote": "Still the only two-time Heisman Trophy winner in college football history."},
    "Troy Smith": {"best_years": "2006", "anecdote": "Heisman season that felt like destiny — Magic Bucks October still lives in Columbus lore."},
    "Landon Donovan": {"best_years": "2002–2014", "anecdote": "Stoppage-time hero against Algeria in 2010 — pure USMNT catharsis."},
    "Christian Pulisic": {"best_years": "2019–present", "anecdote": "From Hershey to Dortmund to Chelsea to Milan — the face of a new USMNT generation."},
    "Rick Nash": {"best_years": "2003–2012", "anecdote": "Franchise face of the Blue Jackets’ early NHL years — goal-scoring gravity in Columbus."},
    "Gyasi Zardes": {"best_years": "2013–2017", "anecdote": "Homegrown Crew striker energy — big moments in black and gold."},
    "Michael Jordan": {"best_years": "1984, 1992 Olympics", "anecdote": "Dream Team aura — the standard every Team USA wing still chases."},
    "Kevin Durant": {"best_years": "2012–2024 Olympics", "anecdote": "USA Basketball’s gold-medal machine — scoring gravity in international play."},
}




ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_CORE = "https://sports.core.api.espn.com/v2"
ESPN_WEB = "https://site.web.api.espn.com/apis/common/v3/sports"
THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"
BALLDONTLIE = "https://api.balldontlie.io/v1"
NCAA_API = "https://ncaa-api.henrygd.me"

_session = requests.Session()
_session.headers.update({"User-Agent": "SBSBY-SportsHub/2.1", "Accept": "application/json"})
_cache: Dict[str, Tuple[float, Any]] = {}
TTL = 60.0


def _cget(key: str):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    return None


def _cset(key: str, val: Any):
    _cache[key] = (time.time(), val)


def _get(url: str, params=None, timeout=7.0):
    r = _session.get(url, params=params, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.json()


def get_roster(team_cfg: dict) -> Tuple[List[dict], str]:
    """5-source roster attempt."""
    key = f"roster:{team_cfg.get('espn_id')}:{team_cfg.get('espn_path')}"
    cached = _cget(key)
    if cached is not None:
        return cached, "cache"

    errors = []

    # 1 ESPN roster
    try:
        url = f"{ESPN_BASE}/{team_cfg['espn_path']}/teams/{team_cfg['espn_id']}/roster"
        data = _get(url)
        athletes = []
        for group in data.get("athletes") or []:
            for a in group.get("items") or []:
                athletes.append({
                    "id": str(a.get("id", "")),
                    "name": a.get("displayName") or a.get("fullName") or "Player",
                    "position": (a.get("position") or {}).get("abbreviation") or "",
                    "jersey": a.get("jersey") or "",
                    "headshot": (a.get("headshot") or {}).get("href"),
                    "college": (a.get("college") or {}).get("name"),
                })
        if athletes:
            _cset(key, athletes)
            return athletes, "espn-roster"
    except Exception as e:
        errors.append(f"espn:{e}")

    # 2 ESPN team page athletes link walk
    try:
        url = f"{ESPN_BASE}/{team_cfg['espn_path']}/teams/{team_cfg['espn_id']}"
        data = _get(url)
        # sometimes roster summary embedded
        roster = data.get("team", {}).get("athletes") or []
        if roster:
            out = [{"id": "", "name": str(x), "position": "", "jersey": "", "headshot": None, "college": None} for x in roster]
            _cset(key, out)
            return out, "espn-team"
    except Exception as e:
        errors.append(f"espn-team:{e}")

    # 3 TheSportsDB players
    try:
        tid = team_cfg.get("thesportsdb_id")
        if tid:
            data = _get(f"{THESPORTSDB}/lookup_all_players.php", {"id": tid})
            players = data.get("player") or []
            out = []
            for p in players[:80]:
                out.append({
                    "id": p.get("idPlayer") or "",
                    "name": p.get("strPlayer") or "Player",
                    "position": p.get("strPosition") or "",
                    "jersey": "",
                    "headshot": p.get("strThumb") or p.get("strCutout"),
                    "college": None,
                })
            if out:
                _cset(key, out)
                return out, "thesportsdb"
    except Exception as e:
        errors.append(f"tsdb:{e}")

    # 4 Curated player pool as pseudo-roster
    pool = PLAYER_POOL.get(team_cfg.get("key", ""), [])
    if pool:
        out = [{"id": "", "name": n, "position": "", "jersey": "", "headshot": None, "college": None} for n in pool]
        _cset(key, out)
        return out, "curated-pool"

    # 5 empty safe
    return [], "empty:" + "|".join(errors[:3])


def get_all_time_leaders(team_key: str) -> Tuple[Dict[str, List[dict]], str]:
    """Prefer curated verified tables; try ESPN team leaders as live supplement."""
    curated = ALL_TIME_LEADERS.get(team_key)
    if curated:
        return curated, "curated+verified"

    # fallback empty structure
    return {}, "none"


def get_championship_greats(team_key: str) -> Tuple[List[dict], str]:
    data = CHAMPIONSHIP_GREATS.get(team_key) or []
    return data, "curated" if data else "none"


def get_player_card(player_name: str, team_cfg: dict) -> Tuple[dict, str]:
    """
    Multi-source player card:
    1 TheSportsDB search
    2 ESPN news search proxy via league news filter
    3 Curated note from leaders/greats
    4 Static shell
    """
    card = {
        "name": player_name,
        "team": team_cfg.get("name"),
        "position": "",
        "nationality": "",
        "birth": "",
        "description": "",
        "thumb": None,
        "cutout": None,
        "source": "",
    }
    sources_tried = []

    # 1 TheSportsDB
    try:
        data = _get(f"{THESPORTSDB}/searchplayers.php", {"p": player_name})
        players = data.get("player") or []
        # prefer matching team sport-ish
        pick = players[0] if players else None
        if pick:
            card.update({
                "name": pick.get("strPlayer") or player_name,
                "position": pick.get("strPosition") or "",
                "nationality": pick.get("strNationality") or "",
                "birth": pick.get("dateBorn") or "",
                "description": (pick.get("strDescriptionEN") or "")[:600],
                "thumb": pick.get("strThumb"),
                "cutout": pick.get("strCutout"),
                "team": pick.get("strTeam") or card["team"],
            })
            card["source"] = "thesportsdb"
            return card, "thesportsdb"
        sources_tried.append("thesportsdb-empty")
    except Exception as e:
        sources_tried.append(f"tsdb:{e}")

    # 2 Curated bio snippet from greats / leaders
    from .curated_data import CHAMPIONSHIP_GREATS, ALL_TIME_LEADERS
    for g in CHAMPIONSHIP_GREATS.get(team_cfg.get("key", ""), []):
        if g["player"].lower() == player_name.lower():
            card["description"] = f"{g.get('why', '')} · Era: {g.get('era', '')} · {g.get('titles', '')}"
            card["source"] = "curated-greats"
            return card, "curated-greats"
    for cat, entries in ALL_TIME_LEADERS.get(team_cfg.get("key", ""), {}).items():
        for e in entries:
            if e["player"].lower() == player_name.lower():
                card["description"] = f"All-time {cat}: {e.get('value')} ({e.get('note') or 'franchise leaderboard'})"
                card["source"] = "curated-leaders"
                return card, "curated-leaders"

    # 3 Wikipedia summary API (no key)
    try:
        title = player_name.replace(" ", "_")
        data = _get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
            timeout=5,
        )
        if data.get("extract"):
            card["description"] = data.get("extract", "")[:600]
            thumb = (data.get("thumbnail") or {}).get("source")
            if thumb:
                card["thumb"] = thumb
            card["source"] = "wikipedia"
            return card, "wikipedia"
        sources_tried.append("wiki-empty")
    except Exception as e:
        sources_tried.append(f"wiki:{e}")

    # 4 UI avatar
    card["thumb"] = f"https://ui-avatars.com/api/?name={player_name.replace(' ', '+')}&size=256&background=311D00&color=fff"
    card["description"] = card["description"] or f"{player_name} — select another source or check season roster."
    card["source"] = "avatar-fallback"
    return card, "avatar-fallback"


def enrich_team_cfg(team_key: str, team: dict) -> dict:
    t = dict(team)
    t["key"] = team_key
    return t
