"""
Bayesian hierarchical Poisson helpers for team scoring rates.
Lightweight / educational — no PyMC dependency.

Models:
  1) Gamma–Poisson conjugate update for a single rate λ
  2) Empirical-Bayes hierarchical shrinkage of team rates toward a league mean
  3) Independent Poisson match probabilities using shrunk λs

Not a full MCMC Dixon–Coles engine; a transparent teaching approximation.
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional, Sequence, Tuple


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0 or lam < 0:
        return 0.0
    if lam == 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


# ---------------------------------------------------------------------------
# Conjugate Gamma–Poisson
# Prior: λ ~ Gamma(a, b)  with mean a/b  (rate parameterization)
# Likelihood: y_i | λ ~ Poisson(λ)  (per-period counts; exposure t optional)
# Posterior: λ | y ~ Gamma(a + sum y, b + n)   for unit exposures
# ---------------------------------------------------------------------------

def gamma_poisson_update(
    counts: Sequence[float],
    a_prior: float = 2.0,
    b_prior: float = 1.5,
    exposures: Optional[Sequence[float]] = None,
) -> dict:
    """
    Conjugate update for Poisson rate with Gamma prior.
    a,b use rate parameterization: mean = a/b, var = a/b^2.
    """
    ys = [max(0.0, float(y)) for y in counts]
    n = len(ys)
    if n == 0:
        mean = a_prior / b_prior if b_prior else 0.0
        return {
            "a_post": a_prior, "b_post": b_prior,
            "mean": round(mean, 4), "mode": round(max(0.0, (a_prior - 1) / b_prior), 4) if a_prior >= 1 else 0.0,
            "sd": round(math.sqrt(a_prior / (b_prior ** 2)), 4) if b_prior else 0.0,
            "n": 0, "prior_mean": round(a_prior / b_prior, 4) if b_prior else 0.0,
        }
    if exposures is None:
        exp = [1.0] * n
    else:
        exp = [max(1e-6, float(t)) for t in exposures]
        if len(exp) != n:
            exp = [1.0] * n
    a_post = a_prior + sum(ys)
    b_post = b_prior + sum(exp)
    mean = a_post / b_post
    var = a_post / (b_post ** 2)
    mode = max(0.0, (a_post - 1) / b_post) if a_post >= 1 else 0.0
    return {
        "a_post": round(a_post, 4),
        "b_post": round(b_post, 4),
        "mean": round(mean, 4),
        "mode": round(mode, 4),
        "sd": round(math.sqrt(max(0.0, var)), 4),
        "n": n,
        "prior_mean": round(a_prior / b_prior, 4) if b_prior else 0.0,
        "sample_mean": round(sum(ys) / sum(exp), 4),
    }


# ---------------------------------------------------------------------------
# Empirical Bayes hierarchical shrinkage
# Team rates θ_i drawn from league population; shrink MLE toward grand mean.
# James–Stein style / EB: θ̂_i = μ + (1-B)(ȳ_i - μ)
# B ≈ σ²_noise / (σ²_noise + τ²) estimated from between-team dispersion
# ---------------------------------------------------------------------------

def empirical_bayes_rates(
    team_rates: Dict[str, float],
    team_games: Optional[Dict[str, int]] = None,
    global_var_floor: float = 0.05,
) -> dict:
    """
    Shrink observed team scoring rates toward the grand mean.
    team_rates: name -> goals/points per game (or λ proxy)
    team_games: optional sample sizes for weighting
    """
    if not team_rates:
        return {"teams": {}, "mu": 0.0, "B": 1.0, "tau2": 0.0}
    names = list(team_rates.keys())
    ys = [float(team_rates[n]) for n in names]
    ns = [max(1, int((team_games or {}).get(n, 3))) for n in names]
    # grand mean (game-weighted)
    mu = sum(y * n for y, n in zip(ys, ns)) / sum(ns)
    # crude between-team variance
    between = sum(n * (y - mu) ** 2 for y, n in zip(ys, ns)) / max(1, sum(ns))
    # within noise ~ mu/n for Poisson-ish (var of mean = λ/n)
    within = [max(global_var_floor, mu / n) for n in ns]
    avg_within = sum(within) / len(within)
    tau2 = max(0.0, between - avg_within)
    results = {}
    for name, y, n, w in zip(names, ys, ns, within):
        # shrinkage factor toward mu for this team
        B = w / (w + tau2) if (w + tau2) > 0 else 1.0
        theta = mu + (1 - B) * (y - mu)
        results[name] = {
            "observed": round(y, 4),
            "shrunk": round(theta, 4),
            "games": n,
            "B_shrinkage": round(B, 4),
            "pull_toward_mean": round(mu - y, 4),
        }
    return {
        "mu": round(mu, 4),
        "tau2": round(tau2, 4),
        "avg_within": round(avg_within, 4),
        "teams": results,
    }


def hierarchical_match_preview(
    lambda_home_att: float,
    lambda_away_att: float,
    lambda_home_def: float,
    lambda_away_def: float,
    home_advantage: float = 1.08,
    max_goals: int = 7,
) -> dict:
    """
    Hierarchical-style λ composition:
      λ_home = att_home * def_away * home_adv
      λ_away = att_away * def_home
    Then independent Poisson scoreline probs.
    Rates should be scaled so product is on goal-count scale (~0.5–2.5 soccer).
    """
    lh = max(0.05, float(lambda_home_att) * float(lambda_away_def) * float(home_advantage))
    la = max(0.05, float(lambda_away_att) * float(lambda_home_def))
    # normalize if someone passed raw PPG for NBA etc.
    if lh > 8 or la > 8:
        scale = max(lh, la) / 2.2
        lh, la = lh / scale, la / scale
    p_home = p_draw = p_away = 0.0
    best = (0, 0, -1.0)
    for h in range(max_goals + 1):
        ph = poisson_pmf(h, lh)
        for a in range(max_goals + 1):
            p = ph * poisson_pmf(a, la)
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p
            if p > best[2]:
                best = (h, a, p)
    return {
        "lambda_home": round(lh, 3),
        "lambda_away": round(la, 3),
        "p_home": round(p_home, 4),
        "p_draw": round(p_draw, 4),
        "p_away": round(p_away, 4),
        "most_likely": f"{best[0]}-{best[1]}",
        "most_likely_p": round(best[2], 4),
        "home_advantage": home_advantage,
    }


def rates_from_form_games(games: List[dict], team_name: str = "") -> Tuple[List[float], List[float]]:
    """Extract scored / allowed lists for conjugate updates from form payload."""
    scored, allowed = [], []
    tn = (team_name or "").lower()
    for g in games or []:
        try:
            hs = float(g.get("home_score") if g.get("home_score") not in (None, "", "–") else 0)
            as_ = float(g.get("away_score") if g.get("away_score") not in (None, "", "–") else 0)
        except (TypeError, ValueError):
            continue
        home = (g.get("home_team") or "").lower()
        away = (g.get("away_team") or "").lower()
        if tn and tn in home:
            scored.append(hs)
            allowed.append(as_)
        elif tn and tn in away:
            scored.append(as_)
            allowed.append(hs)
        elif not tn:
            scored.append(hs)
            allowed.append(as_)
    return scored, allowed
