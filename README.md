# SO!SB!Y! — Superb Owl! Super Browns! Yeah!

## Secrets

```toml
ODDS_API_KEY = "..."
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "anon_key"
TWILIO_ACCOUNT_SID = "ACxxxx"
TWILIO_AUTH_TOKEN = "xxxx"
TWILIO_FROM_NUMBER = "+1xxxx"
MOD_PASSWORD = "strong_mod_password"
```

## Supabase tables + RLS (run in SQL editor)

```sql
create table if not exists community_topics (
  id bigint generated always as identity primary key,
  team text, title text, author text, tags jsonb default '[]',
  created double precision, updated double precision
);
create table if not exists community_posts (
  id bigint generated always as identity primary key,
  topic_id bigint references community_topics(id) on delete cascade,
  author text, body text, created double precision,
  up int default 0, down int default 0,
  image_url text default '', link_url text default ''
);
create table if not exists community_users (
  name text primary key, avatar text, posts int default 0
);

alter table community_topics enable row level security;
alter table community_posts enable row level security;
alter table community_users enable row level security;

-- Public fan board (adjust for production)
create policy "public read topics" on community_topics for select using (true);
create policy "public insert topics" on community_topics for insert with check (true);
create policy "public read posts" on community_posts for select using (true);
create policy "public insert posts" on community_posts for insert with check (true);
create policy "public update posts" on community_posts for update using (true);
create policy "public delete posts" on community_posts for delete using (true);
create policy "public read users" on community_users for select using (true);
create policy "public upsert users" on community_users for insert with check (true);
```

Tighten policies later (auth.uid(), mod roles). Without Supabase, community uses local JSON failover.

## Features

- Real **Mount Rushmore photo** base with rock-blended player faces
- Standings: ESPN current → prior seasons → CBS/FOX/Google link fallback
- Bet sandbox: fractional Kelly ladder + Monte Carlo + parlay lab
- Daily team fun fact (curated + Wikimedia on-this-day)
- Main-page team switcher, Superb Owl branding

## Deploy

`streamlit run app.py` — main file `app.py` on Cloud.

Educational betting tools only. Not affiliated with leagues/schools.


## API notes / rate limits

| Source | Notes |
|--------|--------|
| **ESPN** (`site.api.espn.com`) | Unofficial/undocumented. No published quota; community guidance ~1 req / 30–60s for live polling. App throttles ~3 req/s max and retries 429. |
| **TheSportsDB** free | Key `123` in URL path. **30 requests/minute**. Premium raises limits + livescores. |
| **The Odds API** | Free tier ~500 req/month — use secrets key. |

HS / track (Reynoldsburg, Tiffin): curated program hubs + MaxPreps/NFHS/TFRRS links when ESPN IDs are absent.


## WebSocket fallback strategy

1. **Primary:** HTTP polling of ESPN + TheSportsDB (reliable, cache + tenacity).
2. **Live tick:** On auto-refresh, `live_score_tick` clears the team score cache and refetches.
3. **Optional WS:** Set secret `SPORTS_WS_URL` for a private push feed; payloads merge when present.
4. **Why not pure WS?** Major leagues do not offer free public score WebSockets. NFHS/MaxPreps are not open JSON score APIs.

## Team lock

Scoreboard/schedule matching uses **ESPN team id first**. Name matching uses distinctive tokens only (blocks generic words like "Football").


## Score formatting fix

ESPN competitor `score` may be a string **or** `{"value": "3", "displayValue": "3"}`.
`format_score()` / `_norm_espn_event` unwrap both so the UI never shows `{'value'}`.

## Optional Redis

Set `REDIS_URL` in secrets to enable a shared cache layer. Without it, memory + disk cache still work.

## Teams

Removed: Reynoldsburg, Tiffin Track, Kent State (local/HS focus dropped for reliability).
