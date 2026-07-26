"""On-this-day style fun facts per team — multi-source with curated failover."""
from __future__ import annotations
import random
from datetime import datetime
from typing import Tuple
import requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SOSBY-FunFacts/1.0"})

CURATED = {
    "browns": [
        "The Dawg Pound nickname took off in the 1980s — bark optional, loyalty required.",
        "Jim Brown never missed a game in nine NFL seasons. That's not a typo.",
        "Municipal Stadium held the old 'Factory of Sadness' memes — fans still showed up.",
        "Orange helmets + brown stripes = pure North Coast iconography.",
    ],
    "guardians": [
        "Progressive Field summers hit different when the lake breeze shows up.",
        "The franchise's 1990s October runs still get replayed in Cleveland living rooms.",
        "Name changed to Guardians — the bridge and the city stayed the point.",
        "Slider season is a lifestyle, not just a pitch.",
    ],
    "cavaliers": [
        "2016 wasn't a season — it was a civic event from The Land.",
        "Wine and gold still means June basketball in Northeast Ohio.",
        "The Block and the dagger three live rent-free forever.",
        "Caviland is a state of mind as much as a map pin.",
    ],
    "osu_football": [
        "Script Ohio still gives people goosebumps on purpose.",
        "O-H! … you already know the rest.",
        "The Shoe on a night game is a personality test.",
        "Across the field isn't just lyrics — it's a warning.",
    ],
    "osu_mbb": [
        "Scarlet pressure in the paint is a Buckeye tradition.",
        "Value City Arena noise has ended more than one visitor's night.",
        "TBDBITL gets the football glory; the hoops still bang in March.",
    ],
    "crew": [
        "Nordecke doesn't do quiet — Massive is a volume setting.",
        "Black and gold nights at Lower.com Field are a Columbus ritual.",
        "When the drums start early, the match already started in the stands.",
    ],
    "bluejackets": [
        "The cannon is not subtle. Neither is Nationwide on a goal.",
        "Union Blue hits different in January.",
        "CBJ energy: workmanlike, loud, and proud of it.",
    ],
    "usmnt": [
        "I believe that we will win — still the chant, still the hope.",
        "Sam's Army travels better than most airline miles programs.",
    ],
    "usab": [
        "USA Basketball gold is the expectation — pressure is the point.",
        "Dream Team DNA still shows up in every generation.",
    ],
    "kent_mbb": [
        "Golden Flashes in March have a history of spoiling brackets.",
        "MAC fight travels — Kent knows the miles.",
    ],
    "rhs_football": [
        "Purple and gold under the lights — Raider Nation Friday classic.",
        "Reynoldsburg football: OCC battles and hometown noise.",
    ],
    "rhs_mbb": [
        "Raiders hoops — purple pressure, gold standards.",
        "When the gym is packed, every possession feels bigger.",
    ],
    "tiffin_tf": [
        "Dragons measure days in splits and personal bests.",
        "Track doesn't lie — the clock is the only judge.",
    ],
}


def _wiki_on_this_day() -> str:
    try:
        now = datetime.utcnow()
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{now.month}/{now.day}"
        r = SESSION.get(url, timeout=5)
        if r.status_code != 200:
            return ""
        selected = (r.json() or {}).get("selected") or []
        if not selected:
            return ""
        text = (selected[0].get("text") or "").strip()
        return text[:180] if text else ""
    except Exception:
        return ""


def fun_fact_for_team(team_key: str, team_name: str) -> Tuple[str, str]:
    """Return (fact, source)."""
    # 1 curated rotating by day
    facts = CURATED.get(team_key) or [
        f"{team_name}: show up, stay loud, repeat.",
        f"History is written one possession at a time for {team_name}.",
    ]
    day_i = datetime.utcnow().timetuple().tm_yday
    fact = facts[day_i % len(facts)]

    # 2 optional wiki on-this-day spice (generic history)
    wiki = _wiki_on_this_day()
    if wiki and day_i % 3 == 0:
        return (f"{fact} · On this day in history: {wiki}", "curated+wikimedia")

    return fact, "curated"
