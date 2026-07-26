"""
1960s Batman-era POW/BAM style cartoon placeholders for player cards.
Generated with Pillow when no real headshot exists.
"""
from __future__ import annotations
import io
import random
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


POSITION_COLORS = {
    "QB": ((30, 60, 120), (255, 200, 50)),
    "RB": ((120, 40, 20), (255, 180, 80)),
    "WR": ((20, 100, 60), (255, 220, 100)),
    "TE": ((80, 40, 100), (220, 180, 255)),
    "OL": ((60, 60, 60), (200, 200, 200)),
    "DL": ((100, 20, 20), (255, 100, 80)),
    "LB": ((40, 40, 90), (150, 180, 255)),
    "DB": ((20, 80, 80), (100, 255, 220)),
    "K": ((90, 90, 30), (255, 255, 120)),
    "P": ((50, 70, 50), (180, 255, 180)),
    "G": ((20, 80, 40), (255, 200, 50)),
    "F": ((100, 30, 30), (255, 150, 80)),
    "C": ((40, 40, 100), (150, 150, 255)),
    "PG": ((80, 40, 20), (255, 180, 60)),
    "SG": ((60, 20, 80), (220, 150, 255)),
    "SF": ((20, 70, 90), (100, 220, 255)),
    "PF": ((90, 50, 20), (255, 200, 120)),
    "P": ((30, 50, 100), (200, 220, 255)),  # pitcher
    "SS": ((40, 80, 40), (180, 255, 180)),
    "1B": ((100, 40, 40), (255, 160, 160)),
    "2B": ((40, 60, 100), (160, 180, 255)),
    "3B": ((80, 60, 20), (255, 220, 120)),
    "OF": ((20, 90, 50), (150, 255, 180)),
    "GK": ((20, 20, 20), (255, 220, 50)),
    "FW": ((120, 20, 40), (255, 120, 100)),
    "MF": ((20, 70, 40), (120, 255, 160)),
    "DF": ((30, 40, 90), (120, 150, 255)),
    "DEFAULT": ((40, 30, 20), (255, 200, 80)),
}

BURSTS = ["POW!", "BAM!", "ZAP!", "WHAM!", "SOCK!", "BLAM!"]


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def generate_cartoon(
    name: str,
    position: str = "",
    team_primary: str = "#311D00",
    size: Tuple[int, int] = (400, 500),
) -> bytes:
    """Return PNG bytes of a POW/BAM style cartoon card art."""
    W, H = size
    pos_key = (position or "").upper().strip()
    # normalize common names
    for k in list(POSITION_COLORS.keys()):
        if k != "DEFAULT" and (k in pos_key or pos_key in k):
            pos_key = k
            break
    else:
        pos_key = "DEFAULT"
    bg, accent = POSITION_COLORS.get(pos_key, POSITION_COLORS["DEFAULT"])

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    # halftone-ish dots
    random.seed(sum(ord(c) for c in name))
    for _ in range(120):
        x, y = random.randint(0, W), random.randint(0, H)
        r = random.randint(2, 8)
        d.ellipse([x, y, x+r, y+r], fill=(accent[0]//3, accent[1]//3, accent[2]//3))

    # burst starburst behind figure
    cx, cy = W // 2, int(H * 0.42)
    for i in range(16):
        ang = i * (360 / 16)
        import math
        rad = math.radians(ang)
        x2 = cx + int(math.cos(rad) * 160)
        y2 = cy + int(math.sin(rad) * 140)
        d.polygon([(cx, cy), (x2, y2), (cx + int(math.cos(rad+0.2)*40), cy + int(math.sin(rad+0.2)*40))], fill=accent)

    # simple figure silhouette (head + body + pose by position)
    # head
    d.ellipse([cx-45, cy-90, cx+45, cy-10], fill=(255, 220, 180), outline=(20, 15, 10), width=3)
    # eyes
    d.ellipse([cx-25, cy-65, cx-10, cy-50], fill=(20, 15, 10))
    d.ellipse([cx+10, cy-65, cx+25, cy-50], fill=(20, 15, 10))
    # smile
    d.arc([cx-20, cy-45, cx+20, cy-20], 0, 180, fill=(20, 15, 10), width=3)
    # body
    d.rectangle([cx-50, cy-5, cx+50, cy+90], fill=accent, outline=(20, 15, 10), width=3)
    # arms
    d.line([cx-50, cy+20, cx-100, cy+50], fill=(255, 220, 180), width=12)
    d.line([cx+50, cy+20, cx+100, cy+50], fill=(255, 220, 180), width=12)
    # legs
    d.line([cx-25, cy+90, cx-40, cy+160], fill=(30, 30, 40), width=14)
    d.line([cx+25, cy+90, cx+40, cy+160], fill=(30, 30, 40), width=14)

    # jersey number blob
    d.ellipse([cx-22, cy+15, cx+22, cy+55], fill=bg)
    num = str((sum(ord(c) for c in name) % 99) or 1)
    d.text((cx, cy+35), num, fill=accent, font=_font(22), anchor="mm")

    # POW banner
    burst = BURSTS[sum(ord(c) for c in name) % len(BURSTS)]
    d.polygon([(20, 30), (140, 15), (150, 70), (30, 85)], fill=(255, 50, 50), outline=(20, 10, 10))
    d.text((85, 48), burst, fill=(255, 255, 100), font=_font(22), anchor="mm")

    # name plate
    d.rectangle([10, H-70, W-10, H-12], fill=(20, 15, 10))
    label = name.upper() if len(name) < 22 else name[:20].upper() + "…"
    d.text((W//2, H-50), label, fill=(255, 220, 100), font=_font(18), anchor="mm")
    d.text((W//2, H-28), f"{pos_key or 'STAR'} · SBSBY CLASSIC", fill=(200, 180, 140), font=_font(11), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def cartoon_data_uri(name: str, position: str = "", team_primary: str = "#311D00") -> str:
    import base64
    raw = generate_cartoon(name, position, team_primary)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"
