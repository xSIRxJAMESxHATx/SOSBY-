"""Famous moments links + ticket seller directory (legal / public search links)."""
from __future__ import annotations
from typing import Dict, List
from urllib.parse import quote_plus

MOMENTS: Dict[str, List[dict]] = {
    "browns": [
        {"title": "The Drive / The Fumble lore", "url": "https://www.youtube.com/results?search_query=Cleveland+Browns+The+Drive", "note": "Search — historical context"},
        {"title": "Baker Mayfield debut energy", "url": "https://www.youtube.com/results?search_query=Baker+Mayfield+Browns+debut", "note": "YT search"},
        {"title": "Myles Garrett highlights", "url": "https://www.youtube.com/results?search_query=Myles+Garrett+highlights", "note": "YT search"},
        {"title": "Browns official site", "url": "https://www.clevelandbrowns.com/", "note": "Team media"},
        {"title": "ESPN Browns", "url": "https://www.espn.com/nfl/team/_/name/cle/cleveland-browns", "note": "ESPN"},
    ],
    "cavaliers": [
        {"title": "2016 Finals Game 7", "url": "https://www.youtube.com/results?search_query=Cavs+2016+Game+7", "note": "YT search"},
        {"title": "The Block (LeBron)", "url": "https://www.youtube.com/results?search_query=LeBron+The+Block+2016", "note": "YT search"},
        {"title": "Kyrie Game 7 dagger", "url": "https://www.youtube.com/results?search_query=Kyrie+Irving+Game+7+dagger", "note": "YT search"},
        {"title": "Cavs official", "url": "https://www.nba.com/cavaliers", "note": "Team"},
        {"title": "ESPN Cavs", "url": "https://www.espn.com/nba/team/_/name/cle/cleveland-cavaliers", "note": "ESPN"},
    ],
    "guardians": [
        {"title": "1995 / 1997 October runs", "url": "https://www.youtube.com/results?search_query=Cleveland+Indians+1995+playoffs", "note": "YT search"},
        {"title": "Progressive Field moments", "url": "https://www.youtube.com/results?search_query=Progressive+Field+highlights", "note": "YT search"},
        {"title": "Guardians official", "url": "https://www.mlb.com/guardians", "note": "Team"},
        {"title": "ESPN Guardians", "url": "https://www.espn.com/mlb/team/_/name/cle/cleveland-guardians", "note": "ESPN"},
        {"title": "CBS Sports Guardians", "url": "https://www.cbssports.com/mlb/teams/CLE/cleveland-guardians/", "note": "CBS"},
    ],
    "osu_football": [
        {"title": "Script Ohio", "url": "https://www.youtube.com/results?search_query=Script+Ohio", "note": "YT search"},
        {"title": "The Game highlights", "url": "https://www.youtube.com/results?search_query=Ohio+State+Michigan+highlights", "note": "YT search"},
        {"title": "Ohio State Athletics", "url": "https://ohiostatebuckeyes.com/sports/football", "note": "Official"},
        {"title": "ESPN Ohio State", "url": "https://www.espn.com/college-football/team/_/id/194/ohio-state-buckeyes", "note": "ESPN"},
        {"title": "FOX Sports search", "url": "https://www.foxsports.com/search?q=ohio%20state%20football", "note": "FOX"},
    ],
}

DEFAULT_MOMENTS = [
    {"title": "Team highlights search", "url": "https://www.youtube.com/results?search_query={q}", "note": "YT"},
    {"title": "Google news", "url": "https://www.google.com/search?q={q}+greatest+moments", "note": "Google"},
    {"title": "Bing news", "url": "https://www.bing.com/search?q={q}+famous+games", "note": "Bing"},
    {"title": "ESPN search", "url": "https://www.espn.com/search/_/q/{q}", "note": "ESPN"},
    {"title": "CBS Sports search", "url": "https://www.cbssports.com/search/{q}/", "note": "CBS"},
]


def moments_for(team_key: str, team_name: str) -> List[dict]:
    if team_key in MOMENTS:
        return MOMENTS[team_key]
    q = quote_plus(team_name)
    out = []
    for m in DEFAULT_MOMENTS:
        out.append({"title": m["title"], "url": m["url"].format(q=q), "note": m["note"]})
    return out


def ticket_links(team_name: str) -> List[dict]:
    q = quote_plus(team_name + " tickets")
    return [
        {"name": "Ticketmaster", "url": f"https://www.ticketmaster.com/search?q={quote_plus(team_name)}"},
        {"name": "SeatGeek", "url": f"https://seatgeek.com/search?q={quote_plus(team_name)}"},
        {"name": "StubHub", "url": f"https://www.stubhub.com/secure/search?q={quote_plus(team_name)}"},
        {"name": "Vivid Seats", "url": f"https://www.vividseats.com/search?searchTerm={quote_plus(team_name)}"},
        {"name": "Team official (Google)", "url": f"https://www.google.com/search?q={quote_plus(team_name + ' official tickets')}"},
        {"name": "Gametime", "url": f"https://gametime.co/search?q={quote_plus(team_name)}"},
    ]
