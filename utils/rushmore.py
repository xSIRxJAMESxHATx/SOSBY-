"""Mount Rushmore composite using real mountain photo + smart head crops."""
from __future__ import annotations
import io
from pathlib import Path
from typing import List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SOSBY-SportsHub/3.3"})

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
BASE_CANDIDATES = [
    _ASSETS / "mount_rushmore_base.jpg",
    _ASSETS / "mount_rushmore_base.png",
]

# Tuned for 1280x960 public-domain Rushmore photo
SLOTS_1280 = [
    (200, 130, 280),
    (430, 170, 230),
    (620, 200, 200),
    (820, 150, 250),
]


def _fetch_image(url: str, timeout: float = 6.0) -> Optional[Image.Image]:
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _placeholder_head(name: str, size: int = 220) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 3, size - 3], fill=(130, 125, 118, 255))
    initials = "".join(p[0] for p in name.split()[:2]).upper() or "?"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(12, size // 3))
    except Exception:
        font = ImageFont.load_default()
    d.text((size / 2, size / 2), initials, fill=(240, 235, 220, 255), font=font, anchor="mm")
    return img


def fetch_player_headshot(player_name: str) -> Image.Image:
    q = player_name.replace(" ", "%20")
    try:
        r = SESSION.get(f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={q}", timeout=6)
        if r.status_code == 200:
            for p in (r.json().get("player") or [])[:5]:
                for key in ("strCutout", "strThumb", "strRender"):
                    url = p.get(key)
                    if url and str(url).startswith("http"):
                        img = _fetch_image(url)
                        if img:
                            return img
    except Exception:
        pass
    try:
        title = player_name.replace(" ", "_")
        r = SESSION.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", timeout=5)
        if r.status_code == 200:
            thumb = (r.json().get("thumbnail") or {}).get("source")
            if thumb:
                img = _fetch_image(thumb)
                if img:
                    return img
    except Exception:
        pass
    img = _fetch_image(
        f"https://ui-avatars.com/api/?name={q}&size=256&background=5a554e&color=f5f0e6&bold=true"
    )
    return img if img else _placeholder_head(player_name)


def _rock_blend_face(im: Image.Image, size: int) -> Image.Image:
    try:
        from .smart_crop import crop_for_rushmore
        im = crop_for_rushmore(im, size).convert("RGBA")
    except Exception:
        im = im.convert("RGBA")
        w, h = im.size
        side = min(w, h)
        im = im.crop((0, 0, side, side)).resize((size, size), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(im)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    rock = ImageOps.colorize(gray, black="#3a3530", white="#e8e0d4").convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([2, 2, size - 3, size - 3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    rock.putalpha(mask)
    return rock


def _load_base() -> Image.Image:
    for p in BASE_CANDIDATES:
        try:
            if p.exists():
                return Image.open(p).convert("RGBA")
        except Exception:
            continue
    W, H = 1280, 960
    img = Image.new("RGBA", (W, H), (40, 70, 120, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(0, H), (0, 400), (400, 250), (800, 280), (1280, 400), (1280, H)], fill=(110, 105, 98, 255))
    return img


def generate_rushmore(players: List[str], title: str = "Mount Rushmore") -> Image.Image:
    base = _load_base()
    W, H = base.size
    sx, sy = W / 1280.0, H / 960.0
    slots = [(int(x * sx), int(y * sy), int(d * min(sx, sy))) for x, y, d in SLOTS_1280]
    names = (list(players) + ["?", "?", "?", "?"])[:4]
    out = base.copy()

    for i, (x, y, sz) in enumerate(slots):
        name = names[i]
        try:
            head = fetch_player_headshot(name)
        except Exception:
            head = _placeholder_head(name)
        try:
            face = _rock_blend_face(head, sz)
        except Exception:
            face = _placeholder_head(name, sz)
        # clamp position
        x = max(0, min(W - sz, x))
        y = max(0, min(H - sz, y))
        try:
            out.paste(face, (x, y), face)
        except Exception:
            out.paste(face.convert("RGB"), (x, y))

    draw = ImageDraw.Draw(out)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(22, W // 40))
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(12, W // 90))
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(11, W // 100))
    except Exception:
        font_title = font_name = font_small = ImageFont.load_default()

    draw.rectangle([0, 0, W, int(H * 0.07)], fill=(15, 20, 30, 200))
    draw.text((W // 2, int(H * 0.035)), title, fill=(255, 255, 255, 255), font=font_title, anchor="mm")

    for i, (x, y, sz) in enumerate(slots):
        label = names[i] if len(names[i]) < 24 else names[i][:22] + "…"
        ty = min(y + sz + 6, H - 36)
        draw.rounded_rectangle([x, ty, x + sz, ty + 24], radius=6, fill=(20, 18, 15, 220))
        draw.text((x + sz // 2, ty + 12), label, fill=(245, 240, 230, 255), font=font_name, anchor="mm")

    draw.rectangle([0, H - 28, W, H], fill=(15, 20, 30, 180))
    draw.text(
        (W // 2, H - 14),
        "Fan composite · Multi-source portraits · SO!SB!Y!",
        fill=(220, 220, 220, 200),
        font=font_small,
        anchor="mm",
    )
    return out.convert("RGB")


def rushmore_to_bytes(players: List[str], title: str = "Mount Rushmore") -> bytes:
    try:
        img = generate_rushmore(players, title)
    except Exception as e:
        img = Image.new("RGB", (960, 640), (40, 55, 80))
        d = ImageDraw.Draw(img)
        d.text((480, 300), "Rushmore unavailable", fill=(255, 255, 255), anchor="mm")
        d.text((480, 340), str(e)[:80], fill=(200, 200, 200), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue()
