"""Team slogans, phrases, inside jokes — Cleveland / Ohio / Raiders centric."""
from __future__ import annotations
from typing import Dict

FLAVOR: Dict[str, dict] = {
    "browns": {
        "slogan": "Here We Go Brownies — Dawg Pound forever.",
        "phrases": ["Dawg Pound", "Believeland", "Orange and Brown", "Cleveland rocks", "Who do you play for?", "Lake-effect loyalty"],
        "witty": "Whatever the record, the lake-effect loyalty never melts.",
        "icon": "🐕",
    },
    "guardians": {
        "slogan": "Guarded by the lake. Powered by Progressive Field.",
        "phrases": ["Go Guards", "Our time", "Cleveland baseball summers", "The Land's nine", "Slider season"],
        "witty": "When the bats wake up, the whole North Coast hears it.",
        "icon": "⚾",
    },
    "cavaliers": {
        "slogan": "All for Caviland — The Land remembers 2016.",
        "phrases": ["The Land", "Caviland", "Believe", "Wine and gold", "Sword and shield", "From The Shot to The Block"],
        "witty": "Northeast Ohio still writes the script when the lights get bright.",
        "icon": "⚔️",
    },
    "osu_football": {
        "slogan": "Script Ohio. Hang on tight.",
        "phrases": ["O-H!", "I-O!", "The Shoe", "Go Bucks", "Across the field", "Skull Session"],
        "witty": "If you hear the Skull Session, you already know how Saturday goes.",
        "icon": "🌰",
    },
    "osu_mbb": {
        "slogan": "Buckeyes in the paint — Scarlet and Gray never sleep.",
        "phrases": ["Go Bucks", "Value City Arena energy", "Scarlet pressure", "TBDBITL adjacent pride"],
        "witty": "When the threes rain in Columbus, the whole Big Ten checks the radar.",
        "icon": "🏀",
    },
    "crew": {
        "slogan": "Massive. Black & gold. Nordecke loud.",
        "phrases": ["Massive", "Nordecke", "Crew forever", "Lower.com Field nights", "Black and gold"],
        "witty": "If the drums start early, the opponents already lost the parking lot.",
        "icon": "⚽",
    },
    "bluejackets": {
        "slogan": "CBJ — Cannon ready.",
        "phrases": ["CBJ", "Cannon night", "Nationwide Arena", "Union Blue", "C-b-j clap"],
        "witty": "When that cannon fires, High Street feels it two blocks over.",
        "icon": "🏒",
    },
    "usmnt": {
        "slogan": "I believe that we will win.",
        "phrases": ["USMNT", "I believe", "Sam's Army", "Stars and Stripes"],
        "witty": "From Concacaf chaos to World Cup dreams — always loud, always ours.",
        "icon": "🇺🇸",
    },
    "usab": {
        "slogan": "USA Basketball — gold standard.",
        "phrases": ["Team USA", "Dream Team DNA", "Red, white, and blue"],
        "witty": "When the USA puts five on the floor, the whole planet checks the scoreboard.",
        "icon": "🏀",
    },
    "kent_mbb": {
        "slogan": "Golden Flashes — MAC attack.",
        "phrases": ["Go Flashes", "MAC pride", "Kent State fight"],
        "witty": "Never count out the Flashes when March starts whispering.",
        "icon": "⚡",
    },
    "rhs_football": {
        "slogan": "Reynoldsburg Raiders — purple and gold under the lights.",
        "phrases": ["Go Raiders", "Purple and gold", "Raider Nation", "OCC battle", "Friday night pride"],
        "witty": "Friday nights in Reynoldsburg — purple storm, gold standard.",
        "icon": "🛡️",
    },
    "rhs_mbb": {
        "slogan": "Raiders basketball — hard cuts, purple pressure.",
        "phrases": ["Go Raiders", "Purple and gold", "Raider Nation", "Paint ownership"],
        "witty": "When the gym packs out, every possession feels like a playoff game.",
        "icon": "🛡️",
    },
    "tiffin_tf": {
        "slogan": "Tiffin Dragons — track that breathes fire.",
        "phrases": ["Go Dragons", "G-MAC distance", "Spike up"],
        "witty": "Lanes, jumps, throws — Dragons measure excellence in fractions of a second.",
        "icon": "🐉",
    },
}

DEFAULT_FLAVOR = {
    "slogan": "Ohio sports — loud, loyal, legendary.",
    "phrases": ["Believeland", "Cleveland rocks", "Ohio pride"],
    "witty": "From the lake to the campus, we show up.",
    "icon": "🦉",
}


def get_flavor(team_key: str) -> dict:
    return FLAVOR.get(team_key, DEFAULT_FLAVOR)
