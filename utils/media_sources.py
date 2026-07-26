"""
Legal / official-leaning live audio & video discovery links per team.
At least 5 channels each: streaming apps, TV, radio, web, YouTube/social.
No unauthorized streams.
"""
from __future__ import annotations
from typing import Dict, List
from urllib.parse import quote_plus

# Generic templates filled with team search terms
def _yt(q: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(q + ' live')}"

def _google(q: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(q)}"

MEDIA: Dict[str, Dict[str, List[dict]]] = {}

def _pack(team_name: str, league_hints: dict) -> Dict[str, List[dict]]:
    q = team_name
    return {
        "Streaming / Web apps": [
            {"name": league_hints.get("stream1", "League / team app"), "url": league_hints.get("stream1_url", _google(q + " official app stream")), "note": "Official app or league pass"},
            {"name": league_hints.get("stream2", "ESPN app"), "url": "https://www.espn.com/", "note": "App + browser when rights allow"},
            {"name": "Fubo search", "url": _google(q + " Fubo"), "note": "Live TV streaming (subscription)"},
            {"name": "YouTube TV search", "url": _google(q + " YouTube TV"), "note": "Live TV streaming (subscription)"},
            {"name": "Hulu + Live TV", "url": _google(q + " Hulu live"), "note": "Subscription live TV"},
        ],
        "TV channels": [
            {"name": league_hints.get("tv1", "Regional sports network"), "url": _google(q + " " + league_hints.get("tv1", "RSN") + " channel"), "note": "Local RSN / national window"},
            {"name": "ESPN / ABC window", "url": "https://www.espn.com/", "note": "National telecasts"},
            {"name": "CBS / FOX / NBC window", "url": _google(q + " TV schedule"), "note": "Check weekly national slate"},
            {"name": "Local broadcast", "url": _google(q + " local TV channel"), "note": "Over-the-air when applicable"},
            {"name": "League network", "url": league_hints.get("league_tv", "https://www.espn.com/"), "note": "NFL Network / NBA TV / etc."},
        ],
        "Radio": [
            {"name": league_hints.get("radio1", "Flagship radio"), "url": _google(q + " radio live"), "note": "Flagship AM/FM / stream"},
            {"name": "iHeart / station site", "url": _google(q + " iHeart radio"), "note": "Station stream apps"},
            {"name": "Audacy / Entercom", "url": _google(q + " Audacy"), "note": "Regional talk & play-by-play"},
            {"name": "SiriusXM search", "url": _google(q + " SiriusXM"), "note": "League channels / home feeds"},
            {"name": "Team audio page", "url": _google(q + " official audio stream"), "note": "Club site audio partners"},
        ],
        "YouTube / social video": [
            {"name": "YouTube live search", "url": _yt(q), "note": "Official highlights & occasional live"},
            {"name": "Team official YT", "url": _google(q + " official YouTube channel"), "note": "Subscribe for live posts"},
            {"name": "League YouTube", "url": league_hints.get("league_yt", "https://www.youtube.com/"), "note": "Full games only when league posts"},
            {"name": "X / Twitter live", "url": f"https://x.com/search?q={quote_plus(q)}&f=live", "note": "Official accounts post links"},
            {"name": "Facebook / Meta live", "url": _google(q + " Facebook live"), "note": "Club pages sometimes stream"},
        ],
        "Online schedules & finders": [
            {"name": "ESPN gamecast", "url": f"https://www.espn.com/search/_/q/{quote_plus(q)}", "note": "Links + audio when available"},
            {"name": "Official team site", "url": _google(q + " official site"), "note": "Watch/listen partners"},
            {"name": "Sports Reference / stats", "url": _google(q + " schedule"), "note": "Schedule context"},
            {"name": "Local news sports", "url": _google(q + " live radio TV how to watch"), "note": "How-to-watch articles"},
            {"name": "Google how to watch", "url": _google("how to watch " + q + " live"), "note": "Aggregated legal options"},
        ],
    }

# Team-specific overrides
OVERRIDES = {
    "browns": {"stream1": "NFL+ / NFL app", "stream1_url": "https://www.nfl.com/plus/", "tv1": "CBS/FOX/Amazon/ESPN", "radio1": "WKRK / Cleveland radio", "league_tv": "https://www.nfl.com/network/", "league_yt": "https://www.youtube.com/@NFL"},
    "guardians": {"stream1": "MLB.TV", "stream1_url": "https://www.mlb.com/live-stream-games", "tv1": "FanDuel Sports Network Ohio", "radio1": "WTAM / Guardians Radio", "league_tv": "https://www.mlb.com/", "league_yt": "https://www.youtube.com/@MLB"},
    "cavaliers": {"stream1": "NBA League Pass", "stream1_url": "https://www.nba.com/league-pass", "tv1": "FanDuel Sports Network Ohio", "radio1": "WTAM / Cavs Radio", "league_tv": "https://www.nba.com/", "league_yt": "https://www.youtube.com/@NBA"},
    "osu_football": {"stream1": "Big Ten Network / FOX", "stream1_url": "https://btn.com/", "tv1": "FOX / CBS / NBC", "radio1": "Ohio State IMG Sports Network", "league_yt": "https://www.youtube.com/@OhioStateFootball"},
    "osu_mbb": {"stream1": "Big Ten Network", "stream1_url": "https://btn.com/", "tv1": "BTN / FOX", "radio1": "Ohio State IMG Sports Network", "league_yt": "https://www.youtube.com/@OhioStateBBall"},
    "crew": {"stream1": "MLS Season Pass (Apple)", "stream1_url": "https://www.mlssoccer.com/season-pass/", "tv1": "MLS Season Pass", "radio1": "Crew Radio Network", "league_yt": "https://www.youtube.com/@mls"},
    "bluejackets": {"stream1": "ESPN+ / NHL.TV", "stream1_url": "https://www.nhl.com/", "tv1": "FanDuel Sports Network Ohio", "radio1": "CBC Radio / Jackets audio", "league_yt": "https://www.youtube.com/@NHL"},
    "usmnt": {"stream1": "Paramount+ / TNT / FS1", "stream1_url": "https://www.ussoccer.com/", "tv1": "FS1 / TNT / Telemundo", "radio1": "USMNT audio partners", "league_yt": "https://www.youtube.com/@ussoccer"},
    "usab": {"stream1": "NBC / Peacock Olympics windows", "stream1_url": "https://www.nbcolympics.com/", "tv1": "NBC / USA Network", "radio1": "Westwood One / Olympic audio", "league_yt": "https://www.youtube.com/@usabasketball"},
    "kent_mbb": {"stream1": "ESPN+", "stream1_url": "https://www.espn.com/watch/", "tv1": "ESPN+ / MAC Network", "radio1": "Kent State radio partners", "league_yt": "https://www.youtube.com/results?search_query=Kent+State+basketball"},
    "rhs_football": {"stream1": "NFHS Network", "stream1_url": "https://www.nfhsnetwork.com/", "tv1": "Local cable / school stream", "radio1": "Local HS radio / school broadcast", "league_yt": "https://www.youtube.com/results?search_query=Reynoldsburg+football"},
    "rhs_mbb": {"stream1": "NFHS Network", "stream1_url": "https://www.nfhsnetwork.com/", "tv1": "Local cable / school stream", "radio1": "School broadcast partners", "league_yt": "https://www.youtube.com/results?search_query=Reynoldsburg+basketball"},
    "tiffin_tf": {"stream1": "School / G-MAC streams", "stream1_url": "https://gotiffindragons.com/", "tv1": "Conference digital", "radio1": "Campus media", "league_yt": "https://www.youtube.com/results?search_query=Tiffin+University+track"},
}


def get_media_for_team(team_key: str, team_name: str) -> Dict[str, List[dict]]:
    hints = OVERRIDES.get(team_key, {})
    pack = _pack(team_name, hints)
    # ensure 5+ per category
    for cat, items in pack.items():
        while len(items) < 5:
            items.append({"name": f"More options {len(items)+1}", "url": _google(team_name + " " + cat), "note": "Search"})
    return pack
