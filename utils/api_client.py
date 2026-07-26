"""
SBSBY multi-source sports client — production grade.
Primary: ESPN public endpoints
Fallbacks: TheSportsDB
Optional: The Odds API (ODDS_API_KEY in secrets / env)
Intelligent retries, short TTL cache, graceful missing-data handling.
"""

from __future__ import annotations
import re

import os
import time
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ---------------------------------------------------------------------------
# Team configuration
# ---------------------------------------------------------------------------

TEAMS: Dict[str, dict] = {
    "browns": {
        "name": "Cleveland Browns",
        "short": "Browns",
        "search_name": "Cleveland Browns",
        "sport": "football",
        "league": "nfl",
        "espn_id": "5",
        "espn_path": "football/nfl",
        "thesportsdb_id": "134920",
        "odds_sport_key": "americanfootball_nfl",
        "odds_team": "Cleveland Browns",
        "colors": {
            "primary": "#311D00",
            "secondary": "#FF3C00",
            "accent": "#FFFFFF",
            "light_bg": "#FDF6F0",
            "light_card": "#FFF8F3",
            "dark_bg": "#1A1208",
            "dark_card": "#2A1F12",
        },
        "prediction_query": "Cleveland Browns",
    },
    "guardians": {
        "name": "Cleveland Guardians",
        "short": "Guardians",
        "sport": "baseball",
        "league": "mlb",
        "espn_id": "5",
        "espn_path": "baseball/mlb",
        "thesportsdb_id": "135269",
        "odds_sport_key": "baseball_mlb",
        "odds_team": "Cleveland Guardians",
        "colors": {
            "primary": "#0C2340",
            "secondary": "#E31937",
            "accent": "#FFFFFF",
            "light_bg": "#F0F4F8",
            "light_card": "#F8FBFD",
            "dark_bg": "#0A1520",
            "dark_card": "#122030",
        },
        "prediction_query": "Cleveland Guardians",
    },
    "cavaliers": {
        "name": "Cleveland Cavaliers",
        "short": "Cavaliers",
        "sport": "basketball",
        "league": "nba",
        "espn_id": "5",
        "espn_path": "basketball/nba",
        "thesportsdb_id": "134880",
        "odds_sport_key": "basketball_nba",
        "odds_team": "Cleveland Cavaliers",
        "colors": {
            "primary": "#860038",
            "secondary": "#FDBB30",
            "accent": "#041E42",
            "light_bg": "#FDF5F7",
            "light_card": "#FFF9FB",
            "dark_bg": "#1A0A12",
            "dark_card": "#2A1220",
        },
        "prediction_query": "Cleveland Cavaliers",
    },
    "osu_football": {
        "name": "Ohio State Buckeyes Football",
        "short": "Buckeyes",
        "search_name": "Ohio State Buckeyes",
        "sport": "football",
        "league": "college-football",
        "espn_id": "194",
        "espn_path": "football/college-football",
        "thesportsdb_id": "134940",
        "odds_sport_key": "americanfootball_ncaaf",
        "odds_team": "Ohio State",
        "colors": {
            "primary": "#BB0000",
            "secondary": "#666666",
            "accent": "#FFFFFF",
            "light_bg": "#FDF5F5",
            "light_card": "#FFF8F8",
            "dark_bg": "#1A0808",
            "dark_card": "#2A1010",
        },
        "prediction_query": "Ohio State Football",
    },
    "osu_mbb": {
        "name": "Ohio State Buckeyes Men's Basketball",
        "short": "OSU Men's BB",
        "sport": "basketball",
        "league": "mens-college-basketball",
        "espn_id": "194",
        "espn_path": "basketball/mens-college-basketball",
        "thesportsdb_id": "134941",
        "odds_sport_key": "basketball_ncaab",
        "odds_team": "Ohio State",
        "colors": {
            "primary": "#BB0000",
            "secondary": "#666666",
            "accent": "#FFFFFF",
            "light_bg": "#FDF5F5",
            "light_card": "#FFF8F8",
            "dark_bg": "#1A0808",
            "dark_card": "#2A1010",
        },
        "prediction_query": "Ohio State Basketball",
    },
    "crew": {
        "name": "Columbus Crew",
        "short": "Crew",
        "sport": "soccer",
        "league": "usa.1",
        "espn_id": "183",
        "espn_path": "soccer/usa.1",
        "thesportsdb_id": "134981",
        "odds_sport_key": "soccer_usa_mls",
        "odds_team": "Columbus Crew",
        "colors": {
            "primary": "#000000",
            "secondary": "#FFED00",
            "accent": "#FFFFFF",
            "light_bg": "#FFFEF5",
            "light_card": "#FFFEF8",
            "dark_bg": "#12120A",
            "dark_card": "#1F1F12",
        },
        "prediction_query": "Columbus Crew",
    },
    "bluejackets": {
        "name": "Columbus Blue Jackets",
        "short": "Blue Jackets",
        "sport": "hockey",
        "league": "nhl",
        "espn_id": "29",
        "espn_path": "hockey/nhl",
        "thesportsdb_id": "134863",
        "odds_sport_key": "icehockey_nhl",
        "odds_team": "Columbus Blue Jackets",
        "colors": {
            "primary": "#002654",
            "secondary": "#CE1126",
            "accent": "#A2AAAD",
            "light_bg": "#F0F4F8",
            "light_card": "#F7FAFC",
            "dark_bg": "#0A1520",
            "dark_card": "#122030",
        },
        "prediction_query": "Columbus Blue Jackets",
    },
    "usmnt": {
        "name": "US Men's National Team Soccer",
        "short": "USMNT",
        "sport": "soccer",
        "league": "fifa.world",
        "espn_id": "660",
        "espn_path": "soccer/fifa.world",
        "thesportsdb_id": "135508",
        "odds_sport_key": "soccer_fifa_world_cup",
        "odds_team": "USA",
        "colors": {
            "primary": "#002868",
            "secondary": "#BF0A30",
            "accent": "#FFFFFF",
            "light_bg": "#F5F7FB",
            "light_card": "#FAFBFD",
            "dark_bg": "#0A1020",
            "dark_card": "#121A30",
        },
        "prediction_query": "USMNT USA soccer",
    },
    "usab": {
        "name": "USA Men's Basketball",
        "short": "Team USA BB",
        "sport": "basketball",
        "league": "mens-olympic-basketball",
        "espn_id": "1",
        "espn_path": "basketball/mens-olympic-basketball",
        "thesportsdb_id": "135500",
        "odds_sport_key": "basketball_nba",
        "odds_team": "USA",
        "colors": {
            "primary": "#002868",
            "secondary": "#BF0A30",
            "accent": "#FFFFFF",
            "light_bg": "#F5F7FB",
            "light_card": "#FAFBFD",
            "dark_bg": "#0A1020",
            "dark_card": "#121A30",
        },
        "prediction_query": "Team USA basketball",
    },
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"  # free tier key; 30 req/min
ODDS_API_BASE = "https://api.the-odds-api.com/v4"


class APIError(Exception):
    pass


GENERIC_MATCH_BLOCKLIST = {
    "football", "basketball", "baseball", "soccer", "hockey", "track",
    "field", "team", "sports", "university", "college", "boys", "girls",
    "mens", "men's", "women", "women's", "varsity", "high", "school",
    "club", "fc", "sc", "united", "city", "the", "and", "game", "match",
    "osu",  # too short / ambiguous alone
}


def team_match_tokens(team: dict) -> list:
    """Delegate to utils.team_match for a single source of truth."""
    try:
        from .team_match import match_tokens
        return match_tokens(team)
    except Exception:
        return []


def _safe_get(d: Any, *keys, default=None):

    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


REDDIT_SUBS = {
    "browns": "https://www.reddit.com/r/Browns/",
    "guardians": "https://www.reddit.com/r/ClevelandGuardians/",
    "cavaliers": "https://www.reddit.com/r/clevelandcavs/",
    "osu_football": "https://www.reddit.com/r/OhioStateFootball/",
    "osu_mbb": "https://www.reddit.com/r/OhioStateBasketball/",
    "crew": "https://www.reddit.com/r/columbuscrew/",
    "bluejackets": "https://www.reddit.com/r/BlueJackets/",
    "usmnt": "https://www.reddit.com/r/ussoccer/",
    "usab": "https://www.reddit.com/r/usabasketball/",
}


def reddit_url(team_key: str) -> str:
    return REDDIT_SUBS.get(team_key) or (
        "https://www.reddit.com/search/?q=" + quote_plus(
            (TEAMS.get(team_key) or {}).get("name") or team_key
        )
    )


# Local-only cards for programs without stable ESPN IDs
LOCAL_PROGRAMS = {
}


def local_program_rows(team_key: str, kind: str = "schedule") -> List[dict]:
    prog = LOCAL_PROGRAMS.get(team_key) or {}
    label = prog.get("label") or team_key
    note = prog.get("note") or ""
    sport_hint = ""
    if "football" in team_key:
        sport_hint = "football"
    elif "mbb" in team_key or "basketball" in team_key:
        sport_hint = "basketball"
    elif "tf" in team_key or "track" in team_key:
        sport_hint = "track"

    # MaxPreps enrichment for OH high schools
    mp_rows: List[dict] = []
    if False:  # HS programs removed
        try:
            from .maxpreps import as_schedule_rows, as_standings_rows
            if kind == "standings":
                mp_rows = as_standings_rows("Reynoldsburg", "oh", sport_hint)
            else:
                mp_rows = as_schedule_rows("Reynoldsburg", "oh", sport_hint)
        except Exception:
            mp_rows = []

    if kind == "standings":
        base = [{
            "Team": label,
            "W": "—",
            "L": "—",
            "PCT": "—",
            "GB": "—",
            "STRK": note[:80] or "Local program",
        }] + [
            {"Team": name, "W": "link", "L": "", "PCT": "", "GB": "", "STRK": url}
            for name, url in (prog.get("links") or [])
        ]
        # merge maxpreps standings links (skip duplicate Team header)
        for r in mp_rows:
            if r.get("Team") and r.get("Team") != label:
                base.append(r)
        return base

    rows = [{
        "id": f"local-{team_key}",
        "name": label,
        "date": "",
        "status": "Program hub",
        "status_state": "pre",
        "detail": note,
        "home_team": label,
        "home_score": "–",
        "away_team": "See links",
        "away_score": "–",
        "venue": "",
        "broadcast": None,
        "source": "local-program",
    }]
    for name, url in (prog.get("links") or []):
        rows.append({
            "id": url,
            "name": name,
            "date": "",
            "status": "Link",
            "status_state": "pre",
            "detail": url,
            "home_team": name,
            "home_score": "–",
            "away_team": "Open",
            "away_score": "–",
            "venue": "",
            "broadcast": None,
            "source": "local-program",
        })
    for r in mp_rows:
        rows.append(r)
    return rows


# Caching strategy
# - Memory dict with per-key TTL (live scores short, schedule/standings longer)
# - Disk JSON under .data/http_cache for cross-rerun reuse
# - Empty score/schedule results get short negative TTL only
# - clear_cache() wipes memory + disk

class SportsAPIClient:

    """Multi-source client: memory + disk cache, exponential backoff, throttle."""

    def __init__(self, timeout: float = 7.0, cache_ttl: float = 45.0):
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.live_cache_ttl = 15.0
        self.schedule_ttl = 180.0
        self.standings_ttl = 300.0
        self.news_ttl = 120.0
        self._min_interval = 0.4
        self._last_request_ts = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SOSBY-SportsHub/3.4 (+https://share.streamlit.io)",
                "Accept": "application/json",
            }
        )
        # memory: key -> (ts, data, ttl)
        self._cache: Dict[str, Tuple[float, Any, float]] = {}
        self.odds_api_key = (
            os.environ.get("ODDS_API_KEY")
            or os.environ.get("THE_ODDS_API_KEY")
            or ""
        )

    def _get_cached(self, key: str) -> Optional[Any]:
        hit = self._cache.get(key)
        if hit:
            ts, data, ttl = hit
            if (time.time() - ts) < ttl:
                return data
        # redis layer (optional)
        try:
            from .redis_cache import redis_get
            data = redis_get(key)
            if data is not None:
                self._cache[key] = (time.time(), data, self.cache_ttl)
                return data
        except Exception:
            pass
        # disk layer
        try:
            from .disk_cache import disk_get
            disk_ttl = self.schedule_ttl
            if key.startswith("sb:"):
                disk_ttl = self.live_cache_ttl
            elif key.startswith("std:"):
                disk_ttl = self.standings_ttl
            elif key.startswith("news:"):
                disk_ttl = self.news_ttl
            data = disk_get(key, disk_ttl)
            if data is not None:
                self._cache[key] = (time.time(), data, disk_ttl)
                return data
        except Exception:
            pass
        return None

    def _set_cache(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        use_ttl = float(ttl if ttl is not None else self.cache_ttl)
        self._cache[key] = (time.time(), data, use_ttl)
        try:
            from .redis_cache import redis_set
            redis_set(key, data, use_ttl)
        except Exception:
            pass
        try:
            from .disk_cache import disk_set
            disk_set(key, data)
        except Exception:
            pass

    def clear_cache(self) -> None:
        self._cache.clear()
        try:
            from .redis_cache import redis_clear_prefix
            redis_clear_prefix()
        except Exception:
            pass
        try:
            from .disk_cache import disk_clear
            disk_clear()
        except Exception:
            pass

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_ts
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_ts = time.time()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.6, min=0.5, max=8.0),
        retry=retry_if_exception_type((requests.RequestException, APIError)),
        reraise=True,
    )
    def _request(self, url: str, params: Optional[dict] = None) -> Any:
        """HTTP GET with throttle + exponential backoff (tenacity)."""
        self._throttle()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}") from e
        if resp.status_code == 429:
            # explicit backoff before tenacity also retries
            time.sleep(2.0)
            raise APIError(f"Rate limited: {url}")
        if resp.status_code >= 500:
            raise APIError(f"Server {resp.status_code}: {url}")
        if resp.status_code >= 400:
            # don't retry most 4xx except 429
            raise APIError(f"HTTP {resp.status_code}: {url}")
        try:
            return resp.json()
        except ValueError as e:
            raise APIError(f"Bad JSON from {url}") from e

    def _try_sources(
        self,
        sources: List[Tuple[str, Callable[[], Any]]],
        cache_key: str,
        allow_empty: bool = True,
        ttl: Optional[float] = None,
    ) -> Tuple[Any, str]:
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached, "cache"

        errors: List[str] = []
        for name, fn in sources:
            try:
                data = fn()
                if data is None:
                    errors.append(f"{name}: empty")
                    continue
                if not allow_empty and (data == [] or data == {}):
                    errors.append(f"{name}: empty payload")
                    continue
                use_ttl = ttl
                if use_ttl is None:
                    if cache_key.startswith("sb:"):
                        try:
                            live = any(
                                (g.get("status_state") or "") == "in"
                                for g in (data if isinstance(data, list) else [])
                            )
                            use_ttl = self.live_cache_ttl if live else self.cache_ttl
                        except Exception:
                            use_ttl = self.cache_ttl
                    elif cache_key.startswith("sch:"):
                        use_ttl = self.schedule_ttl
                    elif cache_key.startswith("std:"):
                        use_ttl = self.standings_ttl
                    elif cache_key.startswith("news:"):
                        use_ttl = self.news_ttl
                    else:
                        use_ttl = self.cache_ttl
                self._set_cache(cache_key, data, use_ttl)
                return data, name
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                continue

        empty: Any = []
        # short negative cache only — avoid sticky blanks for scores/schedule
        neg_ttl = 8.0 if cache_key.startswith(("sb:", "sch:")) else 20.0
        self._set_cache(cache_key, empty, neg_ttl)
        return empty, "none:" + ";".join(errors[:3])


    def _norm_espn_event(self, ev: dict) -> dict:
        """Normalize ESPN event (scoreboard or team schedule) to common shape."""
        if not isinstance(ev, dict):
            return {
                "id": None, "name": "Game", "date": "", "status": "Scheduled",
                "status_state": "pre", "detail": "", "home_team": "Home", "home_score": "–",
                "away_team": "Away", "away_score": "–", "venue": "", "broadcast": None,
                "source": "espn",
            }
        comp = (ev.get("competitions") or [{}])[0] or {}
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        if not home and len(competitors) >= 2:
            # fallback order
            away = competitors[0]
            home = competitors[1]
        status = _safe_get(ev, "status", "type", default={}) or {}
        if not status:
            status = _safe_get(comp, "status", "type", default={}) or {}
        state = (status.get("state") or "pre").lower()
        # scores
        def _score(c):
            try:
                from .scorecard import format_score
                return format_score(c.get("score"))
            except Exception:
                s = c.get("score")
                if isinstance(s, dict):
                    s = s.get("displayValue") or s.get("value")
                return "–" if s is None or s == "" else str(s)
        venue = _safe_get(comp, "venue", "fullName") or _safe_get(ev, "venue", "fullName") or ""
        broadcasts = []
        for b in (comp.get("broadcasts") or []):
            name = _safe_get(b, "media", "shortName") or b.get("name")
            if name:
                broadcasts.append(str(name))
        # geo / notes
        odds_list = comp.get("odds") or []
        line = None
        if odds_list:
            o = odds_list[0]
            line = {
                "provider": _safe_get(o, "provider", "name"),
                "spread": o.get("details"),
                "over_under": o.get("overUnder"),
            }
        return {
            "id": ev.get("id"),
            "name": ev.get("name") or ev.get("shortName") or "Game",
            "date": ev.get("date") or "",
            "status": status.get("description") or status.get("detail") or "Scheduled",
            "status_state": state,
            "detail": status.get("detail") or status.get("shortDetail") or "",
            "home_team": _safe_get(home, "team", "displayName", default="Home") or "Home",
            "home_score": _score(home),
            "home_logo": _safe_get(home, "team", "logo") or _safe_get(home, "team", "logos", 0, "href"),
            "away_team": _safe_get(away, "team", "displayName", default="Away") or "Away",
            "away_score": _score(away),
            "away_logo": _safe_get(away, "team", "logo"),
            "venue": venue or "",
            "broadcast": ", ".join(broadcasts) if broadcasts else None,
            "odds": line,
            "source": "espn",
        }

    def _norm_tsdb_event(self, e: dict) -> dict:
        """Normalize TheSportsDB event."""
        try:
            from .scorecard import format_score as _fs
        except Exception:
            def _fs(v):
                return "–" if v is None or v == "" else str(v)
        e = e or {}
        home_s = e.get("intHomeScore")
        away_s = e.get("intAwayScore")
        status = e.get("strStatus") or "Scheduled"
        state = "pre"
        st_l = str(status).lower()
        if home_s is not None and away_s is not None and str(home_s) != "" and str(away_s) != "":
            state = "post"
            if "final" not in st_l:
                status = "Final"
        date = e.get("dateEvent") or ""
        time = e.get("strTime") or ""
        if date and time and "T" not in date:
            date = f"{date}T{time}"
        return {
            "id": e.get("idEvent"),
            "name": e.get("strEvent") or f"{e.get('strAwayTeam','')} @ {e.get('strHomeTeam','')}",
            "date": date,
            "status": status,
            "status_state": state,
            "detail": e.get("strTime") or e.get("strVenue") or "",
            "home_team": e.get("strHomeTeam") or "Home",
            "home_score": _fs(home_s),
            "home_logo": e.get("strHomeTeamBadge"),
            "away_team": e.get("strAwayTeam") or "Away",
            "away_score": _fs(away_s),
            "away_logo": e.get("strAwayTeamBadge"),
            "venue": e.get("strVenue") or "",
            "broadcast": e.get("strCountry") or None,
            "source": "thesportsdb",
        }

    def get_scoreboard(
        self, team_key: str, date: Optional[str] = None
    ) -> Tuple[List[dict], str]:
        """
        Aggregate multi-source games, then pick:
          live → today → last final + next upcoming
        Never sticky-cache empty scoreboards.
        """
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sb:{team_key}:{date or 'today'}:v7"

        cached = self._get_cached(cache_key)
        if cached is not None and cached != []:
            return cached, "cache"

        if team.get("hs") and team_key in LOCAL_PROGRAMS and not team.get("espn_id"):
            rows = local_program_rows(team_key, "schedule")
            self._set_cache(cache_key, rows, self.cache_ttl)
            return rows, "local-program"

        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")
        short = (team.get("short") or "").lower()
        name_l = (team.get("name") or "").lower()
        sources_used: List[str] = []
        pool: List[dict] = []

        def _parse_date(g: dict) -> str:
            return (g.get("date") or "")[:19]

        def _state(g: dict) -> str:
            return (g.get("status_state") or "").lower()

        def _is_final(g: dict) -> bool:
            st, status = _state(g), str(g.get("status") or "").lower()
            detail = str(g.get("detail") or "").lower()
            if st in ("post", "final"):
                return True
            if "final" in status or "final" in detail:
                return True
            # scored and not live/pre
            hs, aws = g.get("home_score"), g.get("away_score")
            if hs not in (None, "–", "") and aws not in (None, "–", "") and st not in ("in", "pre"):
                try:
                    float(hs); float(aws)
                    return True
                except Exception:
                    pass
            return False

        def _is_live(g: dict) -> bool:
            return _state(g) == "in" or "live" in str(g.get("status") or "").lower()

        def _is_upcoming(g: dict) -> bool:
            return not _is_final(g) and not _is_live(g)

        def _dedupe(games: List[dict]) -> List[dict]:
            seen, out = set(), []
            for g in games:
                k = str(g.get("id") or "") + "|" + str(g.get("name") or "") + "|" + _parse_date(g)
                if k in seen:
                    continue
                seen.add(k)
                out.append(g)
            return out

        def _involves_event(e: dict) -> bool:
            # STRICT: ESPN team id is authoritative when present
            comps = _safe_get(e, "competitions", 0, "competitors") or []
            ids = [str(_safe_get(c, "team", "id") or "") for c in comps]
            if tid:
                return tid in ids
            # Name fallback only with distinctive tokens (never "Football")
            blob = f"{e.get('name','')} {e.get('shortName','')}".lower()
            tokens = team_match_tokens(team)
            return any(tok in blob for tok in tokens)

        def add_games(games: List[dict], label: str) -> None:
            nonlocal pool, sources_used
            if not games:
                return
            pool.extend(games)
            sources_used.append(label)

        # --- Source 1: ESPN team schedule (best year-round) ---
        if tid and path:
            for season_q in (None, {}):
                try:
                    url = f"{ESPN_BASE}/{path}/teams/{tid}/schedule"
                    # current season implicit; also try seasontype=2 regular
                    params = {"seasontype": 2} if season_q is not None else None
                    data = self._request(url, params)
                    events = data.get("events") or []
                    if not events and season_q is None:
                        # try without params already done; continue
                        continue
                    games = [self._norm_espn_event(e) for e in events]
                    add_games(games, "espn-schedule")
                    break
                except Exception:
                    continue

        # --- Source 2: ESPN scoreboard today + yesterday ---
        if path:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            for delta in (0, -1, 1):
                day = (now + timedelta(days=delta)).strftime("%Y%m%d")
                try:
                    data = self._request(f"{ESPN_BASE}/{path}/scoreboard", {"dates": day})
                    events = [e for e in (data.get("events") or []) if _involves_event(e)]
                    add_games([self._norm_espn_event(e) for e in events], f"espn-sb-{day}")
                except Exception:
                    continue

        # --- Source 3: TheSportsDB last + next ---
        tsid = team.get("thesportsdb_id") or ""
        if tsid:
            try:
                past = self._request(f"{THESPORTSDB_BASE}/eventslast.php", {"id": tsid})
                games = []
                for e in (past.get("results") or [])[:10]:
                    g = self._norm_tsdb_event(e)
                    g["status_state"] = "post"
                    g["status"] = g.get("status") or "Final"
                    games.append(g)
                add_games(games, "tsdb-last")
            except Exception:
                pass
            try:
                nxt = self._request(f"{THESPORTSDB_BASE}/eventsnext.php", {"id": tsid})
                games = []
                for e in (nxt.get("events") or [])[:10]:
                    g = self._norm_tsdb_event(e)
                    g["status_state"] = g.get("status_state") or "pre"
                    games.append(g)
                add_games(games, "tsdb-next")
            except Exception:
                pass

        pool = _dedupe(pool)
        # Strict post-filter: id or distinctive name tokens
        tokens = team_match_tokens(team)
        def _keeps_g(g: dict) -> bool:
            blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
            if tid:
                # For ESPN-sourced rows trust schedule (already team endpoint) or name
                if g.get("source") == "espn" and (
                    short in blob or any(tok in blob for tok in tokens)
                ):
                    return True
                # if scores came from team schedule endpoint they should match
                if any(tok in blob for tok in tokens):
                    return True
                # last resort: short name
                return bool(short and short.lower() in blob)
            return any(tok in blob for tok in tokens) if tokens else True
        pool = [g for g in pool if _keeps_g(g)]

        # Pick view
        live = [g for g in pool if _is_live(g)]
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_g = [g for g in pool if (g.get("date") or "").startswith(today)]
        finals = sorted([g for g in pool if _is_final(g)], key=_parse_date)
        upcoming = sorted([g for g in pool if _is_upcoming(g)], key=_parse_date)

        picked: List[dict] = []
        if live:
            picked = live
        elif today_g:
            # include yesterday final if today is upcoming only
            if all(_is_upcoming(g) for g in today_g) and finals:
                picked = [finals[-1]] + today_g
            else:
                picked = today_g
        else:
            if finals:
                picked.append(finals[-1])
            if upcoming:
                picked.append(upcoming[0])
            if not picked and pool:
                picked = sorted(pool, key=_parse_date)[-2:]

        if not picked:
            q = quote_plus(team.get("name") or team_key)
            picked = [{
                "id": "fallback",
                "name": f"{team.get('name')} scores",
                "date": "",
                "status": "Open sources",
                "status_state": "pre",
                "detail": f"https://www.google.com/search?q={q}+score",
                "home_team": team.get("short") or team.get("name"),
                "home_score": "–",
                "away_team": "See link",
                "away_score": "–",
                "venue": "",
                "broadcast": None,
                "source": "fallback",
            }]
            sources_used.append("fallback")

        src = "+".join(sources_used[:6]) or "none"
        ttl = self.live_cache_ttl if any(_is_live(g) for g in picked) else self.cache_ttl
        self._set_cache(cache_key, picked, ttl)
        return picked, src

    def get_team_info(self, team_key: str) -> Tuple[dict, str]:
        if team_key not in TEAMS:
            return {"name": "Unknown", "record": "—", "logo": None}, "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"info:{team_key}"

        def espn() -> dict:
            url = f"{ESPN_BASE}/{team['espn_path']}/teams/{team['espn_id']}"
            data = self._request(url)
            t = data.get("team") or {}
            record_items = _safe_get(t, "record", "items", default=[]) or []
            summary = record_items[0].get("summary") if record_items else None
            logos = t.get("logos") or []
            return {
                "name": t.get("displayName") or team["name"],
                "abbreviation": t.get("abbreviation"),
                "location": t.get("location"),
                "logo": logos[0].get("href") if logos else None,
                "record": summary or t.get("standingSummary") or "—",
                "standingSummary": t.get("standingSummary"),
                "source": "espn",
            }

        def thesportsdb() -> dict:
            url = f"{THESPORTSDB_BASE}/lookupteam.php"
            data = self._request(url, {"id": team["thesportsdb_id"]})
            teams = data.get("teams") or []
            if not teams:
                return None
            t = teams[0]
            return {
                "name": t.get("strTeam") or team["name"],
                "abbreviation": t.get("strTeamShort"),
                "location": t.get("strStadiumLocation"),
                "logo": t.get("strTeamBadge"),
                "record": "—",
                "standingSummary": (t.get("strDescriptionEN") or "")[:160],
                "source": "thesportsdb",
            }

        data, src = self._try_sources(
            [("espn", espn), ("thesportsdb", thesportsdb)],
            cache_key,
            allow_empty=False,
        )
        if not data:
            data = {
                "name": team["name"],
                "abbreviation": team["short"][:3].upper(),
                "location": "Ohio",
                "logo": None,
                "record": "—",
                "standingSummary": None,
                "source": "static-fallback",
            }
            src = "static-fallback"
        return data, src

    # ---- News ----
    def get_news(self, team_key: str, limit: int = 12) -> Tuple[List[dict], str]:
        """Headlines only for the selected team (no long club descriptions)."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"news:{team_key}:{limit}:v3"
        needles = []
        for k in ("name", "short", "odds_team", "search_name", "mascot"):
            v = (team.get(k) or "").lower().strip()
            if v and len(v) > 2 and v not in needles:
                needles.append(v)
        for part in (team.get("name") or "").lower().split():
            if len(part) > 3 and part not in needles:
                needles.append(part)

        def _relevant(h: str, d: str = "") -> bool:
            text = f"{h} {d}".lower()
            return any(n in text for n in needles) if needles else True

        def espn_team_news() -> Optional[List[dict]]:
            tid, path = team.get("espn_id") or "", team.get("espn_path") or ""
            if not tid or not path or team.get("hs"):
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}/news", {"limit": max(limit, 10)})
            except Exception:
                return None
            out = []
            for a in data.get("articles") or []:
                h, d = a.get("headline") or "", a.get("description") or ""
                out.append({
                    "headline": h or "Headline",
                    "description": (d or "")[:180],
                    "published": a.get("published") or "",
                    "url": _safe_get(a, "links", "web", "href") or "#",
                    "image": (a.get("images") or [{}])[0].get("url"),
                    "source": "ESPN",
                })
                if len(out) >= limit:
                    break
            return out or None

        def espn_filtered() -> Optional[List[dict]]:
            path = team.get("espn_path") or ""
            if not path or team.get("hs"):
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/news", {"limit": 50})
            except Exception:
                return None
            out = []
            for a in data.get("articles") or []:
                h, d = a.get("headline") or "", a.get("description") or ""
                if not _relevant(h, d):
                    continue
                out.append({
                    "headline": h,
                    "description": (d or "")[:180],
                    "published": a.get("published") or "",
                    "url": _safe_get(a, "links", "web", "href") or "#",
                    "image": (a.get("images") or [{}])[0].get("url"),
                    "source": "ESPN filtered",
                })
                if len(out) >= limit:
                    break
            return out or None

        def search_links() -> List[dict]:
            q = quote_plus(team.get("name") or team_key)
            return [
                {"headline": f"{team.get('name')} — Google News", "description": "", "published": "", "url": f"https://www.google.com/search?q={q}&tbm=nws", "image": None, "source": "Google"},
                {"headline": f"{team.get('name')} — ESPN", "description": "", "published": "", "url": f"https://www.espn.com/search/_/q/{q}", "image": None, "source": "ESPN"},
                {"headline": f"{team.get('name')} — CBS", "description": "", "published": "", "url": f"https://www.cbssports.com/search/{q}/", "image": None, "source": "CBS"},
            ]

        return self._try_sources(
            [("espn-team", espn_team_news), ("espn-filtered", espn_filtered), ("links", search_links)],
            cache_key,
        )

    def get_standings(self, team_key: str) -> Tuple[List[dict], str]:
        """Always return standings context for the selected team."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"std:{team_key}:v4"
        if team.get("hs") and team_key in LOCAL_PROGRAMS and not team.get("espn_id"):
            rows = local_program_rows(team_key, "standings")
            return rows, "local-program"
        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")
        year = time.gmtime().tm_year
        focus = (team.get("name") or team.get("short") or "").lower()

        def _parse_entries(data: Any) -> List[dict]:
            rows: List[dict] = []

            def walk(node: Any) -> None:
                if isinstance(node, dict):
                    entries = node.get("entries") or _safe_get(node, "standings", "entries") or []
                    if isinstance(entries, list) and entries and isinstance(entries[0], dict) and "team" in (entries[0] or {}):
                        for entry in entries:
                            team_obj = entry.get("team") or {}
                            stats = {
                                s.get("name"): s.get("displayValue")
                                for s in (entry.get("stats") or [])
                                if s.get("name")
                            }
                            rows.append({
                                "Team": team_obj.get("displayName") or team_obj.get("name") or "—",
                                "W": stats.get("wins") or stats.get("overallWins") or stats.get("wins") or "—",
                                "L": stats.get("losses") or stats.get("overallLosses") or "—",
                                "PCT": stats.get("winPercent") or stats.get("avgPointsFor") or "—",
                                "GB": stats.get("gamesBehind") or "—",
                                "STRK": stats.get("streak") or stats.get("total") or "—",
                            })
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for item in node:
                        walk(item)

            walk(data)
            seen = set()
            uniq = []
            for r in rows:
                if r["Team"] not in seen:
                    seen.add(r["Team"])
                    uniq.append(r)
            return uniq

        def espn_standings() -> Optional[List[dict]]:
            for url in (
                f"{ESPN_BASE}/{path}/standings",
                f"{ESPN_BASE}/{path}/standings?season={year}",
                f"{ESPN_BASE}/{path}/standings?season={year-1}",
            ):
                try:
                    data = self._request(url)
                except Exception:
                    continue
                rows = _parse_entries(data)
                if rows:
                    return rows[:40]
            return None

        def espn_team_record_row() -> Optional[List[dict]]:
            if not tid:
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}")
            except Exception:
                return None
            t0 = data.get("team") or {}
            rec = "—"
            for item in (t0.get("record") or {}).get("items") or []:
                if item.get("type") == "total" or item.get("description") == "Overall Summary":
                    rec = item.get("summary") or rec
                    break
            standing = t0.get("standingSummary") or ""
            return [{
                "Team": t0.get("displayName") or team.get("name"),
                "W": rec.split("-")[0] if "-" in str(rec) else rec,
                "L": rec.split("-")[1] if "-" in str(rec) and len(rec.split("-")) > 1 else "—",
                "PCT": "—",
                "GB": "—",
                "STRK": standing or "Team record",
            }]

        def curated_fallback() -> List[dict]:
            q = quote_plus(team.get("name") or team_key)
            return [
                {
                    "Team": team.get("name") or team_key,
                    "W": "—",
                    "L": "—",
                    "PCT": "—",
                    "GB": "—",
                    "STRK": f"Selected team · {team.get('league')}",
                },
                {"Team": "ESPN standings", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.espn.com/search/_/q/{q}%20standings"},
                {"Team": "CBS Sports", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.cbssports.com/search/{q}/"},
                {"Team": "FOX Sports", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.foxsports.com/search?q={q}"},
                {"Team": "Google", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.google.com/search?q={q}+standings"},
            ]

        rows, src = self._try_sources(
            [
                ("espn-standings", espn_standings),
                ("espn-team-record", espn_team_record_row),
                ("fallback", curated_fallback),
            ],
            cache_key,
        )
        rows = rows or curated_fallback()
        # Move selected team to top when present
        if focus and rows:
            def score(r):
                name = (r.get("Team") or "").lower()
                return 0 if any(p in name for p in focus.split() if len(p) > 2) else 1
            rows = sorted(rows, key=score)
        return rows, src

    def get_schedule(self, team_key: str) -> Tuple[List[dict], str]:
        """Ordered full schedule (when/where/score) — merges ESPN + TheSportsDB."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sch:{team_key}:v7"

        cached = self._get_cached(cache_key)
        if cached is not None and cached != []:
            return cached, "cache"

        if team.get("hs") and team_key in LOCAL_PROGRAMS and not team.get("espn_id"):
            rows = local_program_rows(team_key, "schedule")
            self._set_cache(cache_key, rows, getattr(self, "schedule_ttl", 180.0))
            return rows, "local-program"

        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")
        pool: List[dict] = []
        sources_used: List[str] = []

        def _sk(g: dict) -> str:
            return (g.get("date") or "9999")[:19]

        def _dedupe(games: List[dict]) -> List[dict]:
            seen, out = set(), []
            for g in games:
                k = str(g.get("id") or "") + "|" + _sk(g) + "|" + str(g.get("name") or "")
                if k in seen:
                    continue
                seen.add(k)
                out.append(g)
            return out

        if tid and path:
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}/schedule")
                events = data.get("events") or []
                if events:
                    pool.extend(self._norm_espn_event(e) for e in events)
                    sources_used.append("espn-schedule")
            except Exception:
                pass
            # regular season explicit
            try:
                data = self._request(
                    f"{ESPN_BASE}/{path}/teams/{tid}/schedule",
                    {"seasontype": 2},
                )
                events = data.get("events") or []
                if events:
                    pool.extend(self._norm_espn_event(e) for e in events)
                    sources_used.append("espn-reg")
            except Exception:
                pass

        tsid = team.get("thesportsdb_id") or ""
        if tsid:
            for endpoint, key, state in (
                ("eventslast.php", "results", "post"),
                ("eventsnext.php", "events", "pre"),
            ):
                try:
                    data = self._request(f"{THESPORTSDB_BASE}/{endpoint}", {"id": tsid})
                    for e in data.get(key) or []:
                        g = self._norm_tsdb_event(e)
                        g["status_state"] = state
                        pool.append(g)
                    sources_used.append(f"tsdb-{state}")
                except Exception:
                    continue

        # Keep only games involving selected team (TSDB can be noisy)
        tokens = team_match_tokens(team)
        def _keeps(g: dict) -> bool:
            blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
            if not tokens:
                return True
            return any(tok in blob for tok in tokens)
        pool = [g for g in pool if _keeps(g)]
        pool = _dedupe(pool)
        pool = sorted(pool, key=_sk)

        if not pool:
            q = quote_plus(team.get("name") or team_key)
            pool = [{
                "id": "sch-fallback",
                "name": f"{team.get('name')} schedule",
                "date": "",
                "status": "Open link",
                "status_state": "pre",
                "detail": f"https://www.google.com/search?q={q}+schedule",
                "home_team": team.get("short") or "",
                "home_score": "–",
                "away_team": "Schedule",
                "away_score": "–",
                "venue": "",
                "broadcast": None,
                "source": "search",
            }]
            sources_used.append("fallback")

        src = "+".join(sources_used[:6]) or "none"
        self._set_cache(cache_key, pool, getattr(self, "schedule_ttl", 180.0))
        return pool, src

    def get_recent_form(self, team_key: str) -> Tuple[List[dict], str]:
        """Recent finished games for selected team only; falls back to broader history."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        name = (team.get("name") or "").lower()
        short = (team.get("short") or "").lower()

        def _involves_team(g: dict) -> bool:
            blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
            return (name and name in blob) or (short and short in blob) or not name

        try:
            schedule, src = self.get_schedule(team_key)
            finished = [
                g for g in schedule
                if (
                    (g.get("status_state") or "") in ("post", "final")
                    or "final" in str(g.get("status", "")).lower()
                )
                and _involves_team(g)
            ]
            if finished:
                return finished[-12:], src
        except Exception:
            pass

        # TheSportsDB last events
        try:
            tid = team.get("thesportsdb_id") or ""
            if tid:
                past = self._request(f"{THESPORTSDB_BASE}/eventslast.php", {"id": tid})
                events = past.get("results") or []
                out = [self._norm_tsdb_event(e) for e in events if e]
                out = [g for g in out if _involves_team(g)]
                if out:
                    return out[-12:], "thesportsdb-last"
        except Exception:
            pass

        return [], "none"

    def get_all_time_trends(self, team_key: str) -> Tuple[List[dict], str]:
        """Curated / historical trend points when live form is empty."""
        from .curated_data import ALL_TIME_LEADERS, CHAMPIONSHIP_GREATS
        rows: List[dict] = []
        greats = (CHAMPIONSHIP_GREATS or {}).get(team_key) or []
        for g in greats[:8]:
            rows.append({
                "era": g.get("era") or "",
                "player": g.get("player") or "",
                "note": g.get("why") or g.get("titles") or "Historical marker",
                "kind": "great",
            })
        leaders = (ALL_TIME_LEADERS or {}).get(team_key) or {}
        for cat, entries in list(leaders.items())[:4]:
            for e in (entries or [])[:3]:
                rows.append({
                    "era": cat,
                    "player": e.get("player") or "",
                    "note": f"{e.get('value','')} — all-time leader context",
                    "kind": "leader",
                })
        if not rows:
            team = TEAMS.get(team_key, {})
            rows = [{
                "era": "franchise",
                "player": team.get("short") or team_key,
                "note": f"Historical trend data limited for {team.get('name') or team_key}.",
                "kind": "meta",
            }]
        return rows, "curated-all-time"

    # ---- Odds (optional The Odds API) ----
    def set_odds_key(self, key: str) -> None:
        self.odds_api_key = (key or "").strip()

    def get_odds(self, team_key: str) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        if not self.odds_api_key:
            return [], "no-api-key"
        team = TEAMS[team_key]
        cache_key = f"odds:{team_key}"
        sport_key = team.get("odds_sport_key")
        team_name = (team.get("odds_team") or "").lower()

        def odds_api() -> List[dict]:
            url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
            params = {
                "apiKey": self.odds_api_key,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american",
            }
            data = self._request(url, params)
            if not isinstance(data, list):
                return []
            out = []
            for game in data:
                home = (game.get("home_team") or "").lower()
                away = (game.get("away_team") or "").lower()
                relevant = team_name in home or team_name in away
                if not relevant and len(out) >= 5:
                    continue
                bookmakers = game.get("bookmakers") or []
                books = []
                for bm in bookmakers[:5]:
                    markets = {}
                    for m in bm.get("markets") or []:
                        markets[m.get("key")] = [
                            {
                                "name": o.get("name"),
                                "price": o.get("price"),
                                "point": o.get("point"),
                            }
                            for o in (m.get("outcomes") or [])
                        ]
                    books.append({"book": bm.get("title"), "markets": markets})
                out.append(
                    {
                        "commence_time": game.get("commence_time"),
                        "home_team": game.get("home_team"),
                        "away_team": game.get("away_team"),
                        "sport": game.get("sport_title"),
                        "bookmakers": books,
                        "relevant": relevant,
                    }
                )
            # prefer relevant games first
            out.sort(key=lambda g: (not g["relevant"], g.get("commence_time") or ""))
            return out[:10]

        return self._try_sources([("the-odds-api", odds_api)], cache_key)

    def prediction_links(self, team_key: str) -> List[dict]:
        q = TEAMS.get(team_key, {}).get("prediction_query", "Cleveland")
        qq = quote_plus(q)
        return [
            {
                "name": "Polymarket",
                "url": f"https://polymarket.com/search?q={qq}",
                "desc": "Crypto prediction markets — game & season contracts",
            },
            {
                "name": "Kalshi",
                "url": f"https://kalshi.com/search?q={qq}",
                "desc": "CFTC-regulated event contracts",
            },
            {
                "name": "ESPN search",
                "url": f"https://www.espn.com/search/_/q/{qq}",
                "desc": "News + odds ecosystem",
            },
            {
                "name": "The Odds API",
                "url": "https://the-odds-api.com/",
                "desc": "Free key powers in-app consensus odds",
            },
        ]

    def any_live_games(self, team_key: str) -> bool:
        try:
            games, _ = self.get_scoreboard(team_key)
            return any((g.get("status_state") or "") == "in" for g in games)
        except Exception:
            return False



    def get_betting_dashboard(self, team_key: str) -> Tuple[dict, str]:
        """Unified betting payload: live odds + ESPN lines + market links."""
        result = {
            "games": [],
            "has_api_key": bool(self.odds_api_key),
            "espn_lines": [],
            "links": self.prediction_links(team_key),
        }
        sources = []
        # Odds API
        try:
            games, src = self.get_odds(team_key)
            result["games"] = games
            sources.append(src)
        except Exception as e:
            sources.append(f"odds-api:{e}")
        # ESPN scoreboard embedded lines
        try:
            sb, ssrc = self.get_scoreboard(team_key)
            lines = []
            for g in sb:
                if g.get("odds"):
                    lines.append({
                        "matchup": g.get("name"),
                        "status": g.get("status"),
                        "odds": g.get("odds"),
                        "home": g.get("home_team"),
                        "away": g.get("away_team"),
                    })
            result["espn_lines"] = lines
            sources.append(ssrc)
        except Exception as e:
            sources.append(f"espn-lines:{e}")
        return result, "+".join(sources[:4])



@lru_cache(maxsize=1)
def get_client() -> SportsAPIClient:
    return SportsAPIClient()
