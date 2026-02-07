"""
Media Analyzer Module — Audio Detection, Frame Analysis, Subtitle Mining
Uses ffprobe and yt-dlp for deep media inspection without downloading full videos.
"""

import re
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
#  AUDIO ANALYSIS — Detect silent/static/missing audio
# ═══════════════════════════════════════════════════════════════════════
def check_audio_stream(video_url: str) -> Dict[str, Any]:
    """
    Check if a video has an audio stream and its properties.
    Uses yt-dlp to get format info without downloading.
    """
    try:
        cmd = [
            "yt-dlp", "--dump-json", "--no-download",
            "--no-warnings", "--no-playlist", video_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            return {"has_audio": None, "error": "fetch_failed"}

        data = json.loads(result.stdout.strip().split("\n")[0])
        formats = data.get("formats", [])

        has_audio = False
        audio_codec = None
        audio_bitrate = 0

        for fmt in formats:
            acodec = fmt.get("acodec", "none")
            if acodec and acodec != "none":
                has_audio = True
                audio_codec = acodec
                abr = fmt.get("abr", 0) or 0
                if abr > audio_bitrate:
                    audio_bitrate = abr

        return {
            "has_audio": has_audio,
            "audio_codec": audio_codec,
            "audio_bitrate": audio_bitrate,
            "is_silent": not has_audio,
            "is_low_bitrate": audio_bitrate > 0 and audio_bitrate < 32,
            "format_count": len(formats),
        }
    except Exception as e:
        return {"has_audio": None, "error": str(e)}


def batch_audio_check(video_ids: List[str], progress_callback=None) -> Dict[str, Dict]:
    """Check audio for multiple videos."""
    results = {}
    for i, vid_id in enumerate(video_ids):
        if progress_callback:
            progress_callback(i, len(video_ids), vid_id)
        url = f"https://www.youtube.com/watch?v={vid_id}"
        results[vid_id] = check_audio_stream(url)
    return results


# ═══════════════════════════════════════════════════════════════════════
#  SUBTITLE MINING — Search within auto-generated captions
# ═══════════════════════════════════════════════════════════════════════
def fetch_subtitles(video_id: str, lang: str = "en") -> Optional[str]:
    """
    Fetch auto-generated subtitles for a video.
    Returns subtitle text or None.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-langs", lang,
            "--skip-download",
            "--sub-format", "vtt",
            "-o", "/tmp/oe_subs_%(id)s",
            "--no-warnings",
            "--no-playlist",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Try to read the subtitle file
        import glob
        sub_files = glob.glob(f"/tmp/oe_subs_{video_id}*.vtt")
        if sub_files:
            with open(sub_files[0], "r", errors="ignore") as f:
                text = f.read()
            # Clean up
            for sf in sub_files:
                try:
                    import os
                    os.remove(sf)
                except:
                    pass
            # Strip VTT formatting, keep just text
            lines = []
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                    continue
                if re.match(r'^\d{2}:\d{2}', line):
                    continue
                if "-->" in line:
                    continue
                # Remove HTML tags
                line = re.sub(r'<[^>]+>', '', line)
                if line:
                    lines.append(line)
            return " ".join(lines)
        return None
    except Exception as e:
        logger.debug(f"Subtitle fetch failed: {e}")
        return None


def search_subtitles(video_ids: List[str], search_term: str,
                     progress_callback=None) -> List[Dict]:
    """Search within auto-generated subtitles of multiple videos."""
    matches = []
    for i, vid_id in enumerate(video_ids):
        if progress_callback:
            progress_callback(i, len(video_ids), vid_id)
        text = fetch_subtitles(vid_id)
        if text and search_term.lower() in text.lower():
            # Find context around match
            idx = text.lower().index(search_term.lower())
            start = max(0, idx - 100)
            end = min(len(text), idx + len(search_term) + 100)
            context = text[start:end]
            matches.append({
                "video_id": vid_id,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "context": f"...{context}...",
                "full_text_length": len(text),
            })
    return matches


# ═══════════════════════════════════════════════════════════════════════
#  UPLOAD PATTERN FINGERPRINTING
# ═══════════════════════════════════════════════════════════════════════
def fingerprint_upload_pattern(df) -> Dict[str, Any]:
    """
    Analyze a channel's upload patterns to identify bot vs human behavior.
    """
    if df.empty:
        return {"pattern": "unknown", "confidence": 0}

    result = {
        "total_videos": len(df),
        "flags": [],
        "score": 0,  # 0=human, 100=bot
    }

    # Check title patterns
    titles = df["title"].tolist() if "title" in df.columns else []
    if titles:
        # Same title repeated
        from collections import Counter
        tc = Counter(titles)
        most_common_count = tc.most_common(1)[0][1] if tc else 0
        if most_common_count > 3:
            result["flags"].append(f"REPEATED_TITLE:{most_common_count}x")
            result["score"] += 25

        # Sequential numbering
        numbered = sum(1 for t in titles if re.match(r'^.*\d{3,}.*$', str(t)))
        if numbered > len(titles) * 0.5:
            result["flags"].append(f"SEQUENTIAL_NUMBERS:{numbered}/{len(titles)}")
            result["score"] += 20

        # Very short titles
        short = sum(1 for t in titles if len(str(t)) < 5)
        if short > len(titles) * 0.5:
            result["flags"].append(f"SHORT_TITLES:{short}/{len(titles)}")
            result["score"] += 15

    # Check duration consistency
    if "duration_seconds" in df.columns:
        durs = df["duration_seconds"].tolist()
        if durs:
            unique_durs = len(set(durs))
            if unique_durs <= 3 and len(durs) > 5:
                result["flags"].append(f"SAME_DURATION:{unique_durs}_unique")
                result["score"] += 20

    # Check upload time consistency
    if "upload_hour" in df.columns:
        hours = df[df["upload_hour"] >= 0]["upload_hour"].tolist()
        if hours:
            hour_counts = Counter(hours)
            top_hour_pct = hour_counts.most_common(1)[0][1] / len(hours) * 100
            if top_hour_pct > 80:
                result["flags"].append(f"SAME_HOUR:{top_hour_pct:.0f}%")
                result["score"] += 15

    # Check default filenames
    if "is_default_filename" in df.columns:
        def_pct = df["is_default_filename"].sum() / len(df) * 100
        if def_pct > 80:
            result["flags"].append(f"DEFAULT_NAMES:{def_pct:.0f}%")
            result["score"] += 15

    result["score"] = min(result["score"], 100)
    if result["score"] >= 60:
        result["pattern"] = "BOT/AUTOMATED"
    elif result["score"] >= 30:
        result["pattern"] = "SEMI-AUTOMATED"
    else:
        result["pattern"] = "HUMAN"

    return result
