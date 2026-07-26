"""
Lightweight disk cache to cut repeat API calls across reruns.
JSON files under .data/http_cache/ with TTL.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path(__file__).resolve().parent.parent / ".data" / "http_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key_path(key: str) -> Path:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]
    return CACHE_DIR / f"{h}.json"


def disk_get(key: str, ttl: float) -> Optional[Any]:
    path = _key_path(key)
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        ts = float(obj.get("ts") or 0)
        if time.time() - ts > float(ttl):
            return None
        return obj.get("data")
    except Exception:
        return None


def disk_set(key: str, data: Any) -> None:
    path = _key_path(key)
    try:
        # only JSON-serializable payloads
        payload = {"ts": time.time(), "data": data}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def disk_clear() -> None:
    for p in CACHE_DIR.glob("*.json"):
        try:
            p.unlink()
        except Exception:
            pass
