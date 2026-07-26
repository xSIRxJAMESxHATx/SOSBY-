"""Game-day weather with multi-source failover + cartoon icons + map links."""
from __future__ import annotations
import io
from typing import Any, Dict, List, Optional, Tuple
import requests
from PIL import Image, ImageDraw, ImageFont

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SBSBY-Weather/1.0"})

# Stadium / home coordinates (lat, lon, label)
VENUES: Dict[str, Tuple[float, float, str]] = {
    "browns": (41.5061, -81.6995, "Huntington Bank Field, Cleveland"),
    "guardians": (41.4962, -81.6852, "Progressive Field, Cleveland"),
    "cavaliers": (41.4965, -81.6882, "Rocket Mortgage FieldHouse, Cleveland"),
    "osu_football": (40.0017, -83.0197, "Ohio Stadium, Columbus"),
    "osu_mbb": (40.0055, -83.0245, "Value City Arena, Columbus"),
    "crew": (39.9685, -83.0165, "Lower.com Field, Columbus"),
    "bluejackets": (39.9692, -83.0061, "Nationwide Arena, Columbus"),
    "usmnt": (40.0, -83.0, "USA match venue (varies)"),
    "usab": (40.0, -83.0, "USA Basketball venue (varies)"),
    "kent_mbb": (41.1490, -81.3412, "MAC Center, Kent"),
    "rhs_football": (39.9547, -82.8121, "Reynoldsburg, OH"),
    "rhs_mbb": (39.9547, -82.8121, "Reynoldsburg, OH"),
    "tiffin_tf": (41.1145, -83.1780, "Tiffin University, Tiffin OH"),
}


def _get_json(url: str, timeout: float = 6.0) -> Optional[dict]:
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def fetch_weather(team_key: str) -> Tuple[dict, str]:
    lat, lon, label = VENUES.get(team_key, (41.5, -81.7, "Cleveland, OH"))
    sources_tried = []

    # 1 Open-Meteo (no key)
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )
        data = _get_json(url)
        if data and "current" in data:
            cur = data["current"]
            code = int(cur.get("weather_code") or 0)
            return {
                "temp_f": cur.get("temperature_2m"),
                "humidity": cur.get("relative_humidity_2m"),
                "wind_mph": cur.get("wind_speed_10m"),
                "precip": cur.get("precipitation"),
                "code": code,
                "summary": _code_to_summary(code),
                "label": label,
                "lat": lat,
                "lon": lon,
            }, "open-meteo"
    except Exception as e:
        sources_tried.append(f"open-meteo:{e}")

    # 2 wttr.in JSON
    try:
        data = _get_json(f"https://wttr.in/{lat},{lon}?format=j1")
        if data:
            cur = (data.get("current_condition") or [{}])[0]
            desc = ((cur.get("weatherDesc") or [{}])[0]).get("value") or "Weather"
            return {
                "temp_f": float(cur.get("temp_F") or 0),
                "humidity": float(cur.get("humidity") or 0),
                "wind_mph": float(cur.get("windspeedMiles") or 0),
                "precip": float(cur.get("precipMM") or 0),
                "code": 0,
                "summary": desc,
                "label": label,
                "lat": lat,
                "lon": lon,
            }, "wttr.in"
    except Exception as e:
        sources_tried.append(f"wttr:{e}")

    # 3 metaweather-style skip — use National Weather Service points
    try:
        pts = _get_json(f"https://api.weather.gov/points/{lat},{lon}")
        if pts:
            forecast_url = (pts.get("properties") or {}).get("forecast")
            if forecast_url:
                fc = _get_json(forecast_url)
                periods = ((fc or {}).get("properties") or {}).get("periods") or []
                if periods:
                    p0 = periods[0]
                    return {
                        "temp_f": p0.get("temperature"),
                        "humidity": None,
                        "wind_mph": None,
                        "precip": None,
                        "code": 0,
                        "summary": p0.get("shortForecast") or p0.get("name"),
                        "label": label,
                        "lat": lat,
                        "lon": lon,
                    }, "weather.gov"
    except Exception as e:
        sources_tried.append(f"nws:{e}")

    # 4 Open-Meteo again with minimal
    # 5 Static fallback
    return {
        "temp_f": "—",
        "humidity": "—",
        "wind_mph": "—",
        "precip": "—",
        "code": -1,
        "summary": "Weather temporarily unavailable",
        "label": label,
        "lat": lat,
        "lon": lon,
    }, "fallback"


def _code_to_summary(code: int) -> str:
    if code == 0: return "Clear / sunny"
    if code in (1, 2, 3): return "Partly cloudy"
    if code in (45, 48): return "Fog"
    if code in (51, 53, 55, 61, 63, 65): return "Rain"
    if code in (71, 73, 75, 77, 85, 86): return "Snow"
    if code in (95, 96, 99): return "Thunderstorm"
    if code in (66, 67): return "Freezing rain"
    return "Mixed conditions"


def map_links(lat: float, lon: float) -> List[dict]:
    return [
        {"name": "OpenStreetMap", "url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"},
        {"name": "Google Maps satellite", "url": f"https://www.google.com/maps/@{lat},{lon},17z/data=!3m1!1e3"},
        {"name": "Google Maps place", "url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"},
        {"name": "Bing Maps", "url": f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=17&style=a"},
        {"name": "Apple Maps (web)", "url": f"https://maps.apple.com/?ll={lat},{lon}&z=16"},
    ]



def weather_cartoon(summary: str, temp_f, lat: float = 41.5) -> bytes:
    """Clean, bold weather badge icon."""
    W, H = 340, 240
    s = (summary or "").lower()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font = small = ImageFont.load_default()

    if "snow" in s or "freezing" in s:
        bg = (180, 205, 230)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([120, 50, 220, 140], fill=(250, 250, 255), outline=(140, 150, 170), width=3)
        d.ellipse([140, 100, 250, 180], fill=(250, 250, 255), outline=(140, 150, 170), width=3)
        for i in range(18):
            x, y = (i * 41) % W, (i * 29) % H
            d.line([(x, y), (x+6, y+6)], fill=(255, 255, 255), width=2)
            d.line([(x+6, y), (x, y+6)], fill=(255, 255, 255), width=2)
        caption = "Lake-effect mode — bundle up"
    elif "thunder" in s or "storm" in s:
        bg = (55, 65, 85)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([70, 30, 270, 110], fill=(75, 80, 95))
        d.polygon([(170, 95), (145, 150), (165, 150), (150, 195), (200, 130), (175, 130)], fill=(255, 220, 50))
        caption = "Storm watch — grab the jacket"
    elif "rain" in s:
        bg = (90, 120, 160)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([80, 40, 260, 120], fill=(100, 110, 130))
        for i in range(12):
            x = 60 + i * 22
            d.line([(x, 130), (x-8, 200)], fill=(180, 210, 255), width=3)
        caption = "Rain on the North Coast"
    elif "clear" in s or "sunny" in s:
        bg = (110, 185, 255)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([110, 45, 230, 165], fill=(255, 210, 40), outline=(255, 170, 0), width=4)
        d.ellipse([140, 85, 158, 103], fill=(40, 40, 40))
        d.ellipse([182, 85, 200, 103], fill=(40, 40, 40))
        d.arc([145, 105, 195, 140], 10, 170, fill=(40, 40, 40), width=3)
        # shades
        d.arc([135, 80, 205, 110], 200, 340, fill=(30, 30, 30), width=3)
        caption = "Sunshine with swagger"
    else:
        bg = (150, 170, 190)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([90, 50, 250, 140], fill=(220, 225, 230), outline=(160, 165, 175), width=3)
        caption = (summary or "Checking the sky…")[:42]

    try:
        tlabel = f"{int(float(temp_f))}°F" if temp_f not in (None, "—") else "—°F"
    except Exception:
        tlabel = "—°F"
    d.rounded_rectangle([12, 12, 100, 48], radius=10, fill=(25, 25, 35))
    d.text((56, 30), tlabel, fill=(255, 220, 100), font=font, anchor="mm")
    d.rounded_rectangle([12, H-42, W-12, H-12], radius=8, fill=(25, 25, 35, 230) if False else (25, 25, 35))
    d.text((W//2, H-27), caption, fill=(240, 240, 245), font=small, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
