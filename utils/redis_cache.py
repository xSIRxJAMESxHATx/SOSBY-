"""
Optional Redis cache layer for SO!SB!Y!

Persistence strategies (Redis server / provider):
  - RDB snapshots: point-in-time dump (good defaults on managed Redis)
  - AOF (append-only file): higher durability, more disk I/O
  - Hybrid RDB+AOF: common on Upstash/Redis Cloud
  - Ephemeral (no persist): fine for score TTLs measured in seconds

App-level strategies used here:
  - Write-through: every memory cache set also writes Redis when available
  - Key namespace: sosby:{key}
  - TTL tiers: caller supplies TTL (live scores short, standings longer)
  - Soft failure: Redis down → silent no-op; memory+disk still work
  - Optional REDIS_URL or REDIS_TLS_URL in Streamlit secrets / env

This is not a substitute for ESPN as source of truth — only a shared
cache across sessions/instances.
"""
from __future__ import annotations
import json
import os
from typing import Any, Optional

_client = None
_failed = False
_mode = "disabled"  # disabled | connected | failed


def status() -> dict:
    return {"mode": _mode, "url_configured": bool(
        (os.environ.get("REDIS_URL") or os.environ.get("REDIS_TLS_URL") or "").strip()
    )}


def _conn():
    global _client, _failed, _mode
    if _failed:
        return None
    if _client is not None:
        return _client
    url = (os.environ.get("REDIS_URL") or os.environ.get("REDIS_TLS_URL") or "").strip()
    if not url:
        _mode = "disabled"
        _failed = True
        return None
    try:
        import redis  # type: ignore
        kwargs = dict(
            socket_timeout=1.5,
            socket_connect_timeout=1.5,
            decode_responses=True,
        )
        if url.startswith("rediss://"):
            kwargs["ssl_cert_reqs"] = None
        _client = redis.from_url(url, **kwargs)
        _client.ping()
        _mode = "connected"
        return _client
    except Exception:
        _failed = True
        _mode = "failed"
        _client = None
        return None


def redis_get(key: str) -> Optional[Any]:
    c = _conn()
    if not c:
        return None
    try:
        raw = c.get(f"sosby:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def redis_set(key: str, data: Any, ttl: float = 60.0) -> None:
    """Write-through with expiry. Skips non-JSON-serializable payloads."""
    c = _conn()
    if not c:
        return
    try:
        payload = json.dumps(data)
    except Exception:
        return
    try:
        c.setex(f"sosby:{key}", max(1, int(ttl)), payload)
    except Exception:
        pass


def redis_clear_prefix() -> None:
    c = _conn()
    if not c:
        return
    try:
        for k in c.scan_iter("sosby:*", count=200):
            c.delete(k)
    except Exception:
        pass
