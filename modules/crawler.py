"""
Crawler Module — Related Video Crawling, Channel Autopsy, Deep Roulette
Uses yt-dlp to crawl YouTube's recommendation graph and find adjacent obscurity.
No API key required.
"""

import re
import json
import random
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def get_related_videos(video_id: str, max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch videos related/suggested by YouTube for a given video.
    Uses yt-dlp to extract the 'related videos' from the watch page.
    No API key needed.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            "--extractor-args", "youtube:player_skip=webpage",
            f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        items = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                vid = data.get("id", data.get("url", ""))
                if vid and vid != video_id:
                    items.append(data)
            except json.JSONDecodeError:
                continue
        return items[:max_results]
    except Exception as e:
        logger.error(f"Related video fetch failed: {e}")
        return []


def crawl_related_chain(start_video_id: str, depth: int = 3, per_level: int = 5,
                         progress_callback=None) -> List[Dict[str, Any]]:
    """
    Crawl the related video graph starting from a seed video.
    Goes N levels deep, collecting per_level videos at each hop.
    Returns all unique videos found.
    """
    visited = {start_video_id}
    all_found = []
    current_level = [start_video_id]

    for d in range(depth):
        next_level = []
        for vid_id in current_level:
            if progress_callback:
                progress_callback(d, vid_id)
            related = get_related_videos(vid_id, max_results=per_level)
            for item in related:
                rid = item.get("id", item.get("url", ""))
                if rid and rid not in visited:
                    visited.add(rid)
                    item["_crawl_depth"] = d + 1
                    item["_crawl_source"] = vid_id
                    all_found.append(item)
                    next_level.append(rid)
        # Only take a subset to avoid exponential blowup
        current_level = next_level[:per_level]

    return all_found


def channel_autopsy(channel_id: str, max_videos: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch all (or up to max_videos) uploads from a channel using yt-dlp.
    No API key needed. Returns raw yt-dlp JSON items.
    """
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            "--playlist-end", str(max_videos),
            url,
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
        logger.error(f"Channel autopsy failed: {e}")
        return []


def channel_autopsy_full(channel_id: str, max_videos: int = 50) -> pd.DataFrame:
    """
    Full channel autopsy: fetch videos, get details, parse into DataFrame.
    """
    from modules.scraper_engine import scraper_get_details, scraper_parse_results

    flat = channel_autopsy(channel_id, max_videos)
    if not flat:
        return pd.DataFrame()

    # Extract IDs
    video_ids = []
    for item in flat:
        vid = item.get("id", item.get("url", ""))
        if vid.startswith("http"):
            vid = vid.split("v=")[-1].split("&")[0].split("/")[-1]
        if vid:
            video_ids.append(vid)

    if not video_ids:
        return pd.DataFrame()

    # Get full details
    detailed = scraper_get_details(video_ids[:max_videos])
    if detailed:
        return scraper_parse_results(detailed)
    else:
        return scraper_parse_results(flat)


def deep_roulette_pick(leaderboard: List[Dict] = None) -> Optional[str]:
    """
    Pick a random video for deep web roulette.
    Strategy: generate random search, pick a 0-view result.
    Returns a video ID or None.
    """
    from modules.youtube_engine import generate_chaos_queries, FILENAME_PATTERNS
    import random

    # Strategy 1: random filename + random numbers
    queries = generate_chaos_queries(3)
    query = random.choice(queries)

    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            f"ytsearch5:{query}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        items = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        if items:
            pick = random.choice(items)
            vid = pick.get("id", pick.get("url", ""))
            if vid.startswith("http"):
                vid = vid.split("v=")[-1].split("&")[0].split("/")[-1]
            return vid
    except Exception as e:
        logger.error(f"Roulette pick failed: {e}")

    return None


def deep_roulette_batch(count: int = 10) -> List[str]:
    """Generate a batch of random video IDs for roulette."""
    from modules.youtube_engine import generate_chaos_queries
    import random

    all_ids = []
    queries = generate_chaos_queries(count)

    for query in queries:
        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--flat-playlist",
                "--no-download",
                "--no-warnings",
                "--ignore-errors",
                f"ytsearch3:{query}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    vid = data.get("id", data.get("url", ""))
                    if vid.startswith("http"):
                        vid = vid.split("v=")[-1].split("&")[0].split("/")[-1]
                    if vid:
                        all_ids.append(vid)
                except json.JSONDecodeError:
                    continue
        except Exception:
            continue

    random.shuffle(all_ids)
    return all_ids[:count]
