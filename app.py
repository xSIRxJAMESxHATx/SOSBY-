"""
SO!SB!Y! V2.0 — Superb Owl! Super Browns! Yeah!
Modular, lazy-loaded, and mobile-optimized.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# V2 Error Handler
from utils.error_handler import safe_render

# Existing Utilities
from utils.api_client import TEAMS, get_client, reddit_url
from utils.theme import inject_css
from utils.api_extras import (
    get_roster, get_all_time_leaders, get_championship_greats,
    get_player_card, enrich_team_cfg,
)
from utils.curated_data import DEFAULT_RUSHMORE, PLAYER_POOL
from utils.rushmore import rushmore_to_bytes
from utils.betting_tools import (
    detect_arbitrage, bankroll_plan, kelly_fraction, full_kelly_table,
    LIVE_ARB_STRATEGIES, STAT_ARB_MODELS, price_dispersion, implied_edge_table, american_to_decimal
)
from utils.media_sources import get_media_for_team
from utils.cartoon import cartoon_data_uri
from utils.team_flavor import get_flavor
from utils.weather import fetch_weather, map_links, weather_cartoon
from utils.community import (
    list_topics, create_topic, add_post, vote, delete_post, delete_topic,
    list_users, avatar_url, AVATAR_PRESETS, moderate_text, supabase_configured,
)
from utils.twilio_sms import twilio_configured, send_sms, SETUP_HELP
from utils.chatbot import reply as bot_reply
from utils.moments_tickets import moments_for, ticket_links
from utils.betting_sandbox import (
    sandbox_single_summary, parlay_monte_carlo, poisson_score_matrix, 
    poisson_total_over_prob, monte_carlo, lambdas_from_form, kalman_1d
)
from utils.bet_journal import add_entry, list_entries, clear_all, summary_stats, to_csv
from utils.pdf_export import export_team_pdf
from utils.scorecard import render_score_card, format_score_pair, format_score
from utils.ws_feeds import probe_websocket, sports_ws_candidates, get_owner_ws, merge_ws_payload_into_games, live_score_tick
from utils.viz3d import form_3d_scatter, poisson_surface
from utils.errors import safe_call, format_feed_status
from utils.bayes_poisson import (
    gamma_poisson_update, empirical_bayes_rates,
    hierarchical_match_preview, rates_from_form_games,
)

# V2 Page Config
st.set_page_config(page_title="SO!SB!Y!", page_icon="assets/favicon.ico", layout="wide", initial_sidebar_state="collapsed")

# V2 CSS Injection
def load_css():
    try:
        with open("styles/theme.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass
load_css()

# Inject Secrets
for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "MOD_PASSWORD", "ODDS_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_ANON_KEY"):
    try:
        val = st.secrets.get(key, "")
        if val and not os.environ.get(key):
            os.environ[key] = str(val)
    except Exception:
        pass

# Initialize Session State
for k, v in {
    "team_key": "browns", "dark_mode": False, "auto_refresh": True,
    "refresh_sec": 45, "odds_key_input": "", "selected_player": None,
    "rushmore_picks": None, "show_sources": False, "username": "Fan",
    "avatar_preset": "initials", "chat_log": []
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Globals
client = get_client()
odds_key = st.session_state.odds_key_input or os.environ.get("ODDS_API_KEY", "")
if odds_key:
    client.set_odds_key(odds_key)

team_key = st.session_state.team_key
team = TEAMS[team_key]
team_cfg = enrich_team_cfg(team_key, team)
flavor = get_flavor(team_key)

def src_note(s: str) -> None:
    if st.session_state.show_sources:
        st.caption(f"source: {s}")

# --- V2 SIDEBAR (Hamburger Menu) ---
with st.sidebar:
    st.markdown("## ☰ Navigation")
    try:
        st.image("assets/Copilot_20260726_103333.png", use_container_width=True)
    except Exception:
        pass
    
    st.markdown("### Team Selection")
    team_options = {v["short"]: k for k, v in TEAMS.items()}
    labels = list(team_options.keys())
    try:
        idx = list(team_options.values()).index(team_key)
    except ValueError:
        idx = 0
    sel = st.selectbox("🏈 Team", labels, index=idx)
    new_key = team_options[sel]
    if new_key != st.session_state.team_key:
        st.session_state.team_key = new_key
        st.session_state.selected_player = None
        st.rerun()
        
    st.session_state.auto_refresh = st.toggle("🔄 Auto-update", st.session_state.auto_refresh)
    st.session_state.refresh_sec = st.slider("Refresh seconds", 30, 90, st.session_state.refresh_sec, 5)

if st.session_state.auto_refresh and st_autorefresh:
    st_autorefresh(interval=int(st.session_state.refresh_sec) * 1000, key="sbsby_auto")

# --- V2 HERO SECTION ---
live = False
try:
    live = client.any_live_games(team_key)
except Exception:
    pass
live_text = '<span style="color:red;">● LIVE</span>' if live else "Hub"

st.markdown(f"""
<div class="hero-section">
    <h1>Superb Owl</h1>
    <h2>Super {team.get('short')} Yeah</h2>
    <p>Your complete {team.get('name')} command center. · {live_text}</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**{flavor.get('slogan','')}** — _{flavor.get('witty','')}_")
if flavor.get("phrases"):
    st.caption(" · ".join(flavor["phrases"][:8]))

# Fetch info and metrics
try:
    info, info_src = client.get_team_info(team_key)
except Exception:
    info, info_src = {"record": "—", "logo": None}, "err"
record = info.get("record") or "—"

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-pill"><div class="label">Record</div><div class="value">{record}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-pill"><div class="label">League</div><div class="value">{team["league"].replace("-"," ").upper()[:18]}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-pill"><div class="label">Access</div><div class="value">READ-ONLY</div></div>', unsafe_allow_html=True)
with m4:
    if st.button("↻ Refresh Data", use_container_width=True):
        try:
            client.clear_cache()
        except Exception:
            pass
        st.rerun()

# --- V2 TABS (Lazy Loaded) ---
tab_gameday, tab_analytics, tab_betting, tab_fanzone, tab_settings = st.tabs([
    "🏈 Game Day", "📊 Analytics", "💰 Betting", "🦉 Fan Zone", "⚙️ Settings"
])

# ==========================================
# 🏈 GAME DAY
# ==========================================
with tab_gameday:
    gd_scores, gd_weather, gd_news, gd_schedule = st.tabs(["Scores", "Weather", "News", "Schedule"])

    @safe_render("Scores")
    def render_scores():
        st.markdown('<div class="section-title">Live Scores</div>', unsafe_allow_html=True)
        try:
            st.markdown(f"[Reddit: {team.get('short')}]({reddit_url(team_key)})")
        except Exception:
            pass
        
        if st.session_state.get("auto_refresh"):
            tick = live_score_tick(client, team_key)
            games, src = tick.get("games") or [], tick.get("source") or "tick"
            if tick.get("empty"): st.caption("Waiting for score feed…")
        else:
            games, src = client.get_scoreboard(team_key)
            
        try:
            games = merge_ws_payload_into_games(games or [])
        except Exception:
            pass
            
        if not games:
            st.markdown('<div class="sbsby-card empty-state">Scores temporarily unavailable.</div>', unsafe_allow_html=True)
            
        for g in (games or []):
            st.markdown(render_score_card(g), unsafe_allow_html=True)
        src_note(src)

    @safe_render("Weather")
    def render_weather():
        st.markdown('<div class="section-title">Venue Weather</div>', unsafe_allow_html=True)
        wx, wsrc = fetch_weather(team_key)
        wc1, wc2 = st.columns([1, 1])
        with wc1:
            st.metric("Temperature", f"{wx.get('temp_f')} °F")
            st.metric("Conditions", str(wx.get("summary") or "—"))
            st.caption(f"Wind {wx.get('wind_mph')} mph · Humidity {wx.get('humidity')}% · Precip {wx.get('precip')}")
            try:
                st.image(weather_cartoon(str(wx.get("summary") or ""), wx.get("temp_f"), float(wx.get("lat") or 41.5)), use_container_width=True)
            except Exception: pass
        with wc2:
            st.markdown("**Maps (satellite / place)**")
            for m in map_links(float(wx.get("lat") or 41.5), float(wx.get("lon") or -81.7)):
                st.markdown(f"- [{m['name']}]({m['url']})")
        src_note(wsrc)

    @safe_render("News")
    def render_news():
        st.markdown('<div class="section-title">News</div>', unsafe_allow_html=True)
        arts, src = client.get_news(team_key, 16)
        if not arts: st.info("No headlines right now.")
        for a in arts:
            st.markdown(f"**[{a.get('headline')}]({a.get('url') or '#'})**")
            st.caption(" · ".join(filter(None, [a.get("source") or "", (a.get("published") or "")[:16]])))
        src_note(src)
        
    @safe_render("Schedule")
    def render_schedule():
        st.markdown('<div class="section-title">Schedule</div>', unsafe_allow_html=True)
        games, src = client.get_schedule(team_key)
        rows = []
        for g in games or []:
            rows.append({
                "When": (g.get("date") or "")[:16].replace("T", " "),
                "Matchup": g.get("name") or f"{g.get('away_team','')} @ {g.get('home_team','')}",
                "Venue": g.get("venue") or "",
                "Status": g.get("status") or g.get("detail") or "",
                "Score": format_score_pair(g.get("away_score"), g.get("home_score")),
            })
        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        src_note(src)

    with gd_scores: render_scores()
    with gd_weather: render_weather()
    with gd_news: render_news()
    with gd_schedule: render_schedule()

# ==========================================
# 📊 ANALYTICS
# ==========================================
with tab_analytics:
    an_standings, an_trends, an_leaders, an_players = st.tabs(["Standings", "Trends", "Leaders & Greats", "Players"])

    @safe_render("Standings")
    def render_standings():
        st.markdown('<div class="section-title">Standings</div>', unsafe_allow_html=True)
        rows, src = client.get_standings(team_key)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            src_note(src)
        else:
            st.info("Standings unavailable.")

    @safe_render("Trends")
    def render_trends():
        st.markdown('<div class="section-title">Trends</div>', unsafe_allow_html=True)
        form, src = client.get_recent_form(team_key)
        if form:
            rows = [{"Matchup": g.get("name") or f"{g.get('away_team','')} @ {g.get('home_team','')}",
                     "Away": int(float(g.get("away_score") or 0)), "Home": int(float(g.get("home_score") or 0)), 
                     "Date": (g.get("date") or "")[:10]} for g in form]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            src_note(src)

    @safe_render("Leaders & Greats")
    def render_leaders():
        st.markdown('<div class="section-title">All-Time Leaders</div>', unsafe_allow_html=True)
        leaders, lsrc = get_all_time_leaders(team_key)
        if leaders:
            cat = st.selectbox("Category", list(leaders.keys()), key="lead_cat")
            st.dataframe(pd.DataFrame(leaders.get(cat) or []), use_container_width=True, hide_index=True)
            src_note(lsrc)
        
        st.markdown("### Championship Greats")
        greats, gsrc = get_championship_greats(team_key)
        for g in greats:
            st.markdown(f"**{g.get('player')}** · {g.get('era','')} — {g.get('titles','')} · _{g.get('why','')}_")

    @safe_render("Players")
    def render_players():
        st.markdown('<div class="section-title">Player Cards</div>', unsafe_allow_html=True)
        roster, rsrc = get_roster(team_cfg)
        pool = PLAYER_POOL.get(team_key, [])
        options = sorted(set([p.get("name") for p in roster if p.get("name")] + list(pool or []))) or ["(none)"]
        player = st.selectbox("Player", options, key="player_sel")
        if player and player != "(none)":
            card, csrc = get_player_card(player, team_cfg)
            thumb = card.get("cutout") or card.get("thumb") or cartoon_data_uri(player, card.get("position") or "", team.get("colors", {}).get("primary", "#311D00"))
            st.markdown(f"""
            <div class="bb-card"><img class="bb-photo" src="{thumb}" alt="p"/>
              <div class="bb-name">{card.get('name', player)}</div>
              <div class="bb-team">{card.get('team') or team.get('short')} · {card.get('position') or 'Player'}</div>
              <div class="bb-stats">{str(card.get('description') or '')[:280]}</div>
            </div>""", unsafe_allow_html=True)

    with an_standings: render_standings()
    with an_trends: render_trends()
    with an_leaders: render_leaders()
    with an_players: render_players()

# ==========================================
# 💰 BETTING
# ==========================================
with tab_betting:
    bet_hq, bet_sandbox, bet_odds, bet_journal = st.tabs(["Betting HQ", "Sandbox", "Odds", "Journal"])
    
    @safe_render("Betting HQ")
    def render_betting():
        st.markdown('<div class="section-title">Sports Betting Dashboard</div>', unsafe_allow_html=True)
        dash, dsrc = client.get_betting_dashboard(team_key)
        k1, k2, k3 = st.columns(3)
        k1.metric("Odds API", "LIVE" if dash.get("has_api_key") else "KEY NEEDED")
        k2.metric("Book games", len(dash.get("games") or []))
        k3.metric("ESPN lines", len(dash.get("espn_lines") or []))
        
        st.markdown("#### Arbitrage scan")
        if dash.get("has_api_key") and dash.get("games"):
            opps = detect_arbitrage(dash["games"])
            if opps: st.dataframe(pd.DataFrame(opps), use_container_width=True, hide_index=True)
            else: st.success("No ≥0.3% 2-way ML arb in snapshot.")
        src_note(dsrc)

    @safe_render("Sandbox")
    def render_sandbox():
        st.markdown('<div class="section-title">Bet Sandbox</div>', unsafe_allow_html=True)
        br = st.number_input("Bankroll $", min_value=10.0, value=500.0, step=25.0, key="sb_br")
        c1, c2, c3 = st.columns(3)
        amer = c1.number_input("American odds", value=150, step=10, key="sb_amer")
        wp = c2.slider("Your win %", 1, 99, 55, key="sb_wp") / 100.0
        stake = c3.number_input("Stake $", min_value=1.0, value=25.0, step=5.0, key="sb_stake")
        if st.button("Run single-bet simulation"):
            summary = sandbox_single_summary(amer, wp, stake, br)
            st.write(f"Decimal **{summary.get('decimal')}** · Edge **{summary.get('edge')}**")

    @safe_render("Odds")
    def render_odds():
        st.markdown('<div class="section-title">Odds Detail</div>', unsafe_allow_html=True)
        if not odds_key: st.info("Add Odds API key in Settings for book depth.")
        else:
            ogames, osrc = client.get_odds(team_key)
            for og in ogames or []:
                st.markdown(f"**{og.get('away_team')} @ {og.get('home_team')}**")
            src_note(osrc)

    @safe_render("Journal")
    def render_journal():
        st.markdown('<div class="section-title">Bet Journal</div>', unsafe_allow_html=True)
        with st.form("journal_form"):
            j1, j2, j3 = st.columns(3)
            side = j1.text_input("Side / pick", value=team.get("short") or "")
            odds = j2.number_input("American odds", value=-110, step=5)
            stake = j3.number_input("Stake $", min_value=0.0, value=25.0, step=5.0)
            result = st.selectbox("Result", ["Open", "Win", "Loss", "Push"])
            if st.form_submit_button("Add to journal"):
                add_entry({"team": team.get("name"), "side": side, "odds": odds, "stake": stake, "result": result, "pnl": 0.0})
                st.success("Logged")
        rows = list_entries(100)
        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with bet_hq: render_betting()
    with bet_sandbox: render_sandbox()
    with bet_odds: render_odds()
    with bet_journal: render_journal()

# ==========================================
# 🦉 FAN ZONE
# ==========================================
with tab_fanzone:
    fz_community, fz_deskbot, fz_rushmore, fz_media = st.tabs(["Community", "Desk Bot", "Rushmore", "Watch/Listen"])
    
    @safe_render("Community")
    def render_community():
        st.markdown('<div class="section-title">Community</div>', unsafe_allow_html=True)
        user = st.session_state.username or "Fan"
        with st.expander("Create topic"):
            title = st.text_input("Title (bold topic)", key="ct_title")
            body = st.text_area("Opening post", key="ct_body")
            if st.button("Post topic"):
                ok, msg = create_topic(team_key, title, user, [], body)
                st.success("Created") if ok else st.error(msg)
        topics = list_topics(team_key)
        for tpc in topics or []:
            st.markdown(f"### **{tpc.get('title')}**")
            for p in tpc.get("posts") or []:
                st.markdown(f"**{p.get('author')}**: {p.get('body')}")

    @safe_render("Desk Bot")
    def render_deskbot():
        st.markdown('<div class="section-title">Cleveland Desk Bot</div>', unsafe_allow_html=True)
        q = st.text_input("Ask the desk", key="bot_q")
        if st.button("Send") and q:
            ans, src = bot_reply(q, team_key, team.get("name") or "")
            st.session_state.chat_log.append(("you", q))
            st.session_state.chat_log.append(("bot", ans))
        for who, text in st.session_state.chat_log[-12:]:
            st.markdown(f"**{'You' if who=='you' else 'Desk'}:** {text}")

    @safe_render("Rushmore")
    def render_rushmore():
        st.markdown('<div class="section-title">Fan Mount Rushmore</div>', unsafe_allow_html=True)
        pool = list(PLAYER_POOL.get(team_key, []) or ["Legend A", "Legend B", "Legend C", "Legend D"])
        defaults = st.session_state.rushmore_picks or DEFAULT_RUSHMORE.get(team_key, pool[:4])
        cols = st.columns(4)
        picks = []
        for i, col in enumerate(cols):
            with col: picks.append(st.selectbox(f"Face {i+1}", pool, index=min(i, len(pool)-1), key=f"rush_{i}"))
        st.session_state.rushmore_picks = picks
        if st.button("🗻 Generate Mount Rushmore", type="primary"):
            png = rushmore_to_bytes(picks, title=f"{team['short']} Mount Rushmore")
            st.image(png, use_container_width=True)

    @safe_render("Watch/Listen")
    def render_media():
        st.markdown('<div class="section-title">Media & Moments</div>', unsafe_allow_html=True)
        media = get_media_for_team(team_key, team.get("name") or "")
        for cat, items in media.items():
            st.markdown(f"#### {cat}")
            for it in items: st.markdown(f"- [{it.get('name')}]({it.get('url')})")

    with fz_community: render_community()
    with fz_deskbot: render_deskbot()
    with fz_rushmore: render_rushmore()
    with fz_media: render_media()

# ==========================================
# ⚙️ SETTINGS
# ==========================================
with tab_settings:
    st.markdown('<div class="section-title">App Settings & Profile</div>', unsafe_allow_html=True)
    
    # Profile
    st.markdown("### Profile")
    st.session_state.username = st.text_input("Username", st.session_state.username, max_chars=40)
    st.session_state.avatar_preset = st.selectbox("Avatar theme", ["initials"] + AVATAR_PRESETS, index=0)
    st.image(avatar_url(st.session_state.username, st.session_state.avatar_preset), width=64)
    
    st.divider()
    
    # API & Appearance
    st.markdown("### 🔑 API & Display")
    st.session_state.odds_key_input = st.text_input("The Odds API key", value=st.session_state.odds_key_input, type="password", placeholder="the-odds-api.com")
    st.session_state.show_sources = st.toggle("Show data sources", st.session_state.show_sources)
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", st.session_state.dark_mode)
    
    st.divider()
    
    # PDF Export
    st.markdown("### Reports")
    try:
        _games_pdf, _ = client.get_scoreboard(team_key)
        _std_pdf, _ = client.get_standings(team_key)
        _news_pdf, _ = client.get_news(team_key, 8)
        _j = list_entries(50)
        pdf_bytes = export_team_pdf(team.get("name") or team_key, record, _games_pdf, _std_pdf, _news_pdf, _j)
        st.download_button("📄 Export PDF report", data=pdf_bytes, file_name=f"sosby_{team_key}_report.pdf", mime="application/pdf")
    except Exception:
        st.caption("PDF Export temporarily unavailable.")