"""
Analyzer Module — Upload Burst Detection, Dead Channels, Thumbnail Analysis,
Language Mismatch, Duplicate Detection, Comment Archaeology, Playlist Spelunking
"""

import re
import json
import logging
import subprocess
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
#  UPLOAD BURST DETECTOR
# ═══════════════════════════════════════════════════════════════════════
def detect_upload_bursts(df: pd.DataFrame, threshold: int = 5) -> pd.DataFrame:
    """
    Find channels that uploaded many videos on the same day.
    threshold: minimum uploads in one day to flag as burst.
    Returns DataFrame of burst events.
    """
    if df.empty or "published" not in df.columns or "channel" not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["pub_date"] = pd.to_datetime(df_copy["published"], errors="coerce").dt.date

    bursts = []
    for (channel, pub_date), group in df_copy.groupby(["channel", "pub_date"]):
        if len(group) >= threshold:
            bursts.append({
                "channel": channel,
                "channel_id": group.iloc[0].get("channel_id", ""),
                "date": str(pub_date),
                "upload_count": len(group),
                "video_ids": group["video_id"].tolist(),
                "titles": group["title"].tolist(),
                "total_views": int(group["views"].sum()),
                "avg_weirdness": round(float(group["weirdness_score"].mean()), 1),
                "burst_type": _classify_burst(group),
            })

    return pd.DataFrame(bursts).sort_values("upload_count", ascending=False).reset_index(drop=True) if bursts else pd.DataFrame()


def _classify_burst(group: pd.DataFrame) -> str:
    """Classify a burst: camera dump, bot, phone sync, etc."""
    titles = group["title"].tolist()
    default_count = group["is_default_filename"].sum() if "is_default_filename" in group.columns else 0

    if default_count > len(titles) * 0.7:
        return "📷 Camera Dump"
    elif all(len(t) < 5 for t in titles):
        return "🤖 Bot/Auto"
    elif any("screen" in str(t).lower() or "rec" in str(t).lower() for t in titles):
        return "🖥️ Screen Recordings"
    else:
        return "📤 Bulk Upload"


# ═══════════════════════════════════════════════════════════════════════
#  DEAD CHANNEL FINDER
# ═══════════════════════════════════════════════════════════════════════
def find_dead_channels(df: pd.DataFrame, max_videos: int = 3, min_age_days: int = 365) -> pd.DataFrame:
    """
    Find channels that uploaded very few videos and went silent.
    """
    if df.empty or "channel" not in df.columns:
        return pd.DataFrame()

    channel_groups = df.groupby("channel")
    dead = []
    for channel, group in channel_groups:
        if len(group) <= max_videos:
            oldest = group["age_days"].max() if "age_days" in group.columns else 0
            if oldest >= min_age_days:
                dead.append({
                    "channel": channel,
                    "channel_id": group.iloc[0].get("channel_id", ""),
                    "video_count": len(group),
                    "oldest_video_days": int(oldest),
                    "total_views": int(group["views"].sum()),
                    "avg_weirdness": round(float(group["weirdness_score"].mean()), 1),
                    "titles": group["title"].tolist(),
                    "video_ids": group["video_id"].tolist(),
                })

    return pd.DataFrame(dead).sort_values("oldest_video_days", ascending=False).reset_index(drop=True) if dead else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════
#  THUMBNAIL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def analyze_thumbnails(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag videos likely using auto-generated thumbnails.
    Auto-generated thumbs use YouTube's default pattern:
    i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg (vs custom which are maxresdefault or custom)
    """
    if df.empty or "thumbnail" not in df.columns:
        return df

    df_copy = df.copy()

    def _is_auto_thumb(thumb_url, vid_id):
        if not thumb_url or not vid_id:
            return True
        thumb = str(thumb_url).lower()
        # Auto-generated thumbnails use specific patterns
        if "hqdefault" in thumb or "default.jpg" in thumb:
            return True
        if "mqdefault" in thumb or "sddefault" in thumb:
            return True
        # maxresdefault often means custom but not always
        return False

    df_copy["auto_thumbnail"] = df_copy.apply(
        lambda r: _is_auto_thumb(r.get("thumbnail", ""), r.get("video_id", "")), axis=1
    )
    return df_copy


# ═══════════════════════════════════════════════════════════════════════
#  LANGUAGE MISMATCH DETECTOR
# ═══════════════════════════════════════════════════════════════════════
# Simple heuristic: detect non-Latin scripts in title

SCRIPT_PATTERNS = {
    "CJK": re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]'),
    "Arabic": re.compile(r'[\u0600-\u06ff\u0750-\u077f]'),
    "Cyrillic": re.compile(r'[\u0400-\u04ff]'),
    "Devanagari": re.compile(r'[\u0900-\u097f]'),
    "Thai": re.compile(r'[\u0e00-\u0e7f]'),
    "Hebrew": re.compile(r'[\u0590-\u05ff]'),
}


def detect_title_scripts(title: str) -> List[str]:
    """Detect which scripts are present in a title."""
    scripts = []
    has_latin = bool(re.search(r'[a-zA-Z]', title))
    if has_latin:
        scripts.append("Latin")
    for name, pattern in SCRIPT_PATTERNS.items():
        if pattern.search(title):
            scripts.append(name)
    return scripts


def find_language_mismatches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find videos where title language seems mismatched with channel context.
    Flags mixed-script titles, titles with unusual character distributions.
    """
    if df.empty or "title" not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["title_scripts"] = df_copy["title"].apply(detect_title_scripts)
    df_copy["is_mixed_script"] = df_copy["title_scripts"].apply(lambda s: len(s) > 1)
    df_copy["is_non_latin"] = df_copy["title_scripts"].apply(lambda s: "Latin" not in s and len(s) > 0)

    return df_copy


# ═══════════════════════════════════════════════════════════════════════
#  DUPLICATE DETECTION
# ═══════════════════════════════════════════════════════════════════════
def find_duplicate_titles(df: pd.DataFrame) -> pd.DataFrame:
    """Find videos with identical or near-identical titles (possible re-uploads)."""
    if df.empty or "title" not in df.columns:
        return pd.DataFrame()

    # Normalize titles for comparison
    df_copy = df.copy()
    df_copy["title_norm"] = df_copy["title"].str.lower().str.strip()
    df_copy["title_norm"] = df_copy["title_norm"].str.replace(r'[^\w\s]', '', regex=True)

    dupes = df_copy[df_copy.duplicated(subset=["title_norm"], keep=False)]
    return dupes.sort_values("title_norm").reset_index(drop=True)


def find_title_hash_dupes(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Group videos by normalized title hash."""
    if df.empty:
        return {}

    groups = {}
    for _, row in df.iterrows():
        title_norm = re.sub(r'[^\w]', '', str(row.get("title", "")).lower())
        h = hashlib.md5(title_norm.encode()).hexdigest()[:12]
        if h not in groups:
            groups[h] = []
        groups[h].append(row.get("video_id", ""))

    return {k: v for k, v in groups.items() if len(v) > 1}


# ═══════════════════════════════════════════════════════════════════════
#  PLAYLIST SPELUNKER
# ═══════════════════════════════════════════════════════════════════════
def search_playlists(query: str, max_results: int = 10) -> List[Dict]:
    """Search for YouTube playlists using yt-dlp."""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            f"ytsearch{max_results}:{query} playlist",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        items = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return items
    except Exception as e:
        logger.error(f"Playlist search failed: {e}")
        return []


def spelunk_playlist(playlist_url: str, max_videos: int = 50) -> List[Dict]:
    """Extract videos from a playlist."""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            "--playlist-end", str(max_videos),
            playlist_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        items = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return items
    except Exception as e:
        logger.error(f"Playlist spelunk failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════
#  COMMENT ARCHAEOLOGY
# ═══════════════════════════════════════════════════════════════════════
ARCHAEOLOGY_PHRASES = [
    "how did I get here",
    "3am youtube",
    "weird part of youtube",
    "deep youtube",
    "this side of youtube",
    "why is this recommended",
    "what is this video",
    "found footage",
    "creepy video",
    "nobody has seen this",
    "hidden gem",
    "0 views",
    "am I the only one watching",
    "algorithm brought me",
]


def archaeology_search(phrases: List[str] = None, max_per_phrase: int = 5) -> List[Dict]:
    """Search YouTube using phrases people use when they find weird content."""
    if phrases is None:
        phrases = ARCHAEOLOGY_PHRASES

    all_items = []
    for phrase in phrases:
        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--flat-playlist",
                "--no-download",
                "--no-warnings",
                "--ignore-errors",
                f'ytsearch{max_per_phrase}:"{phrase}"',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    data["_archaeology_phrase"] = phrase
                    all_items.append(data)
                except json.JSONDecodeError:
                    continue
        except Exception:
            continue

    return all_items


# ═══════════════════════════════════════════════════════════════════════
#  WATCH HISTORY
# ═══════════════════════════════════════════════════════════════════════
def load_watch_history() -> List[Dict]:
    """Load watch history from persistence."""
    from modules.persistence import _load_json, DATA_DIR
    return _load_json(DATA_DIR / "watch_history.json", [])


def add_to_watch_history(video_id: str, title: str = "", url: str = ""):
    """Record a video view."""
    from modules.persistence import _load_json, _save_json, DATA_DIR, ensure_data_dir
    ensure_data_dir()
    history = _load_json(DATA_DIR / "watch_history.json", [])
    # Check if already in history
    existing = {h.get("video_id") for h in history}
    if video_id not in existing:
        history.append({
            "video_id": video_id,
            "title": title,
            "url": url,
            "watched_at": datetime.now().isoformat(),
        })
    history = history[-1000:]  # Keep last 1000
    _save_json(DATA_DIR / "watch_history.json", history)


def is_watched(video_id: str) -> bool:
    history = load_watch_history()
    return any(h.get("video_id") == video_id for h in history)
