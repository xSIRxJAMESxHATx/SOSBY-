"""Friendly Cleveland-slant rule-based chat agent with failover replies."""
from __future__ import annotations
import random
import re
from typing import List, Tuple

from .team_flavor import get_flavor

GREETINGS = [
    "Hey friend — Believeland checking in! What can I help with?",
    "Welcome to the North Coast chat desk — ask me anything about your team.",
    "O-H! … wait, wrong chat. Still happy you're here — fire away!",
]


def reply(message: str, team_key: str, team_name: str) -> Tuple[str, str]:
    """Return (answer, source_tag). Multiple pattern banks as failsafes."""
    msg = (message or "").strip()
    if not msg:
        return random.choice(GREETINGS), "greet"
    low = msg.lower()
    flavor = get_flavor(team_key)
    slogan = flavor.get("slogan", "")
    witty = flavor.get("witty", "")

    banks: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\b(hi|hello|hey|yo)\b", re.I), random.choice(GREETINGS)),
        (re.compile(r"\b(score|winning|losing)\b", re.I),
         f"Check the **Live Scores** tab for the latest on {team_name}. Auto-refresh keeps it humming every ~45 seconds."),
        (re.compile(r"\b(ticket|tickets|go to the game)\b", re.I),
         f"Hit the **Tickets** tab for Ticketmaster, SeatGeek, StubHub and more for {team_name}."),
        (re.compile(r"\b(weather|cold|snow|rain)\b", re.I),
         "Open **Weather** for live conditions at the venue plus a map link. Lake-effect surprises are a Cleveland specialty!"),
        (re.compile(r"\b(odds|bet|arbitrage|kelly)\b", re.I),
         "Betting HQ has odds, Kelly math, and educational arb notes. Always play responsible — this isn't financial advice."),
        (re.compile(r"\b(slogan|chant|dawg|believeland|massive)\b", re.I),
         f"{slogan} Also: {', '.join(flavor.get('phrases', [])[:3])}."),
        (re.compile(r"\b(help|how|what can)\b", re.I),
         "Use the tabs for Scores, Weather, Moments, Tickets, Community, and Betting HQ. I'm the friendly desk clerk with a Cleveland heart."),
        (re.compile(r"\b(thanks|thank you)\b", re.I), "You got it — go make Northeast Ohio proud!"),
    ]
    for pat, ans in banks:
        if pat.search(msg):
            return ans + f"\n\n_{witty}_", "pattern"

    # failover banks
    fallbacks = [
        f"Solid question. While I dig through the fog off the lake: {slogan}",
        f"I'm a lightweight agent (no big cloud brain on this free tier), but here's the vibe — {witty}",
        f"Try the Community tab to ask fellow fans, or check News for the latest on {team_name}.",
        "If that didn't hit, rephrase once — I'll try another angle. Believeland never quits.",
    ]
    return random.choice(fallbacks), "fallback"
