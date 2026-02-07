"""
Scraper Engine Module — NO API KEY REQUIRED
Uses yt-dlp's built-in YouTube search (ytsearch:) to find videos.
Zero quota limits, infinite searches, no Google account needed.

Tradeoff: Slower than API (~3-8 sec per query), fewer filter options at
search time (filtering happens post-download), no geolocation data.
"""

import re
import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def scraper_search(
    query: str,
    max_results: int = 25,
    sort_by: str = "relevance",
) -> List[Dict[str, Any]]:
    """
    Search YouTube using yt-dlp's ytsearch extractor.
    Returns a list of video metadata dicts.

    sort_by options: "relevance", "date", "views", "rating"
    """
    try:
        # yt-dlp search syntax: ytsearchN:query
        search_url = f"ytsearch{max_results}:{query}"

        cmd = [
            "yt-dlp",
            "--dump-json",          # Output JSON metadata per video
            "--flat-playlist",      # Don't download, just get info
            "--no-warnings",
            "--no-download",
            "--ignore-errors",
            search_url,
        ]

        # Add sort parameter via extractor args
        if sort_by == "date":
            cmd.extend(["--extractor-args", "youtube:player_skip=webpage"])
            # yt-dlp doesn't support sort directly in ytsearch,
            # but we can use the search URL with sp parameter
            # We'll sort post-fetch instead

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        items = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                items.append(data)
            except json.JSONDecodeError:
                continue

        return items

    except subprocess.TimeoutExpired:
        logger.error("yt-dlp search timed out")
        return []
    except FileNotFoundError:
        logger.error("yt-dlp not found")
        return []
    except Exception as e:
        logger.error(f"Scraper search failed: {e}")
        return []


def scraper_get_details(video_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch full metadata for specific video IDs using yt-dlp.
    This gives us view counts, likes, tags, description, etc.
    """
    results = []
    # Batch in groups of 10 to avoid huge command lines
    for i in range(0, len(video_ids), 10):
        batch = video_ids[i:i + 10]
        urls = [f"https://www.youtube.com/watch?v={vid}" for vid in batch]

        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-warnings",
                "--ignore-errors",
                "--no-playlist",
            ] + urls

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    results.append(data)
                except json.JSONDecodeError:
                    continue

        except subprocess.TimeoutExpired:
            logger.warning(f"yt-dlp detail fetch timed out for batch {i}")
        except Exception as e:
            logger.warning(f"yt-dlp detail fetch failed: {e}")

    return results


def scraper_parse_results(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse yt-dlp JSON output into a DataFrame matching the API engine format.
    Works with both flat-playlist results and full metadata.
    """
    from modules.youtube_engine import compute_weirdness_score, detect_default_filename, _format_duration, _compute_title_entropy

    rows = []
    for item in items:
        vid_id = item.get("id", item.get("url", ""))
        # Some flat results have url like "video_id" not full URL
        if vid_id.startswith("http"):
            vid_id = vid_id.split("v=")[-1].split("&")[0].split("/")[-1]

        title = item.get("title", "Untitled") or "Untitled"
        description = item.get("description", "") or ""
        channel = item.get("channel", item.get("uploader", "Unknown")) or "Unknown"
        channel_id = item.get("channel_id", item.get("uploader_id", "")) or ""

        # Views — flat playlist gives view_count, full gives view_count
        views = int(item.get("view_count", 0) or 0)
        likes = int(item.get("like_count", 0) or 0)
        comments = int(item.get("comment_count", 0) or 0)

        # Duration
        duration = int(item.get("duration", 0) or 0)

        # Upload date — yt-dlp gives YYYYMMDD format
        upload_date = item.get("upload_date", "")
        published_dt = None
        age_days = 0
        published_str = ""
        if upload_date and len(upload_date) >= 8:
            try:
                published_dt = datetime.strptime(upload_date[:8], "%Y%m%d")
                age_days = (datetime.now() - published_dt).days
                published_str = published_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass

        # Tags
        tags = item.get("tags", []) or []

        # Thumbnail
        thumbnails = item.get("thumbnails", [])
        thumb_url = ""
        if thumbnails:
            # Pick a medium-sized one
            for t in thumbnails:
                if t.get("width", 0) >= 300:
                    thumb_url = t.get("url", "")
                    break
            if not thumb_url:
                thumb_url = thumbnails[-1].get("url", "")

        # Computed fields
        is_default = detect_default_filename(title)
        title_ent = _compute_title_entropy(title)
        all_caps = title.isupper() and len(title) > 3
        nums_only = bool(re.match(r'^[\d\s._-]+$', title.strip()))
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F9FF\U0001FA00-\U0001FA6F]', title + description))
        vpd = round(views / max(age_days, 1), 4)
        desc_len = len(description)

        weirdness = compute_weirdness_score(
            title=title, description=description, views=views, likes=likes,
            comments=comments, duration_seconds=duration, age_days=age_days,
            tags=tags, has_location=False, title_entropy=title_ent,
            desc_length=desc_len, all_caps=all_caps, numbers_only=nums_only,
            views_per_day=vpd,
        )

        rows.append({
            "video_id": vid_id,
            "title": title,
            "channel": channel,
            "channel_id": channel_id,
            "published": published_str,
            "published_date": published_dt,
            "upload_day": published_dt.strftime("%A") if published_dt else "",
            "upload_hour": published_dt.hour if published_dt else -1,
            "age_days": age_days,
            "description": description,
            "thumbnail": thumb_url,
            "views": views,
            "likes": likes,
            "comments": comments,
            "favorites": 0,
            "views_per_day": vpd,
            "like_ratio": round((likes / views * 100), 2) if views > 0 else 0.0,
            "comment_ratio": round((comments / views * 100), 2) if views > 0 else 0.0,
            "engagement_total": likes + comments,
            "duration_seconds": duration,
            "duration_fmt": _format_duration(duration),
            "latitude": None,
            "longitude": None,
            "has_geo": False,
            "tags": tags,
            "tag_count": len(tags),
            "topic_categories": [],
            "is_default_filename": is_default,
            "title_entropy": title_ent,
            "title_length": len(title),
            "all_caps_title": all_caps,
            "numbers_only_title": nums_only,
            "has_emoji": has_emoji,
            "desc_length": desc_len,
            "desc_word_count": len(description.split()) if description else 0,
            "has_links_in_desc": bool(re.search(r'https?://', description)),
            "has_hashtags": bool(re.search(r'#\w+', description + title)),
            "definition": "hd" if item.get("height", 0) and item.get("height", 0) >= 720 else "sd",
            "caption": "true" if item.get("subtitles") else "false",
            "licensed_content": False,
            "privacy": "public",
            "weirdness_score": weirdness,
            "url": f"https://www.youtube.com/watch?v={vid_id}",
        })

    return pd.DataFrame(rows)


def scraper_search_full(
    query: str,
    max_results: int = 25,
) -> pd.DataFrame:
    """
    One-shot: search + get details + parse into DataFrame.
    Flat playlist search gets basic info, then we fetch full details
    for view counts, likes, etc.
    """
    # Step 1: search (flat — fast, gets video IDs)
    flat_items = scraper_search(query, max_results=max_results)

    if not flat_items:
        return pd.DataFrame()

    # Extract video IDs
    video_ids = []
    for item in flat_items:
        vid = item.get("id", item.get("url", ""))
        if vid.startswith("http"):
            vid = vid.split("v=")[-1].split("&")[0].split("/")[-1]
        if vid:
            video_ids.append(vid)

    if not video_ids:
        return pd.DataFrame()

    # Step 2: get full details (view counts, likes, tags, etc.)
    detailed = scraper_get_details(video_ids)

    if detailed:
        return scraper_parse_results(detailed)
    else:
        # Fall back to flat results (may lack view counts)
        return scraper_parse_results(flat_items)
