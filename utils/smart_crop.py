"""
Advanced heuristic image cropping for headshots (no OpenCV dependency).
Techniques: entropy map, upper-weight bias, skin-tone prior, center-of-mass.
"""
from __future__ import annotations
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageOps, ImageStat, ImageEnhance
import math


def _entropy_map(gray: Image.Image, tile: int = 16) -> list:
    w, h = gray.size
    scores = []
    for y in range(0, h - tile + 1, tile):
        for x in range(0, w - tile + 1, tile):
            crop = gray.crop((x, y, x + tile, y + tile))
            # histogram entropy
            hist = crop.histogram()
            total = sum(hist) or 1
            ent = 0.0
            for c in hist:
                if c:
                    p = c / total
                    ent -= p * math.log2(p)
            # upper-weight bias (faces usually higher)
            weight = 1.0 + max(0.0, 1.2 - (y / max(1, h)))
            scores.append((ent * weight, x, y, tile))
    return scores


def _skin_score(im: Image.Image) -> float:
    """Rough skin-tone pixel fraction in YCbCr-ish RGB ranges."""
    im = im.convert("RGB").resize((64, 64))
    pixels = list(im.getdata())
    hit = 0
    for r, g, b in pixels:
        if (r > 95 and g > 40 and b > 20 and r > g and r > b
                and abs(r - g) > 15 and r - b > 15):
            hit += 1
        # broader warm tones
        elif r > 180 and g > 120 and b > 80 and r >= g >= b:
            hit += 1
    return hit / max(1, len(pixels))


def smart_head_crop(im: Image.Image, out_size: int = 256) -> Image.Image:
    """
    Return square crop biased toward face/head region.
    Pipeline: EXIF orient → entropy peak → skin refine → upper-third fallback.
    """
    im = ImageOps.exif_transpose(im).convert("RGBA")
    w, h = im.size
    if w < 16 or h < 16:
        return im.resize((out_size, out_size), Image.Resampling.LANCZOS)

    # Prefer portrait upper region baseline
    if h >= w:
        base = im.crop((0, 0, w, min(h, int(w * 1.15))))
    else:
        side = h
        left = max(0, (w - side) // 2)
        # shift up slightly
        base = im.crop((left, 0, left + side, side))

    bw, bh = base.size
    gray = ImageOps.grayscale(base)
    scores = _entropy_map(gray, tile=max(8, min(bw, bh) // 10))
    scores.sort(reverse=True)

    best_crop = base
    best_skin = -1.0
    target = min(bw, bh)

    for ent, x, y, tile in scores[:12]:
        # expand tile to ~60% of min dimension around peak
        side = int(target * 0.72)
        cx, cy = x + tile // 2, y + tile // 2
        # pull center upward for head bias
        cy = int(cy * 0.85)
        left = max(0, min(bw - side, cx - side // 2))
        top = max(0, min(bh - side, cy - side // 2))
        cand = base.crop((left, top, left + side, top + side))
        sk = _skin_score(cand)
        score = sk * 2.0 + ent / 10.0
        if score > best_skin:
            best_skin = score
            best_crop = cand

    # contrast polish for rock blend / cards
    rgb = best_crop.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.15)
    return rgb.resize((out_size, out_size), Image.Resampling.LANCZOS)


def crop_for_rushmore(im: Image.Image, size: int) -> Image.Image:
    return smart_head_crop(im, out_size=size)
