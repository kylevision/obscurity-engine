"""
Brute Force Module — Video ID Scanner, Time Capsule, Wayback Cross-Check
Generates random YouTube video IDs and checks if they exist.
Also checks Internet Archive's Wayback Machine for captured videos.
"""

import re
import json
import random
import string
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# YouTube video IDs are 11 chars from this alphabet
YT_ID_CHARS = string.ascii_letters + string.digits + "-_"


def generate_random_video_ids(count: int = 50) -> List[str]:
    """Generate random 11-character YouTube video ID candidates."""
    ids = []
    for _ in range(count):
        vid_id = "".join(random.choices(YT_ID_CHARS, k=11))
        ids.append(vid_id)
    return ids


def check_video_exists(video_id: str) -> Optional[Dict]:
    """
    Check if a YouTube video ID exists using yt-dlp.
    Returns metadata dict if exists, None if not.
    """
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--no-playlist",
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip().split("\n")[0])
            except json.JSONDecodeError:
                return None
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return None


def brute_force_scan(batch_size: int = 20, progress_callback=None) -> List[Dict]:
    """
    Generate random video IDs and check which ones exist.
    This is slow (~1-2 sec per check) but finds truly hidden content.
    """
    candidates = generate_random_video_ids(batch_size)
    found = []

    for i, vid_id in enumerate(candidates):
        if progress_callback:
            progress_callback(i, batch_size, vid_id)
        result = check_video_exists(vid_id)
        if result:
            result["_brute_force"] = True
            result["_scan_id"] = vid_id
            found.append(result)

    return found


def generate_near_ids(seed_id: str, count: int = 20) -> List[str]:
    """
    Generate video IDs that are similar to a seed ID.
    YouTube sometimes assigns sequential-ish IDs, so nearby IDs
    may have been uploaded around the same time.
    """
    ids = []
    seed_list = list(seed_id)

    for _ in range(count):
        new_id = seed_list.copy()
        # Modify 1-3 characters
        num_changes = random.randint(1, 3)
        positions = random.sample(range(11), num_changes)
        for pos in positions:
            new_id[pos] = random.choice(YT_ID_CHARS)
        ids.append("".join(new_id))

    return ids


# ═══════════════════════════════════════════════════════════════════════
#  TIME CAPSULE — Find everything from a specific date
# ═══════════════════════════════════════════════════════════════════════
def generate_time_capsule_queries(target_date: datetime) -> List[str]:
    """
    Generate search queries designed to find videos uploaded on a specific date.
    Uses date-string patterns people often use in titles.
    """
    d = target_date
    queries = [
        d.strftime("%Y%m%d"),           # 20140723
        d.strftime("%Y-%m-%d"),         # 2014-07-23
        d.strftime("%m/%d/%Y"),         # 07/23/2014
        d.strftime("%B %d %Y"),         # July 23 2014
        d.strftime("%b %d %Y"),         # Jul 23 2014
        d.strftime("%d %B %Y"),         # 23 July 2014
        f"IMG_{d.strftime('%Y%m%d')}",  # IMG_20140723
        f"VID_{d.strftime('%Y%m%d')}",  # VID_20140723
        f"MOV_{d.strftime('%Y%m%d')}",  # MOV_20140723
        f"DSC_{d.strftime('%Y%m%d')}",  # DSC_20140723
    ]
    return queries


def random_time_capsule_date(min_year: int = 2005, max_year: int = None) -> datetime:
    """Pick a completely random date within YouTube's history."""
    if max_year is None:
        max_year = datetime.now().year
    start = datetime(min_year, 4, 23)  # YouTube launch
    end = datetime.now()
    delta = (end - start).days
    random_days = random.randint(0, delta)
    return start + timedelta(days=random_days)


# ═══════════════════════════════════════════════════════════════════════
#  WAYBACK MACHINE CROSS-CHECK
# ═══════════════════════════════════════════════════════════════════════
def check_wayback(url: str) -> Optional[Dict]:
    """
    Check if the Wayback Machine has a snapshot of a URL.
    Uses the Wayback Availability API.
    """
    import urllib.request
    import urllib.parse

    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "ObscurityEngine/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest")
            if closest and closest.get("available"):
                return {
                    "url": closest.get("url", ""),
                    "timestamp": closest.get("timestamp", ""),
                    "status": closest.get("status", ""),
                }
    except Exception as e:
        logger.debug(f"Wayback check failed for {url}: {e}")
    return None


def check_wayback_batch(video_ids: List[str], progress_callback=None) -> Dict[str, Dict]:
    """Check multiple YouTube video URLs against the Wayback Machine."""
    results = {}
    for i, vid_id in enumerate(video_ids):
        if progress_callback:
            progress_callback(i, len(video_ids), vid_id)
        url = f"https://www.youtube.com/watch?v={vid_id}"
        snap = check_wayback(url)
        if snap:
            results[vid_id] = snap
    return results


# ═══════════════════════════════════════════════════════════════════════
#  METADATA ANOMALY DETECTOR
# ═══════════════════════════════════════════════════════════════════════
OCEAN_COORDS = [
    # Rough bounding boxes for middle-of-ocean locations
    {"name": "Mid-Atlantic", "lat_range": (-30, 30), "lng_range": (-50, -20)},
    {"name": "Mid-Pacific", "lat_range": (-30, 30), "lng_range": (-170, -130)},
    {"name": "Indian Ocean", "lat_range": (-30, 0), "lng_range": (60, 90)},
]

EXTREME_LOCATIONS = [
    {"name": "Antarctica", "lat_range": (-90, -60), "lng_range": (-180, 180)},
    {"name": "Arctic", "lat_range": (75, 90), "lng_range": (-180, 180)},
    {"name": "Sahara Desert", "lat_range": (18, 30), "lng_range": (-5, 30)},
]


def detect_location_anomalies(lat: float, lng: float) -> List[str]:
    """Check if geolocation is in an unusual place."""
    anomalies = []
    for loc in OCEAN_COORDS + EXTREME_LOCATIONS:
        if (loc["lat_range"][0] <= lat <= loc["lat_range"][1] and
                loc["lng_range"][0] <= lng <= loc["lng_range"][1]):
            anomalies.append(loc["name"])
    return anomalies


def detect_metadata_anomalies(row: dict) -> List[str]:
    """
    Flag suspicious metadata combinations.
    Returns list of anomaly descriptions.
    """
    anomalies = []

    # Geo anomaly
    lat = row.get("latitude")
    lng = row.get("longitude")
    if lat is not None and lng is not None:
        try:
            loc_anomalies = detect_location_anomalies(float(lat), float(lng))
            for a in loc_anomalies:
                anomalies.append(f"GEO_ANOMALY:{a}")
        except (ValueError, TypeError):
            pass

    # Very old upload date but HD quality
    age = int(row.get("age_days", 0))
    definition = str(row.get("definition", ""))
    if age > 5475 and definition == "hd":  # >15 years + HD
        anomalies.append("ERA_MISMATCH:HD_before_HD_era")

    # Upload hour anomaly (3-5 AM local time is unusual)
    hour = int(row.get("upload_hour", -1))
    if 3 <= hour <= 5:
        anomalies.append("TIME_ANOMALY:uploaded_3-5AM")

    # Extremely long title
    title_len = len(str(row.get("title", "")))
    if title_len > 200:
        anomalies.append(f"TITLE_ANOMALY:very_long({title_len})")

    # Description much longer than expected for view count
    desc_words = int(row.get("desc_word_count", 0))
    views = int(row.get("views", 0))
    if desc_words > 500 and views < 10:
        anomalies.append("DESC_ANOMALY:huge_desc_no_views")

    # Has many tags but no views
    tag_count = int(row.get("tag_count", 0))
    if tag_count > 20 and views < 5:
        anomalies.append("TAG_ANOMALY:many_tags_no_views")

    # Very short duration anomaly
    dur = int(row.get("duration_seconds", 0))
    if dur == 1:
        anomalies.append("DUR_ANOMALY:1_second")
    elif dur > 43200:  # >12 hours
        anomalies.append(f"DUR_ANOMALY:marathon({dur//3600}h)")

    return anomalies
