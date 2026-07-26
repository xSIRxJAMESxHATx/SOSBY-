"""Hypothetical bet journal — session + local JSON failover."""
from __future__ import annotations
import json
import time
from pathlib import Path
from threading import Lock
from typing import Dict, List

DATA = Path(__file__).resolve().parent.parent / ".data"
DATA.mkdir(parents=True, exist_ok=True)
STORE = DATA / "bet_journal.json"
_lock = Lock()


def _load() -> List[dict]:
    if not STORE.exists():
        return []
    try:
        return json.loads(STORE.read_text() or "[]")
    except Exception:
        return []


def _save(rows: List[dict]) -> None:
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows[-500:], indent=0))  # cap history
    tmp.replace(STORE)


def add_entry(entry: dict) -> None:
    with _lock:
        rows = _load()
        entry = dict(entry)
        entry.setdefault("id", f"j{int(time.time()*1000)}")
        entry.setdefault("ts", time.time())
        rows.append(entry)
        _save(rows)


def list_entries(limit: int = 100) -> List[dict]:
    with _lock:
        rows = _load()
    rows = sorted(rows, key=lambda r: -float(r.get("ts") or 0))
    return rows[:limit]


def clear_all() -> None:
    with _lock:
        _save([])


def summary_stats(rows: List[dict]) -> dict:
    if not rows:
        return {"n": 0, "staked": 0, "pnl": 0}
    staked = sum(float(r.get("stake") or 0) for r in rows)
    pnl = sum(float(r.get("pnl") or 0) for r in rows)
    return {"n": len(rows), "staked": round(staked, 2), "pnl": round(pnl, 2)}


def to_csv(rows=None) -> str:
    """Return CSV string of journal rows."""
    import csv
    import io
    rows = rows if rows is not None else list_entries(500)
    if not rows:
        return "id,ts,team,side,odds,stake,note,result,pnl\n"
    # stable columns
    cols = ["id", "ts", "team", "side", "odds", "stake", "note", "result", "pnl"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return buf.getvalue()
