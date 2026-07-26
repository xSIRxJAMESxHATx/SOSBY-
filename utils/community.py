"""
Community board with Supabase (preferred) + local JSON failover.
Tables expected in Supabase (SQL in README):
  community_topics, community_posts, community_users
"""
from __future__ import annotations
import json
import os
import time
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from threading import Lock
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / ".data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORE = DATA_DIR / "community.json"
AUDIT = DATA_DIR / "audit.log"
_lock = Lock()
MAX_POSTS_PER_TOPIC = 100

OFFENSIVE = re.compile(
    r"\b(kill\s*yourself|kys|n[i1]gg|f[a@]g|rape|bomb\s*threat)\b",
    re.I,
)

AVATAR_PRESETS = [
    "Dawg", "Guard", "Sword", "Buckeye", "Massive", "Cannon", "Raider", "Dragon",
    "Lake Effect", "Believeland", "Script Ohio", "Nordecke", "The Land", "Flashes",
    "Superb Owl",
]


def _sb_url() -> str:
    return (os.environ.get("SUPABASE_URL") or "").rstrip("/")


def _sb_key() -> str:
    return os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or ""


def supabase_configured() -> bool:
    return bool(_sb_url() and _sb_key())


def _sb_headers() -> dict:
    key = _sb_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _sb(method: str, path: str, json_body=None, params=None) -> Tuple[bool, Any]:
    if not supabase_configured():
        return False, "not configured"
    url = f"{_sb_url()}/rest/v1/{path}"
    try:
        r = requests.request(method, url, headers=_sb_headers(), json=json_body, params=params, timeout=12)
        if r.status_code >= 400:
            return False, r.text[:300]
        if r.text:
            return True, r.json()
        return True, None
    except Exception as e:
        return False, str(e)


def audit(event: str, detail: str = "") -> None:
    try:
        with AUDIT.open("a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} | {event} | {detail}\n")
    except Exception:
        pass


def is_moderator(password: str) -> bool:
    expected = os.environ.get("MOD_PASSWORD") or ""
    return bool(expected) and password == expected


def moderate_text(text: str) -> Tuple[bool, str]:
    if not text or not str(text).strip():
        return False, "Empty content"
    if len(text) > 4000:
        return False, "Too long (max 4000 chars)"
    if OFFENSIVE.search(text):
        return False, "Blocked by safety filter"
    return True, ""


# ---------- local JSON backend ----------
def _load() -> dict:
    if not STORE.exists():
        return {"topics": {}, "users": {}, "seq": 0}
    try:
        return json.loads(STORE.read_text() or "{}")
    except Exception:
        return {"topics": {}, "users": {}, "seq": 0}


def _save(data: dict) -> None:
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=0))
    tmp.replace(STORE)


def list_topics(team_key: str) -> List[dict]:
    if supabase_configured():
        ok, data = _sb("GET", "community_topics", params={
            "team": f"eq.{team_key}",
            "select": "*,community_posts(*)",
            "order": "updated.desc",
        })
        if ok and isinstance(data, list):
            out = []
            for row in data:
                posts = row.get("community_posts") or row.get("posts") or []
                if isinstance(posts, list):
                    posts = sorted(posts, key=lambda p: p.get("created") or p.get("created_at") or 0)
                out.append({
                    "id": str(row.get("id")),
                    "team": row.get("team"),
                    "title": row.get("title"),
                    "author": row.get("author"),
                    "tags": row.get("tags") or [],
                    "created": row.get("created") or 0,
                    "updated": row.get("updated") or 0,
                    "posts": [
                        {
                            "id": str(p.get("id")),
                            "author": p.get("author"),
                            "body": p.get("body"),
                            "created": p.get("created") or 0,
                            "up": p.get("up") or 0,
                            "down": p.get("down") or 0,
                            "image_url": p.get("image_url") or "",
                            "link_url": p.get("link_url") or "",
                        }
                        for p in posts
                    ],
                })
            return out
        audit("supabase_list_fail", str(data)[:120])
    # local failover
    with _lock:
        data = _load()
        topics = [t for t in data.get("topics", {}).values() if t.get("team") == team_key]
        topics.sort(key=lambda x: -x.get("updated", 0))
        return topics


def create_topic(team_key: str, title: str, author: str, tags: List[str], body: str) -> Tuple[bool, str]:
    ok, msg = moderate_text(title)
    if not ok:
        return False, msg
    ok, msg = moderate_text(body)
    if not ok:
        return False, msg
    author = (author or "Fan").strip()[:40]
    tag_list = [t.strip()[:30] for t in (tags or [])[:8]]
    now = time.time()

    if supabase_configured():
        ok, row = _sb("POST", "community_topics", json_body={
            "team": team_key, "title": title.strip()[:200], "author": author,
            "tags": tag_list, "created": now, "updated": now,
        })
        if ok and isinstance(row, list) and row:
            tid = row[0].get("id")
            _sb("POST", "community_posts", json_body={
                "topic_id": tid, "author": author, "body": body.strip()[:4000],
                "created": now, "up": 0, "down": 0, "image_url": "", "link_url": "",
            })
            _sb("POST", "community_users", json_body={"name": author, "avatar": "initials", "posts": 1})
            audit("sb_create_topic", f"{team_key}:{tid}")
            return True, str(tid)
        # fall through to local

    with _lock:
        data = _load()
        data["seq"] = int(data.get("seq") or 0) + 1
        tid = f"t{data['seq']}"
        data.setdefault("topics", {})[tid] = {
            "id": tid, "team": team_key, "title": title.strip()[:200], "author": author,
            "tags": tag_list, "created": now, "updated": now,
            "posts": [{
                "id": f"{tid}_p0", "author": author, "body": body.strip()[:4000],
                "created": now, "up": 0, "down": 0, "image_url": "", "link_url": "",
            }],
        }
        users = data.setdefault("users", {})
        users[author] = users.get(author) or {"name": author, "avatar": "initials", "posts": 0}
        users[author]["posts"] = int(users[author].get("posts") or 0) + 1
        _save(data)
        audit("local_create_topic", f"{team_key}:{tid}")
    return True, tid


def add_post(topic_id: str, author: str, body: str, image_url: str = "", link_url: str = "") -> Tuple[bool, str]:
    ok, msg = moderate_text(body)
    if not ok:
        return False, msg
    if image_url and not str(image_url).startswith(("https://", "http://")):
        return False, "Image URL must be http(s)"
    if link_url and not str(link_url).startswith(("https://", "http://")):
        return False, "Link must be http(s)"
    author = (author or "Fan").strip()[:40]
    now = time.time()

    if supabase_configured():
        ok, posts = _sb("GET", "community_posts", params={"topic_id": f"eq.{topic_id}", "select": "id"})
        if ok and isinstance(posts, list) and len(posts) >= MAX_POSTS_PER_TOPIC:
            return False, f"Topic full ({MAX_POSTS_PER_TOPIC} max)"
        ok, row = _sb("POST", "community_posts", json_body={
            "topic_id": topic_id, "author": author, "body": body.strip()[:4000],
            "created": now, "up": 0, "down": 0,
            "image_url": (image_url or "")[:500], "link_url": (link_url or "")[:500],
        })
        if ok:
            _sb("PATCH", "community_topics", json_body={"updated": now}, params={"id": f"eq.{topic_id}"})
            audit("sb_add_post", topic_id)
            return True, "ok"
        # failover local

    with _lock:
        data = _load()
        topic = data.get("topics", {}).get(topic_id)
        if not topic:
            return False, "Topic not found"
        if len(topic.get("posts") or []) >= MAX_POSTS_PER_TOPIC:
            return False, f"Topic full ({MAX_POSTS_PER_TOPIC} posts max)"
        pid = f"{topic_id}_p{len(topic['posts'])}"
        topic["posts"].append({
            "id": pid, "author": author, "body": body.strip()[:4000], "created": now,
            "up": 0, "down": 0, "image_url": (image_url or "")[:500], "link_url": (link_url or "")[:500],
        })
        topic["updated"] = now
        _save(data)
        audit("local_add_post", pid)
    return True, "ok"


def vote(topic_id: str, post_id: str, direction: str) -> bool:
    if supabase_configured():
        ok, rows = _sb("GET", "community_posts", params={"id": f"eq.{post_id}", "select": "up,down"})
        if ok and isinstance(rows, list) and rows:
            up = int(rows[0].get("up") or 0)
            down = int(rows[0].get("down") or 0)
            if direction == "up":
                up += 1
            else:
                down += 1
            ok2, _ = _sb("PATCH", "community_posts", json_body={"up": up, "down": down}, params={"id": f"eq.{post_id}"})
            if ok2:
                return True
    with _lock:
        data = _load()
        topic = data.get("topics", {}).get(topic_id)
        if not topic:
            return False
        for p in topic.get("posts") or []:
            if p.get("id") == post_id:
                if direction == "up":
                    p["up"] = int(p.get("up") or 0) + 1
                else:
                    p["down"] = int(p.get("down") or 0) + 1
                _save(data)
                return True
    return False


def delete_post(topic_id: str, post_id: str, requester: str, mod_password: str = "") -> Tuple[bool, str]:
    if supabase_configured():
        ok, rows = _sb("GET", "community_posts", params={"id": f"eq.{post_id}", "select": "author"})
        if ok and isinstance(rows, list) and rows:
            author = rows[0].get("author")
            if author == requester or is_moderator(mod_password):
                ok2, _ = _sb("DELETE", "community_posts", params={"id": f"eq.{post_id}"})
                if ok2:
                    audit("sb_delete_post", post_id)
                    return True, "Deleted"
            else:
                return False, "Not allowed"

    with _lock:
        data = _load()
        topic = data.get("topics", {}).get(topic_id)
        if not topic:
            return False, "Not found"
        posts = topic.get("posts") or []
        target = next((p for p in posts if p.get("id") == post_id), None)
        if not target:
            return False, "Post not found"
        if not ((target.get("author") == requester) or is_moderator(mod_password)):
            return False, "Not allowed"
        topic["posts"] = [p for p in posts if p.get("id") != post_id]
        _save(data)
        audit("local_delete_post", post_id)
        return True, "Deleted"


def delete_topic(topic_id: str, mod_password: str) -> Tuple[bool, str]:
    if not is_moderator(mod_password):
        return False, "Moderator password required"
    if supabase_configured():
        _sb("DELETE", "community_posts", params={"topic_id": f"eq.{topic_id}"})
        ok, _ = _sb("DELETE", "community_topics", params={"id": f"eq.{topic_id}"})
        if ok:
            audit("sb_delete_topic", topic_id)
            return True, "Topic deleted"
    with _lock:
        data = _load()
        if topic_id in data.get("topics", {}):
            del data["topics"][topic_id]
            _save(data)
            audit("local_delete_topic", topic_id)
            return True, "Topic deleted"
    return False, "Not found"


def list_users() -> List[dict]:
    if supabase_configured():
        ok, data = _sb("GET", "community_users", params={"select": "*", "order": "posts.desc", "limit": "50"})
        if ok and isinstance(data, list):
            return data
    with _lock:
        data = _load()
        return sorted(data.get("users", {}).values(), key=lambda u: -int(u.get("posts") or 0))


def avatar_url(name: str, preset: str = "initials") -> str:
    from urllib.parse import quote_plus
    if preset and preset != "initials" and preset in AVATAR_PRESETS:
        return f"https://ui-avatars.com/api/?name={quote_plus(preset)}&background=311D00&color=FFD700&bold=true&size=128"
    initials = "".join(p[0] for p in (name or "F").split()[:2]).upper()
    return f"https://ui-avatars.com/api/?name={quote_plus(initials)}&background=0C2340&color=fff&bold=true&size=128"
