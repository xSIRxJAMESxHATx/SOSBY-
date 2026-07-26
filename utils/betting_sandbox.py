"""
Bet sandbox: Kelly, Monte Carlo (antithetic + stratified), Poisson, Kalman smoothing.
Educational only.
"""
from __future__ import annotations
import math
import random
from typing import Any, Dict, List, Optional, Sequence

from .betting_tools import american_to_decimal, implied_prob, kelly_fraction


def fractional_kelly_ladder(decimal_odds: float, win_prob: float, bankroll: float) -> List[dict]:
    rows = []
    for label, frac in [
        ("Full (1/1)", 1.0), ("Half (1/2)", 0.5), ("Quarter (1/4)", 0.25),
        ("Eighth (1/8)", 0.125), ("Tenth (1/10)", 0.10),
    ]:
        f = kelly_fraction(decimal_odds, win_prob, fraction=frac)
        rows.append({
            "style": label,
            "fraction_of_bankroll": round(f, 4),
            "stake": round(bankroll * f, 2),
            "potential_profit": round(bankroll * f * (decimal_odds - 1), 2) if decimal_odds else 0,
        })
    return rows


def parlay_decimal(legs: List[float]) -> float:
    d = 1.0
    for x in legs:
        if not x or x <= 1:
            return 0.0
        d *= x
    return d


def _dec_to_amer(d: float) -> str:
    if d <= 1:
        return "—"
    if d >= 2:
        return f"+{int(round((d - 1) * 100))}"
    return f"-{int(round(100 / (d - 1)))}"


def monte_carlo(
    decimal_odds: float,
    win_prob: float,
    stake: float,
    n_bets: int,
    bankroll: float,
    trials: int = 500,
    antithetic: bool = True,
    stratified: bool = False,
) -> dict:
    """
    Monte Carlo with optional:
      - antithetic variates (u with 1-u)
      - stratified sampling on first-bet uniform (strata across [0,1])
    """
    trials = max(50, min(int(trials), 3000))
    n = max(0, int(n_bets))
    finals = []
    busts = 0

    def run_with(us: List[float]) -> float:
        br = float(bankroll)
        for u in us:
            if br < stake or stake <= 0:
                break
            if u < win_prob:
                br += stake * (decimal_odds - 1)
            else:
                br -= stake
        return br

    if stratified:
        # stratify first-bet U; remaining bets plain RNG
        strata = max(10, min(trials, 100))
        per = max(1, trials // strata)
        for s in range(strata):
            lo, hi = s / strata, (s + 1) / strata
            for j in range(per):
                rng = random.Random(5000 + s * 1000 + j)
                u0 = lo + (hi - lo) * rng.random()
                us = [u0] + [rng.random() for _ in range(max(0, n - 1))]
                f = run_with(us)
                finals.append(f)
                if f <= bankroll * 0.05:
                    busts += 1
                if antithetic:
                    us_a = [1.0 - u for u in us]
                    f2 = run_with(us_a)
                    finals.append(f2)
                    if f2 <= bankroll * 0.05:
                        busts += 1
    else:
        i = 0
        target = trials if not antithetic else trials + (trials % 2)
        while i < target:
            rng = random.Random(1000 + i * 17)
            us = [rng.random() for _ in range(n)]
            f1 = run_with(us)
            finals.append(f1)
            if f1 <= bankroll * 0.05:
                busts += 1
            i += 1
            if antithetic and i < target:
                f2 = run_with([1.0 - u for u in us])
                finals.append(f2)
                if f2 <= bankroll * 0.05:
                    busts += 1
                i += 1

    finals.sort()
    def pct(p):
        return finals[min(len(finals) - 1, int(p * (len(finals) - 1)))]
    mean = sum(finals) / len(finals)
    var = sum((x - mean) ** 2 for x in finals) / max(1, len(finals) - 1)
    return {
        "trials": len(finals),
        "antithetic": antithetic,
        "stratified": stratified,
        "median_final": round(pct(0.5), 2),
        "p05": round(pct(0.05), 2),
        "p95": round(pct(0.95), 2),
        "mean_final": round(mean, 2),
        "std_final": round(math.sqrt(max(0, var)), 2),
        "bust_rate_pct": round(busts / len(finals) * 100, 2),
        "start_bankroll": bankroll,
        "n_bets": n_bets,
        "stake": stake,
    }


def poisson_pmf(k: int, lam: float) -> float:
    if lam < 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 8) -> dict:
    lambda_home = max(0.05, float(lambda_home))
    lambda_away = max(0.05, float(lambda_away))
    max_goals = max(3, min(int(max_goals), 12))
    p_home = p_draw = p_away = 0.0
    best = (0, 0, -1.0)
    matrix = []
    for h in range(max_goals + 1):
        row = []
        ph = poisson_pmf(h, lambda_home)
        for a in range(max_goals + 1):
            p = ph * poisson_pmf(a, lambda_away)
            row.append(round(p, 5))
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p
            if p > best[2]:
                best = (h, a, p)
        matrix.append(row)
    return {
        "lambda_home": lambda_home, "lambda_away": lambda_away,
        "p_home": round(p_home, 4), "p_draw": round(p_draw, 4), "p_away": round(p_away, 4),
        "most_likely_score": f"{best[0]}-{best[1]}", "most_likely_p": round(best[2], 4),
        "matrix": matrix,
    }


def poisson_total_over_prob(lambda_home: float, lambda_away: float, line: float, max_goals: int = 12) -> dict:
    lam = max(0.05, float(lambda_home) + float(lambda_away))
    line = float(line)
    p_over = p_under = p_push = 0.0
    for t in range(0, max_goals + 1):
        p = poisson_pmf(t, lam)
        if t > line:
            p_over += p
        elif t < line:
            p_under += p
        else:
            p_push += p
    return {"lambda_total": round(lam, 3), "line": line,
            "p_over": round(p_over, 4), "p_under": round(p_under, 4), "p_push": round(p_push, 4)}


def lambdas_from_form(games: List[dict], team_name: str = "") -> dict:
    """
    Estimate λ from recent completed scores (points/goals per game).
    Uses team side when name matches; else league-average split.
    """
    scored = []
    allowed = []
    tn = (team_name or "").lower()
    for g in games or []:
        try:
            hs = float(g.get("home_score") if g.get("home_score") not in (None, "", "–") else 0)
            as_ = float(g.get("away_score") if g.get("away_score") not in (None, "", "–") else 0)
        except (TypeError, ValueError):
            continue
        if g.get("status_state") == "in":
            continue
        # only finals-ish
        status = (g.get("status") or g.get("detail") or "").lower()
        if status and ("schedule" in status or "pre" in status):
            continue
        home = (g.get("home_team") or "").lower()
        away = (g.get("away_team") or "").lower()
        if tn and tn in home:
            scored.append(hs)
            allowed.append(as_)
        elif tn and tn in away:
            scored.append(as_)
            allowed.append(hs)
        else:
            scored.append(hs)
            allowed.append(as_)
            scored.append(as_)
            allowed.append(hs)
    if not scored:
        return {"lambda_for": 1.2, "lambda_against": 1.2, "n": 0, "source": "default"}
    # map points → poisson λ scale (soccer-ish); for NFL/NBA use /scale
    avg_for = sum(scored) / len(scored)
    avg_ag = sum(allowed) / len(allowed)
    # heuristic scale so λ stays in a usable range for the toy model
    scale = 1.0
    if avg_for > 15:  # basketball / football points
        scale = max(avg_for / 2.5, 1.0)
        lam_for = max(0.3, avg_for / scale)
        lam_ag = max(0.3, avg_ag / scale)
    else:
        lam_for = max(0.3, avg_for)
        lam_ag = max(0.3, avg_ag)
    return {
        "lambda_for": round(lam_for, 3),
        "lambda_against": round(lam_ag, 3),
        "avg_scored": round(avg_for, 2),
        "avg_allowed": round(avg_ag, 2),
        "n": len(scored),
        "source": "recent-form",
    }


def kalman_1d(observations: Sequence[float], process_var: float = 0.5, measure_var: float = 2.0) -> dict:
    """
    Simple 1D Kalman filter — smooth a series (e.g. scoring rates / odds implied).
    x_k = x_{k-1} + w,  z_k = x_k + v
    """
    obs = [float(x) for x in observations if x is not None]
    if not obs:
        return {"smoothed": [], "error": "no data"}
    x = obs[0]
    p = 1.0
    q = max(1e-6, float(process_var))
    r = max(1e-6, float(measure_var))
    smoothed = []
    for z in obs:
        # predict
        p = p + q
        # update
        k = p / (p + r)
        x = x + k * (z - x)
        p = (1 - k) * p
        smoothed.append(round(x, 4))
    return {
        "smoothed": smoothed,
        "final": smoothed[-1],
        "n": len(obs),
        "process_var": q,
        "measure_var": r,
    }


def parlay_monte_carlo(leg_decimals, leg_probs, stake, bankroll, trials=500) -> dict:
    if not leg_decimals or len(leg_decimals) != len(leg_probs):
        return {"error": "Need matching odds and probs per leg"}
    trials = max(50, min(int(trials), 3000))
    dec = parlay_decimal(leg_decimals)
    if dec <= 1:
        return {"error": "Invalid leg odds"}
    rng = random.Random(42)
    wins = 0
    profit_list = []
    for _ in range(trials):
        ok = all(rng.random() < p for p in leg_probs)
        if ok:
            wins += 1
            profit_list.append(stake * (dec - 1))
        else:
            profit_list.append(-stake)
    return {
        "parlay_decimal": round(dec, 3),
        "parlay_american_approx": _dec_to_amer(dec),
        "win_rate_pct": round(wins / trials * 100, 2),
        "avg_profit": round(sum(profit_list) / trials, 2),
        "trials": trials, "stake": stake, "bankroll": bankroll,
    }


def sandbox_single_summary(american, win_prob, stake, bankroll) -> dict:
    dec = american_to_decimal(american)
    if not dec:
        return {"error": "Invalid American odds"}
    win_prob = max(0.01, min(0.99, float(win_prob)))
    stake = max(0.0, float(stake))
    bankroll = max(1.0, float(bankroll))
    imp = implied_prob(dec)
    edge = win_prob - imp
    return {
        "decimal": round(dec, 3),
        "implied_prob": round(imp, 4),
        "your_prob": win_prob,
        "edge": round(edge, 4),
        "kelly_ladder": fractional_kelly_ladder(dec, win_prob, bankroll),
        "monte_carlo_50_bets": monte_carlo(dec, win_prob, stake, 50, bankroll, 400, True, False),
        "fair_bet": edge > 0,
    }


def intriguing_idea(games_odds: List[dict], form_games: List[dict], team_name: str) -> str:
    """Pick a short value-oriented idea from odds dispersion / form."""
    from .betting_tools import price_dispersion, implied_edge_table
    ideas = []
    try:
        disp = price_dispersion(games_odds or [])
        if disp:
            top = disp[0]
            ideas.append(
                f"Dispersion play: **{top.get('outcome')}** in {top.get('matchup')} shows "
                f"{top.get('dispersion_pct')}% book disagreement (best dec {top.get('best_dec')})."
            )
        edges = implied_edge_table(games_odds or [])
        for e in edges:
            if float(e.get("implied_sum") or 99) < 0.98:
                ideas.append(
                    f"Math edge snapshot: {e.get('matchup')} best-price implied sum "
                    f"{e.get('implied_sum')} (edge ~ {e.get('market_edge_pct')}%)."
                )
                break
    except Exception:
        pass
    try:
        lam = lambdas_from_form(form_games or [], team_name)
        if lam.get("n", 0) >= 2:
            ideas.append(
                f"Form-based Poisson λ for {team_name}: for {lam['lambda_for']} / against {lam['lambda_against']} "
                f"(n={lam['n']} scored-rate samples)."
            )
    except Exception:
        pass
    if not ideas:
        ideas.append(
            f"Keep powder dry on {team_name}: no strong cross-book edge in the current snapshot — "
            "revisit after the next line move."
        )
    # rotate by day
    from datetime import datetime
    i = datetime.utcnow().timetuple().tm_yday % len(ideas)
    return ideas[i]
