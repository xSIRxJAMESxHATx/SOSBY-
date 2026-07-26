"""Superb Owl — classy Browns-crown champion (monocle + cigar)."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Browns-forward palette
BROWN = (49, 29, 0, 255)
ORANGE = (255, 60, 0, 255)
CREAM = (255, 240, 220, 255)
GOLD = (255, 200, 60, 255)
DARK = (25, 15, 5, 255)


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def generate_superb_owl(size: int = 512) -> Image.Image:
    W = H = size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 512.0
    def sc(v): return int(v * s)
    cx, cy = W // 2, H // 2 + sc(15)

    # soft gold halo
    for i, r in enumerate(range(sc(190), sc(50), -sc(10))):
        d.ellipse([cx-r, cy-r-sc(40), cx+r, cy+r-sc(40)], fill=(255, 180, 40, max(6, 22 - i * 2)))

    # body
    d.ellipse([cx-sc(90), cy-sc(20), cx+sc(90), cy+sc(120)], fill=(90, 55, 25, 255), outline=DARK, width=max(2, sc(3)))
    d.ellipse([cx-sc(52), cy+sc(18), cx+sc(52), cy+sc(100)], fill=CREAM)

    # head
    d.ellipse([cx-sc(78), cy-sc(105), cx+sc(78), cy+sc(12)], fill=(110, 68, 28, 255), outline=DARK, width=max(2, sc(3)))
    # tufts
    d.polygon([(cx-sc(72), cy-sc(70)), (cx-sc(105), cy-sc(145)), (cx-sc(30), cy-sc(90))], fill=(85, 50, 20, 255))
    d.polygon([(cx+sc(72), cy-sc(70)), (cx+sc(105), cy-sc(145)), (cx+sc(30), cy-sc(90))], fill=(85, 50, 20, 255))

    # BIG crown (Browns orange + brown band + jewels)
    crown = [
        (cx-sc(75), cy-sc(95)),
        (cx-sc(55), cy-sc(165)),
        (cx-sc(30), cy-sc(110)),
        (cx, cy-sc(180)),
        (cx+sc(30), cy-sc(110)),
        (cx+sc(55), cy-sc(165)),
        (cx+sc(75), cy-sc(95)),
    ]
    d.polygon(crown, fill=ORANGE, outline=BROWN)
    d.rectangle([cx-sc(78), cy-sc(105), cx+sc(78), cy-sc(88)], fill=BROWN)
    for jx, col in [(-sc(40), GOLD), (0, (255,255,255,255)), (sc(40), GOLD)]:
        d.ellipse([cx+jx-sc(8), cy-sc(172), cx+jx+sc(8), cy-sc(156)], fill=col)

    # eyes
    d.ellipse([cx-sc(40), cy-sc(62), cx-sc(5), cy-sc(26)], fill=(255, 255, 245, 255), outline=DARK, width=2)
    d.ellipse([cx+sc(5), cy-sc(62), cx+sc(40), cy-sc(26)], fill=(255, 255, 245, 255), outline=DARK, width=2)
    d.ellipse([cx-sc(27), cy-sc(52), cx-sc(15), cy-sc(40)], fill=(25, 20, 15, 255))
    d.ellipse([cx+sc(17), cy-sc(52), cx+sc(29), cy-sc(40)], fill=(25, 20, 15, 255))
    # monocle
    d.ellipse([cx+sc(1), cy-sc(68), cx+sc(46), cy-sc(22)], outline=GOLD, width=max(3, sc(4)))
    d.line([cx+sc(46), cy-sc(28), cx+sc(56), cy+sc(10)], fill=(200, 160, 50, 255), width=max(2, sc(2)))

    # beak
    d.polygon([(cx-sc(10), cy-sc(20)), (cx+sc(10), cy-sc(20)), (cx, cy-sc(2))], fill=(240, 160, 40, 255))
    # smug arc
    d.arc([cx-sc(16), cy-sc(10), cx+sc(20), cy+sc(14)], 15, 155, fill=DARK, width=max(2, sc(3)))

    # cigar
    d.rounded_rectangle([cx+sc(36), cy-sc(4), cx+sc(108), cy+sc(12)], radius=sc(3), fill=(120, 70, 30, 255))
    d.rectangle([cx+sc(100), cy-sc(4), cx+sc(110), cy+sc(12)], fill=(200, 40, 30, 255))
    d.ellipse([cx+sc(110), cy-sc(16), cx+sc(132), cy+sc(6)], fill=(230, 230, 235, 130))

    # championship props
    d.ellipse([cx+sc(50), cy+sc(48), cx+sc(100), cy+sc(98)], fill=(120, 20, 50, 255))
    d.ellipse([cx-sc(115), cy+sc(45), cx-sc(55), cy+sc(100)], fill=(180, 95, 40, 255))
    # mini trophy
    d.rectangle([cx-sc(12), cy+sc(70), cx+sc(12), cy+sc(88)], fill=GOLD)
    d.ellipse([cx-sc(18), cy+sc(55), cx+sc(18), cy+sc(78)], fill=GOLD)
    d.rectangle([cx-sc(16), cy+sc(88), cx+sc(16), cy+sc(94)], fill=GOLD)

    d.rounded_rectangle([sc(36), H-sc(46), W-sc(36), H-sc(10)], radius=sc(8), fill=DARK)
    d.text((cx, H-sc(28)), "SO!SB!Y!", fill=GOLD, font=_font(max(16, sc(22))), anchor="mm")
    return img


def save_brand_assets() -> dict:
    owl = generate_superb_owl(512)
    icon_path = ASSETS / "superb_owl_icon.png"
    owl.save(icon_path, "PNG")
    wm = generate_superb_owl(800)
    arr = wm.split()
    if len(arr) == 4:
        a = arr[3].point(lambda p: int(p * 0.10))
        wm = Image.merge("RGBA", (arr[0], arr[1], arr[2], a))
    wm_path = ASSETS / "superb_owl_watermark.png"
    wm.save(wm_path, "PNG")
    fav = owl.resize((64, 64), Image.Resampling.LANCZOS)
    fav_path = ASSETS / "favicon.png"
    fav.save(fav_path, "PNG")
    return {"icon": str(icon_path), "watermark": str(wm_path), "favicon": str(fav_path)}


def watermark_data_uri() -> str:
    import base64
    path = ASSETS / "superb_owl_watermark.png"
    if not path.exists():
        save_brand_assets()
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
