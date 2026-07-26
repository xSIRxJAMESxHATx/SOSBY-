"""WebGL-backed 3D visualizations via Plotly (browser WebGL)."""
from __future__ import annotations
from typing import List, Optional
import plotly.graph_objects as go
import plotly.express as px


def form_3d_scatter(rows: List[dict], title: str = "Form space") -> Optional[go.Figure]:
    """3D scatter: Date index × home score × away score."""
    if not rows or len(rows) < 2:
        return None
    xs, ys, zs, labels = [], [], [], []
    for i, g in enumerate(rows):
        try:
            hs = float(g.get("home_score") or g.get("Home") or 0)
            as_ = float(g.get("away_score") or g.get("Away") or 0)
        except (TypeError, ValueError):
            continue
        xs.append(i)
        ys.append(hs)
        zs.append(as_)
        labels.append(str(g.get("Matchup") or g.get("name") or f"G{i}"))
    if len(xs) < 2:
        return None
    fig = go.Figure(data=[go.Scatter3d(
        x=xs, y=ys, z=zs, mode="markers+lines",
        text=labels,
        marker=dict(size=6, color=zs, colorscale="Oranges", opacity=0.9),
        line=dict(color="#888", width=2),
    )])
    fig.update_layout(
        title=title,
        height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(
            xaxis_title="Game #",
            yaxis_title="Home",
            zaxis_title="Away",
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    return fig


def poisson_surface(lambda_h: float, lambda_a: float, max_g: int = 6) -> go.Figure:
    """3D surface of independent Poisson joint probabilities."""
    import math
    def pmf(k, lam):
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
    z = []
    for h in range(max_g + 1):
        row = []
        for a in range(max_g + 1):
            row.append(pmf(h, lambda_h) * pmf(a, lambda_a))
        z.append(row)
    fig = go.Figure(data=[go.Surface(z=z, colorscale="Viridis", showscale=True)])
    fig.update_layout(
        title=f"Poisson joint P(H,A) λh={lambda_h:.2f} λa={lambda_a:.2f}",
        height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(xaxis_title="Away", yaxis_title="Home", zaxis_title="P"),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def monte_carlo_paths_3d(paths: List[List[float]]) -> Optional[go.Figure]:
    """Plot a sample of bankroll paths in 3D (trial × step × bankroll)."""
    if not paths:
        return None
    fig = go.Figure()
    for i, path in enumerate(paths[:40]):
        fig.add_trace(go.Scatter3d(
            x=list(range(len(path))),
            y=[i] * len(path),
            z=path,
            mode="lines",
            line=dict(width=2),
            showlegend=False,
            opacity=0.55,
        ))
    fig.update_layout(
        title="Monte Carlo bankroll paths (sample)",
        height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(xaxis_title="Bet #", yaxis_title="Trial", zaxis_title="Bankroll"),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
