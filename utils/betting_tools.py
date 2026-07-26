"""
Odds arbitrage detection + bankroll management helpers.
Informational only — not financial or gambling advice.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


def american_to_decimal(odds: Any) -> Optional[float]:
    try:
        o = float(odds)
    except (TypeError, ValueError):
        return None
    if o == 0:
        return None
    if o > 0:
        return 1.0 + (o / 100.0)
    return 1.0 + (100.0 / abs(o))


def implied_prob(decimal_odds: float) -> float:
    if not decimal_odds or decimal_odds <= 1:
        return 0.0
    return 1.0 / decimal_odds


def detect_arbitrage(games: List[dict], min_edge_pct: float = 0.3) -> List[dict]:
    """
    Scan h2h markets across books for 2-way arbitrage.
    Returns list of opportunities with stake split suggestion (per $100 total).
    """
    opps: List[dict] = []
    for g in games or []:
        # best decimal price per outcome name across books
        best: Dict[str, Tuple[float, str, Any]] = {}  # name -> (dec, book, amer)
        for bm in g.get("bookmakers") or []:
            book = bm.get("book") or "Book"
            markets = bm.get("markets") or {}
            h2h = markets.get("h2h") or []
            for o in h2h:
                name = (o.get("name") or "").strip()
                amer = o.get("price")
                dec = american_to_decimal(amer)
                if not name or dec is None:
                    continue
                prev = best.get(name)
                if prev is None or dec > prev[0]:
                    best[name] = (dec, book, amer)
        if len(best) < 2:
            continue
        names = list(best.keys())
        # try all pairs (typical moneyline 2-way)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n1, n2 = names[i], names[j]
                d1, b1, a1 = best[n1]
                d2, b2, a2 = best[n2]
                inv = implied_prob(d1) + implied_prob(d2)
                if inv <= 0:
                    continue
                edge = (1.0 - inv) * 100.0
                if edge >= min_edge_pct:
                    # stakes for $100 total riskless (approx)
                    s1 = 100.0 * implied_prob(d1) / inv
                    s2 = 100.0 * implied_prob(d2) / inv
                    profit = min(s1 * d1, s2 * d2) - 100.0
                    opps.append({
                        "matchup": f"{g.get('away_team')} @ {g.get('home_team')}",
                        "commence": (g.get("commence_time") or "")[:16],
                        "outcome_a": n1,
                        "book_a": b1,
                        "odds_a": a1,
                        "stake_a": round(s1, 2),
                        "outcome_b": n2,
                        "book_b": b2,
                        "odds_b": a2,
                        "stake_b": round(s2, 2),
                        "edge_pct": round(edge, 2),
                        "profit_per_100": round(profit, 2),
                        "implied_sum": round(inv, 4),
                    })
    opps.sort(key=lambda x: -x["edge_pct"])
    return opps


def kelly_fraction(decimal_odds: float, win_prob: float, fraction: float = 0.5) -> float:
    """Fractional Kelly stake as % of bankroll. Clamped to [0, 0.25]."""
    if decimal_odds <= 1 or win_prob <= 0 or win_prob >= 1:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - win_prob
    k = (b * win_prob - q) / b
    k = max(0.0, k) * fraction
    return min(k, 0.25)


def bankroll_plan(
    bankroll: float,
    unit_pct: float = 1.0,
    risk_profile: str = "moderate",
) -> dict:
    """Simple unit sizing + suggested max exposure."""
    bankroll = max(0.0, float(bankroll or 0))
    unit_pct = max(0.1, min(5.0, float(unit_pct or 1)))
    unit = bankroll * (unit_pct / 100.0)
    profiles = {
        "conservative": {"max_bet_units": 1, "max_daily_units": 3, "kelly_frac": 0.25},
        "moderate": {"max_bet_units": 2, "max_daily_units": 5, "kelly_frac": 0.5},
        "aggressive": {"max_bet_units": 3, "max_daily_units": 8, "kelly_frac": 0.75},
    }
    p = profiles.get(risk_profile, profiles["moderate"])
    return {
        "bankroll": bankroll,
        "unit_size": round(unit, 2),
        "unit_pct": unit_pct,
        "risk_profile": risk_profile,
        "max_single_bet": round(unit * p["max_bet_units"], 2),
        "max_daily_risk": round(unit * p["max_daily_units"], 2),
        "kelly_fraction": p["kelly_frac"],
        "notes": [
            "Never chase losses — pre-commit unit size.",
            "Arbitrage stakes are math splits, not guaranteed fills.",
            "Educational tool only; not advice.",
        ],
    }


def stake_from_units(unit_size: float, units: float) -> float:
    return round(max(0.0, unit_size * units), 2)



def full_kelly_table(decimal_odds: float, win_prob: float, bankroll: float) -> dict:
    """Full / half / quarter Kelly stake table."""
    results = {}
    for label, frac in [("Full Kelly", 1.0), ("Half Kelly", 0.5), ("Quarter Kelly", 0.25)]:
        f = kelly_fraction(decimal_odds, win_prob, fraction=frac)
        results[label] = {
            "fraction_of_bankroll": round(f, 4),
            "stake": round(bankroll * f, 2),
        }
    # break-even implied
    be = implied_prob(decimal_odds) if decimal_odds else 0
    results["meta"] = {
        "decimal_odds": decimal_odds,
        "implied_prob": round(be, 4),
        "your_edge": round(win_prob - be, 4) if win_prob and be else 0,
        "win_prob": win_prob,
        "bankroll": bankroll,
    }
    return results


LIVE_ARB_STRATEGIES = [
    {
        "title": "Pre-match 2-way ML arb",
        "body": "Compare best moneyline prices across books before tip/kickoff. Lock both sides when implied sum < 1. Stake proportional to inverse odds.",
    },
    {
        "title": "Middle the spread",
        "body": "When books disagree on the line (e.g. -2.5 vs -3.5), a final margin in the middle can win both tickets. Not pure arb — variance remains.",
    },
    {
        "title": "Live steam reaction (caution)",
        "body": "Sharp money moves a line; slower books lag. Requires fast execution and higher limits. Fees and delays kill many live edges.",
    },
    {
        "title": "Promo / boosted-odds synthetic",
        "body": "Pair a book promo boost with a hedge on another book. Read terms — rollover and max-bet caps apply.",
    },
    {
        "title": "Currency / exchange quirks",
        "body": "Exchange lays vs book backs can create temporary edges. Account for commission on exchanges.",
    },
]


STAT_ARB_MODELS = [
    {
        "title": "Cross-book price dispersion",
        "body": "Track the spread between best and worst moneyline. Wide dispersion can signal slower books; educational only.",
    },
    {
        "title": "Implied probability sum",
        "body": "If best-price implied probs across outcomes sum under 1 after fees, a pure arb may exist (see scanner).",
    },
    {
        "title": "Line movement z-score (conceptual)",
        "body": "Sudden multi-book moves vs recent average can flag information; needs time-series odds (paid feeds).",
    },
]



def price_dispersion(games: list) -> list:
    """Per-game best vs worst ML decimal dispersion (educational)."""
    rows = []
    for g in games or []:
        by_name = {}
        for bm in g.get("bookmakers") or []:
            for o in (bm.get("markets") or {}).get("h2h") or []:
                name = o.get("name") or ""
                dec = american_to_decimal(o.get("price"))
                if not name or dec is None:
                    continue
                by_name.setdefault(name, []).append(dec)
        for name, prices in by_name.items():
            if len(prices) < 2:
                continue
            best, worst = max(prices), min(prices)
            rows.append({
                "matchup": f"{g.get('away_team')} @ {g.get('home_team')}",
                "outcome": name,
                "best_dec": round(best, 3),
                "worst_dec": round(worst, 3),
                "dispersion_pct": round((best / worst - 1) * 100, 2) if worst else 0,
            })
    rows.sort(key=lambda r: -r["dispersion_pct"])
    return rows[:30]


def implied_edge_table(games: list) -> list:
    """Best-price implied probs for two-way books."""
    rows = []
    for g in games or []:
        best = {}
        for bm in g.get("bookmakers") or []:
            for o in (bm.get("markets") or {}).get("h2h") or []:
                name = o.get("name") or ""
                dec = american_to_decimal(o.get("price"))
                if name and dec and (name not in best or dec > best[name]):
                    best[name] = dec
        if len(best) >= 2:
            names = list(best.keys())[:2]
            s = sum(implied_prob(best[n]) for n in names)
            rows.append({
                "matchup": f"{g.get('away_team')} @ {g.get('home_team')}",
                "implied_sum": round(s, 4),
                "market_edge_pct": round((1 - s) * 100, 2) if s < 1 else round((s - 1) * -100, 2),
                "outcomes": ", ".join(names),
            })
    return rows
