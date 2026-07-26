"""
Dynamic team-themed CSS — light/dark + mobile + 1960s baseball cards + watermark hook.
All literal braces in CSS are doubled for f-string safety.
"""
from __future__ import annotations

from .api_client import TEAMS


def build_css(team_key: str, dark: bool = False) -> str:
    c = TEAMS.get(team_key, TEAMS["browns"])["colors"]
    if dark:
        bg, card, text, muted = c["dark_bg"], c["dark_card"], "#F5F0EB", "#B8A99A"
        border, shadow = "rgba(255,255,255,0.08)", "0 8px 32px rgba(0,0,0,0.45)"
        header_grad = f"linear-gradient(135deg, {c['primary']} 0%, {c['secondary']} 100%)"
    else:
        bg, card, text, muted = c["light_bg"], c["light_card"], "#1A1410", "#5C5346"
        border, shadow = "rgba(0,0,0,0.06)", "0 8px 28px rgba(0,0,0,0.08)"
        header_grad = f"linear-gradient(135deg, {c['primary']}ee 0%, {c['secondary']}dd 100%)"
    primary = c["primary"]
    secondary = c["secondary"]
    accent = c.get("accent", "#FFFFFF")

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {bg} !important;
        color: {text} !important;
        font-family: 'Outfit', system-ui, sans-serif !important;
    }}
    .stApp {{ background: {bg} !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .sbsby-banner {{
        background: {header_grad};
        color: {accent};
        padding: 1.1rem 1.4rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: {shadow};
        position: relative;
        overflow: hidden;
    }}
    .sbsby-banner h1 {{
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .sbsby-banner .subtitle {{
        margin: 0.3rem 0 0;
        font-size: 0.9rem;
        font-weight: 500;
        opacity: 0.92;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}
    .live-dot {{
        display: inline-block;
        width: 9px;
        height: 9px;
        background: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse-dot 1.2s ease-in-out infinite;
    }}
    @keyframes pulse-dot {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.45; transform: scale(0.85); }}
    }}
    .sbsby-card {{
        background: {card};
        border: 1px solid {border};
        border-left: 4px solid {primary};
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.85rem;
        box-shadow: {shadow};
    }}
    .score-card {{
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 0.5rem 0.75rem;
        width: 100%;
        max-width: 100%;
        overflow: hidden;
        box-sizing: border-box;
    }}
    .team-block {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 0;
        max-width: 100%;
        overflow: hidden;
    }}
    .team-block .logo {{
        width: 36px;
        height: 36px;
        object-fit: contain;
        margin-bottom: 0.25rem;
        border-radius: 6px;
    }}
    .team-block .name {{
        font-weight: 600;
        font-size: 0.82rem;
        margin-top: 0.2rem;
        text-align: center;
        line-height: 1.2;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: inherit;
    }}
    .team-block .score {{
        font-size: clamp(1.35rem, 4vw, 1.85rem);
        font-weight: 800;
        font-family: 'JetBrains Mono', ui-monospace, monospace;
        color: {primary};
        line-height: 1.1;
        letter-spacing: -0.02em;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    .score-mid {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 4.5rem;
        max-width: 7rem;
        padding: 0 0.25rem;
    }}
    .vs-pill {{
        background: {primary}22;
        color: {primary};
        border: 1px solid {primary}44;
        border-radius: 999px;
        padding: 0.25rem 0.65rem;
        font-weight: 700;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
    }}
    .status-badge {{
        display: inline-block;
        background: {secondary}33;
        color: {secondary};
        border-radius: 8px;
        padding: 0.18rem 0.45rem;
        font-size: 0.68rem;
        font-weight: 600;
        margin-top: 0.35rem;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        text-align: center;
    }}
    .status-badge.live {{
        background: #e11d4833;
        color: #e11d48;
        animation: pulse 1.6s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.65; }}
    }}
    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {primary};
        margin: 1.2rem 0 0.65rem;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }}
    .section-title::before {{
        content: '';
        width: 4px;
        height: 1.1em;
        background: {secondary};
        border-radius: 2px;
    }}
    .news-meta {{
        font-size: 0.76rem;
        color: {muted};
        margin-top: 0.2rem;
    }}
    .metric-pill {{
        background: {primary}12;
        border: 1px solid {primary}28;
        border-radius: 12px;
        padding: 0.5rem 0.85rem;
        min-width: 90px;
    }}
    .metric-pill .label {{
        font-size: 0.7rem;
        color: {muted};
        text-transform: uppercase;
    }}
    .metric-pill .value {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {primary};
        font-family: 'JetBrains Mono', monospace;
    }}
    .pred-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 0.65rem;
    }}
    .pred-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 0.85rem;
        text-decoration: none !important;
        color: {text} !important;
    }}
    .pred-card strong {{ color: {primary}; display: block; }}
    .pred-card span {{ font-size: 0.78rem; color: {muted}; }}
    .odds-chip {{
        display: inline-block;
        background: {primary}14;
        border: 1px solid {primary}30;
        border-radius: 8px;
        padding: 0.22rem 0.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.12rem 0.2rem;
        color: {primary};
    }}
    .odds-book {{ font-size: 0.76rem; color: {muted}; margin-top: 0.3rem; }}
    [data-testid="stSidebar"] {{
        background: {card} !important;
        border-right: 1px solid {border};
    }}
    .stButton > button {{
        background: {primary} !important;
        color: {accent} !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    .score-meta {{
        margin-top: 0.55rem;
        font-size: 0.68rem;
        color: {muted};
        text-align: center;
        line-height: 1.35;
        word-break: break-word;
    }}
    .source-badge {{
        font-size: 0.68rem;
        color: {muted};
        font-family: 'JetBrains Mono', monospace;
    }}
    .empty-state {{
        text-align: center;
        padding: 1.25rem;
        color: {muted};
    }}
    .bb-card {{
        width: 100%;
        max-width: 320px;
        margin: 0.5rem auto 1rem;
        background: linear-gradient(160deg, #f7f0e0 0%, #ebe2cc 55%, #e0d5b8 100%);
        border: 8px solid {primary};
        outline: 3px solid {secondary};
        outline-offset: 2px;
        border-radius: 6px;
        box-shadow: 4px 6px 0 rgba(0,0,0,0.25), 0 12px 28px rgba(0,0,0,0.12);
        padding: 0.65rem 0.75rem 0.85rem;
        color: #1a1410;
        font-family: 'Outfit', Georgia, serif;
        position: relative;
    }}
    .bb-card::before {{
        content: 'SO!SB!Y! CLASSIC';
        position: absolute;
        top: 6px;
        right: 10px;
        font-size: 0.55rem;
        letter-spacing: 0.12em;
        color: {primary};
        font-weight: 700;
    }}
    .bb-card .bb-photo {{
        width: 100%;
        aspect-ratio: 4/5;
        object-fit: cover;
        object-position: top;
        border: 3px solid #3a3020;
        background: #cfc4a8;
        display: block;
    }}
    .bb-card .bb-name {{
        text-align: center;
        font-size: 1.15rem;
        font-weight: 800;
        margin: 0.45rem 0 0.15rem;
        color: {primary};
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .bb-card .bb-team {{
        text-align: center;
        font-size: 0.75rem;
        font-weight: 600;
        color: #4a4030;
        margin-bottom: 0.35rem;
    }}
    .bb-card .bb-stats {{
        background: rgba(0,0,0,0.06);
        border-radius: 4px;
        padding: 0.4rem 0.5rem;
        font-size: 0.72rem;
        line-height: 1.45;
        margin-top: 0.35rem;
    }}
    .bb-card .bb-anecdote {{
        font-size: 0.7rem;
        font-style: italic;
        color: #3a3228;
        margin-top: 0.4rem;
        border-top: 1px dashed #9a8c70;
        padding-top: 0.35rem;
        line-height: 1.4;
    }}
    .bb-card .bb-years {{
        display: inline-block;
        background: {secondary};
        color: #fff;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 0.12rem 0.4rem;
        border-radius: 3px;
    }}
    @media (max-width: 640px) {{
        .sbsby-banner h1 {{ font-size: 1.2rem !important; }}
        .team-block .score {{ font-size: 1.25rem !important; }}
        .score-card {{ gap: 0.35rem; }}
        .team-block .name {{ font-size: 0.72rem !important; }}
        .bb-card .bb-photo {{ width: 100%; }}
    }}
    </style>
    """


def inject_css(team_key: str, dark: bool) -> None:
    import streamlit as st
    st.markdown(build_css(team_key, dark), unsafe_allow_html=True)
    try:
        from .branding import watermark_data_uri
        uri = watermark_data_uri()
        st.markdown(
            f"""<style>
            .stApp::before {{
                content: '';
                position: fixed;
                inset: 0;
                background: url('{uri}') center center / min(55vw, 420px) no-repeat;
                opacity: 0.07;
                pointer-events: none;
                z-index: 0;
            }}
            [data-testid="stAppViewContainer"] > .main {{ position: relative; z-index: 1; }}
            </style>""",
            unsafe_allow_html=True,
        )
    except Exception:
        pass
