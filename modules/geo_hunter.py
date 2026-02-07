"""
Geo-Hunter Module — Map visualization + City presets + Clickable location picker
"""

import logging
from typing import List, Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
    logger.warning("folium not installed — geo features limited")

DEFAULT_CENTER = (39.8283, -98.5795)
DEFAULT_ZOOM = 4

# ═══════════════════════════════════════════════════════════════════════
#  CITY / LOCATION PRESETS
# ═══════════════════════════════════════════════════════════════════════
LOCATION_PRESETS = {
    "── MAJOR CITIES ──": None,
    "New York, USA": (40.7128, -74.0060),
    "Los Angeles, USA": (34.0522, -118.2437),
    "Chicago, USA": (41.8781, -87.6298),
    "Houston, USA": (29.7604, -95.3698),
    "Miami, USA": (25.7617, -80.1918),
    "London, UK": (51.5074, -0.1278),
    "Paris, France": (48.8566, 2.3522),
    "Berlin, Germany": (52.5200, 13.4050),
    "Rome, Italy": (41.9028, 12.4964),
    "Madrid, Spain": (40.4168, -3.7038),
    "Moscow, Russia": (55.7558, 37.6173),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Seoul, South Korea": (37.5665, 126.9780),
    "Beijing, China": (39.9042, 116.4074),
    "Shanghai, China": (31.2304, 121.4737),
    "Mumbai, India": (19.0760, 72.8777),
    "Delhi, India": (28.7041, 77.1025),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Singapore": (1.3521, 103.8198),
    "Dubai, UAE": (25.2048, 55.2708),
    "Istanbul, Turkey": (41.0082, 28.9784),
    "Cairo, Egypt": (30.0444, 31.2357),
    "São Paulo, Brazil": (-23.5505, -46.6333),
    "Mexico City, Mexico": (19.4326, -99.1332),
    "Buenos Aires, Argentina": (-34.6037, -58.3816),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Melbourne, Australia": (-37.8136, 144.9631),
    "Toronto, Canada": (43.6532, -79.3832),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Nairobi, Kenya": (-1.2921, 36.8219),
    "── UNUSUAL / REMOTE ──": None,
    "Pyongyang, North Korea": (39.0392, 125.7625),
    "Chernobyl, Ukraine": (51.2763, 30.2219),
    "McMurdo Station, Antarctica": (-77.8419, 166.6863),
    "Easter Island, Chile": (-27.1127, -109.3497),
    "Svalbard, Norway": (78.2232, 15.6267),
    "Timbuktu, Mali": (16.7735, -3.0074),
    "Ulaanbaatar, Mongolia": (47.8864, 106.9057),
    "Yakutsk, Russia": (62.0355, 129.6755),
    "Point Nemo (most remote)": (-48.8767, -123.3933),
    "Tristan da Cunha": (-37.1052, -12.2777),
    "── LANDMARKS ──": None,
    "Pyramids of Giza": (29.9792, 31.1342),
    "Machu Picchu": (-13.1631, -72.5450),
    "Angkor Wat": (13.4125, 103.8670),
    "Stonehenge": (51.1789, -1.8262),
    "Area 51": (37.2431, -115.7930),
    "Bermuda Triangle (center)": (25.0000, -71.0000),
    "Chichen Itza": (20.6843, -88.5678),
    "Great Wall (Badaling)": (40.4319, 116.5704),
    "Mount Everest": (27.9881, 86.9250),
    "Mariana Trench": (11.3493, 142.1996),
}


def get_location_presets() -> Dict[str, Optional[Tuple[float, float]]]:
    return LOCATION_PRESETS


def create_base_map(center=DEFAULT_CENTER, zoom=DEFAULT_ZOOM):
    if not HAS_FOLIUM: return None
    return folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter", attr="© CartoDB")


def create_clickable_map(center=DEFAULT_CENTER, zoom=4):
    """Create a map that returns click coordinates."""
    if not HAS_FOLIUM: return None
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter", attr="© CartoDB")
    # Add click-to-get-coords functionality
    m.add_child(folium.LatLngPopup())
    return m


def add_video_markers(m, df, cluster=True):
    if not HAS_FOLIUM or m is None: return m
    geo_df = df.dropna(subset=["latitude", "longitude"])
    if geo_df.empty:
        return m
    if cluster:
        mc = MarkerCluster(name="Videos").add_to(m)
        target = mc
    else:
        target = m
    for _, row in geo_df.iterrows():
        views = int(row.get("views", 0))
        color = "green" if views == 0 else "blue" if views < 100 else "orange" if views < 1000 else "red"
        popup = f"""<div style="font-family:monospace;background:#0a0a0a;color:#33ff33;padding:8px;border:1px solid #33ff33;min-width:200px">
            <b style="color:#33ffff">{_esc(row.get('title','?'))}</b><br>
            V:{views:,} | {row.get('duration_fmt','?')} | {str(row.get('published',''))[:10]}<br>
            <a href="{row.get('url','#')}" target="_blank" style="color:#ffb000">[OPEN]</a></div>"""
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup, max_width=350),
            tooltip=f"{row.get('title','')[:30]} ({views:,}v)",
            icon=folium.Icon(color=color, icon="play", prefix="fa"),
        ).add_to(target)
    return m


def add_search_radius(m, center, radius_km):
    if not HAS_FOLIUM or m is None: return m
    folium.Circle(
        location=center, radius=radius_km * 1000,
        color="#33ff33", fill=True, fill_color="#33ff33",
        fill_opacity=0.05, weight=2, dash_array="10",
        tooltip=f"Radius: {radius_km}km",
    ).add_to(m)
    folium.Marker(
        location=center,
        icon=folium.DivIcon(
            html='<div style="width:12px;height:12px;background:#ff3333;border:2px solid #33ff33;border-radius:50%;box-shadow:0 0 8px #33ff33"></div>',
            icon_size=(12, 12), icon_anchor=(6, 6),
        ),
        tooltip="Center",
    ).add_to(m)
    return m


def create_heatmap(df, center=DEFAULT_CENTER, zoom=DEFAULT_ZOOM):
    if not HAS_FOLIUM: return None
    m = create_base_map(center, zoom)
    geo_df = df.dropna(subset=["latitude", "longitude"])
    if geo_df.empty:
        return m
    HeatMap(
        geo_df[["latitude", "longitude"]].values.tolist(),
        gradient={0.2: "#000080", 0.4: "#33ffff", 0.6: "#33ff33", 0.8: "#ffb000", 1.0: "#ff3333"},
        radius=15, blur=10,
    ).add_to(m)
    return m


def _esc(t):
    if not t: return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
