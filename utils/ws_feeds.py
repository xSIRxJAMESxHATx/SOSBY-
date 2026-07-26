"""
WebSocket live-feed helpers with reconnect + polling fallback.
Streamlit Cloud cannot keep arbitrary WS open across sessions forever;
this module provides best-effort live sockets and safe fallbacks.
"""
from __future__ import annotations
import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:
    import websocket  # websocket-client
except ImportError:
    websocket = None


class LiveSocket:
    """Thin wrapper: connect, recv loop, auto-reconnect, last payload cache."""

    def __init__(self, url: str, on_message: Optional[Callable[[Any], None]] = None):
        self.url = url
        self.on_message = on_message
        self.last_payload: Any = None
        self.last_error: str = ""
        self.connected = False
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ws = None

    def start(self) -> None:
        if websocket is None:
            self.last_error = "websocket-client not installed"
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass

    def _run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                self._ws = websocket.WebSocketApp(
                    self.url,
                    on_message=self._on_msg,
                    on_error=self._on_err,
                    on_close=self._on_close,
                    on_open=self._on_open,
                )
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
            if self._stop.is_set():
                break
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 15.0)

    def _on_open(self, _ws) -> None:
        self.connected = True
        self.last_error = ""

    def _on_close(self, *_args) -> None:
        self.connected = False

    def _on_err(self, _ws, err) -> None:
        self.last_error = str(err)
        self.connected = False

    def _on_msg(self, _ws, message: str) -> None:
        try:
            data = json.loads(message)
        except Exception:
            data = message
        self.last_payload = data
        if self.on_message:
            try:
                self.on_message(data)
            except Exception:
                pass


# Optional public echo / demo endpoints for connection health checks
DEMO_WS = "wss://echo.websocket.events"


def probe_websocket(url: str = DEMO_WS, timeout: float = 5.0) -> dict:
    """One-shot WS probe for diagnostics (not a sports feed)."""
    if websocket is None:
        return {"ok": False, "error": "websocket-client missing"}
    try:
        ws = websocket.create_connection(url, timeout=timeout)
        ws.send(json.dumps({"ping": True, "app": "SO!SB!Y!"}))
        reply = ws.recv()
        ws.close()
        return {"ok": True, "reply": str(reply)[:200], "url": url}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


def sports_ws_candidates(team_key: str) -> List[dict]:
    """
    Document / attempt known patterns. Most leagues do not expose free public WS;
    we return candidate metadata and let HTTP polling remain primary.
    """
    return [
        {
            "name": "Primary HTTP scoreboard (ESPN)",
            "transport": "https",
            "note": "Authoritative fallback — always used",
        },
        {
            "name": "TheSportsDB poll",
            "transport": "https",
            "note": "Secondary live/next events",
        },
        {
            "name": "Custom WS (owner-configured)",
            "transport": "wss",
            "env": "SPORTS_WS_URL",
            "note": "Set SPORTS_WS_URL secret to enable private/push feed",
        },
    ]


_owner_sockets: Dict[str, LiveSocket] = {}


def get_owner_ws() -> Optional[LiveSocket]:
    """If SPORTS_WS_URL is set, maintain a background socket."""
    import os
    url = (os.environ.get("SPORTS_WS_URL") or "").strip()
    if not url:
        return None
    sock = _owner_sockets.get(url)
    if sock is None:
        sock = LiveSocket(url)
        sock.start()
        _owner_sockets[url] = sock
    return sock


def merge_ws_payload_into_games(games: List[dict]) -> List[dict]:
    """Best-effort merge of last WS payload into game list."""
    sock = get_owner_ws()
    if not sock or not sock.last_payload:
        return games
    payload = sock.last_payload
    try:
        if isinstance(payload, dict) and "games" in payload:
            return payload.get("games") or games
        if isinstance(payload, list):
            return payload
    except Exception:
        pass
    return games


def live_score_tick(client, team_key: str) -> dict:
    """
    One live-score tick for Streamlit auto-refresh / WS-style updates.
    Clears negative cache, fetches scoreboard, returns status payload.
    """
    try:
        # bust score cache key prefix for this team
        for k in list(getattr(client, "_cache", {}).keys()):
            if k.startswith(f"sb:{team_key}:"):
                client._cache.pop(k, None)
    except Exception:
        pass
    try:
        games, src = client.get_scoreboard(team_key)
    except Exception as e:
        return {"ok": False, "error": str(e), "games": [], "source": "error"}
    live = [g for g in (games or []) if (g.get("status_state") or "") == "in"]
    return {
        "ok": True,
        "games": games or [],
        "live_count": len(live),
        "source": src,
        "empty": not bool(games),
    }
