"""
YouTube Search Engine Module — v4 ULTRA EDITION
Every conceivable filter, heuristic, and weirdness detector for finding
the absolute most obscure, forgotten, and bizarre content on YouTube.
"""

import re
import math
import random
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter

import pandas as pd

try:
    import isodate
    HAS_ISODATE = True
except ImportError:
    HAS_ISODATE = False

def _parse_duration(dur_str):
    """Parse ISO 8601 duration with or without isodate."""
    if not dur_str:
        return 0
    if HAS_ISODATE:
        try:
            return int(isodate.parse_duration(dur_str).total_seconds())
        except Exception:
            pass
    # Fallback: parse PT#H#M#S manually
    import re
    try:
        hours = re.search(r'(\d+)H', dur_str)
        minutes = re.search(r'(\d+)M', dur_str)
        seconds = re.search(r'(\d+)S', dur_str)
        total = 0
        if hours: total += int(hours.group(1)) * 3600
        if minutes: total += int(minutes.group(1)) * 60
        if seconds: total += int(seconds.group(1))
        return total
    except Exception:
        return 0

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
#  FILENAME PATTERNS
# ═══════════════════════════════════════════════════════════════════════
FILENAME_PATTERNS = {
    "IMG_XXXX": "IMG_", "DSC_XXXX": "DSC_", "DSCN_XXXX": "DSCN_",
    "DSCF_XXXX": "DSCF_", "MVI_XXXX": "MVI_", "P10XXXXX": "P10",
    "SAM_XXXX": "SAM_", "CIMG_XXXX": "CIMG", "PICT_XXXX": "PICT",
    "CRW_XXXX": "CRW_", "IMGP_XXXX": "IMGP", "_MG_XXXX": "_MG_",
    "MOV_XXXX": "MOV_", "VID_XXXX": "VID_", "VIDEO_XXXX": "VIDEO_",
    "Trim_XXXX": "trim", "Screen Recording": "screen recording",
    "Screencast": "screencast", "20XX-XX-XX": "2009-",
    "FullSizeRender": "FullSizeRender", "RPReplay": "RPReplay",
    "InShot": "InShot_",
    "GOPR_XXXX": "GOPR", "GP_XXXXXX": "GP0", "GX_XXXXXX": "GX01",
    "HERO_XXXX": "HERO", "GH_XXXXXX": "GH01",
    "DJI_XXXX": "DJI_", "DJI_0XXX": "DJI_0",
    "DCIM": "DCIM", "100MEDIA": "100MEDIA", "100ANDRO": "100ANDRO",
    "Untitled": "Untitled", "New Video": "new video",
    "Video 1": '"video 1"', "test": "test video upload",
    "Copy of": "copy of", "Movie on": "movie on",
    "clip": '"clip"', "recording": '"recording"',
    "capture": '"capture"', "vlcsnap": "vlcsnap",
    "bandicam": "bandicam", "OBS_": "OBS ",
    "Rec_": "Rec_", "WIN_": "WIN_",
    "Skype call": "skype call", "Zoom_": "zoom meeting recording",
    "Hangouts": "hangouts video", "Facetime": "facetime recording",
}

PATTERN_CATEGORIES = {
    "📷 DSLR / Mirrorless": [
        "IMG_XXXX", "DSC_XXXX", "DSCN_XXXX", "DSCF_XXXX", "MVI_XXXX",
        "P10XXXXX", "SAM_XXXX", "CIMG_XXXX", "PICT_XXXX", "CRW_XXXX",
        "IMGP_XXXX", "_MG_XXXX",
    ],
    "📱 Phone / Tablet": [
        "MOV_XXXX", "VID_XXXX", "VIDEO_XXXX", "Trim_XXXX",
        "Screen Recording", "Screencast", "20XX-XX-XX",
        "FullSizeRender", "RPReplay", "InShot",
    ],
    "🎬 Action / Drone": [
        "GOPR_XXXX", "GP_XXXXXX", "GX_XXXXXX", "HERO_XXXX",
        "GH_XXXXXX", "DJI_XXXX", "DJI_0XXX",
    ],
    "📁 Generic / Lazy": [
        "DCIM", "100MEDIA", "100ANDRO", "Untitled", "New Video",
        "Video 1", "test", "Copy of", "Movie on", "clip",
        "recording", "capture",
    ],
    "🖥️ Screen Capture": ["vlcsnap", "bandicam", "OBS_", "Rec_", "WIN_"],
    "📞 Webcam / Call": ["Skype call", "Zoom_", "Hangouts", "Facetime"],
}

WEIRDNESS_BOOSTERS = [
    "found footage", "abandoned", "3am", "liminal", "backrooms", "vhs",
    "old tape", "camcorder", "security camera", "cctv", "dashcam",
    "trail cam", "baby monitor", "answering machine", "voicemail",
    "thrift store", "yard sale", "estate sale", "dumpster",
    "strange noise", "unknown", "mysterious", "unexplained",
    "glitch", "corrupted", "cursed", "weird", "creepy",
    "empty", "nobody", "forgotten", "lost media",
    "found in attic", "found in basement", "hidden camera",
    "ring doorbell", "infrared", "night vision", "thermal",
    "police scanner", "ham radio", "shortwave", "numbers station",
    "elevator", "stairwell", "parking garage", "tunnel",
    "underwater", "cave", "sewer", "drain",
    "time capsule", "1990s", "2000s", "childhood",
    "before internet", "dialup", "geocities",
]

RANDOM_DEEP_QUERIES = {
    "🎰 Filename Roulette": [
        "IMG_0001", "VID_20100315", "MVI_3842", "GOPR0001",
        "DSC00001", "MOV_0023", "DJI_0042", "DSCN4521",
        "trim.8A3B2C1D", "P1070832", "SAM_1234", "100_0001",
        "IMG_2847", "VID_20080723", "DSCF0019", "MVI_8392",
    ],
    "📼 Analog / Tape": [
        "vhs tape", "camcorder footage", "home video 1990",
        "tape recording", "8mm film", "hi8 footage",
        "betamax", "vhs-c", "handycam", "super 8",
        "film transfer", "digitized tape", "mini dv",
    ],
    "🏚️ Abandoned / Liminal": [
        "abandoned building walk", "empty mall footage",
        "liminal space video", "empty parking lot night",
        "closed store footage", "dead mall walking",
        "abandoned school inside", "empty hallway",
        "motel room", "empty pool", "closed amusement park",
    ],
    "📹 Surveillance": [
        "cctv footage", "security camera recording", "dashcam footage",
        "trail cam animal", "ring doorbell night", "baby monitor",
        "parking lot camera", "elevator camera footage",
        "warehouse camera", "doorbell cam", "nanny cam",
    ],
    "🌍 Street Footage": [
        "street walk", "driving through town", "bus ride window",
        "train window view", "ferry ride video", "road trip footage",
        "walking around", "bike ride POV", "neighborhood walk",
    ],
    "👻 Found Footage": [
        "found footage", "found this tape", "found camera",
        "found phone video", "old sd card", "found usb",
        "thrift store tape", "estate sale video", "found in trash",
    ],
    "🧪 Glitch / Corrupt": [
        "corrupted video", "glitch footage", "datamosh",
        "broken video file", "video error", "codec error",
        "video artifact", "rendering error",
    ],
    "🌙 Night / Dark": [
        "night footage", "3am video", "night walk",
        "night drive", "infrared camera", "night vision video",
        "dark room", "flashlight exploration",
    ],
    "🏠 Mundane Uploads": [
        "my cat sleeping", "cooking dinner", "backyard video",
        "my room tour 2009", "first video", "unboxing 2007",
        "my dog", "my house", "my car",
    ],
    "🌐 Non-English": [
        "ビデオ", "فيديو", "видео", "비디오", "วิดีโอ",
        "video casero", "vídeo de casa", "altes video",
    ],
    "📅 Date Uploads": [
        "2007-06-15", "2008-12-25", "2009-03-01",
        "2010-08-20", "2011-01-01", "2006-09-10",
        "january 2008", "christmas 2007", "summer 2009",
    ],
    "🔇 Silent / Minimal": [
        "no sound", "silent video", "muted video",
        "screen recording no audio", "quiet", "no audio",
    ],
}

TEMPORAL_PRESETS = {
    "📆 Custom Range": (None, None),
    "🦖 YouTube Primordial (2005–2007)": (datetime(2005, 4, 23), datetime(2007, 12, 31)),
    "📼 Pre-HD Era (2005–2009)": (datetime(2005, 4, 23), datetime(2009, 12, 31)),
    "📱 Early Smartphone (2007–2010)": (datetime(2007, 6, 29), datetime(2010, 12, 31)),
    "🎥 HD Transition (2009–2012)": (datetime(2009, 1, 1), datetime(2012, 12, 31)),
    "👤 Pre-Google+ (2005–2011)": (datetime(2005, 1, 1), datetime(2011, 10, 31)),
    "📸 Instagram Era (2012–2015)": (datetime(2012, 1, 1), datetime(2015, 12, 31)),
    "📲 4K Transition (2015–2018)": (datetime(2015, 1, 1), datetime(2018, 12, 31)),
    "🏠 COVID Lockdown (Mar–Jun 2020)": (datetime(2020, 3, 1), datetime(2020, 6, 30)),
    "🦠 Full COVID (2020–2021)": (datetime(2020, 1, 1), datetime(2021, 12, 31)),
    "📅 Exactly 5 Years Ago": (datetime.now() - timedelta(days=1830), datetime.now() - timedelta(days=1820)),
    "📅 Exactly 10 Years Ago": (datetime.now() - timedelta(days=3660), datetime.now() - timedelta(days=3640)),
    "📅 Exactly 15 Years Ago": (datetime.now() - timedelta(days=5490), datetime.now() - timedelta(days=5470)),
    "🕐 Last 24 Hours": (datetime.now() - timedelta(hours=24), datetime.now()),
    "🕐 Last 7 Days": (datetime.now() - timedelta(days=7), datetime.now()),
    "🕐 Last 30 Days": (datetime.now() - timedelta(days=30), datetime.now()),
    "🕐 Last 90 Days": (datetime.now() - timedelta(days=90), datetime.now()),
    "🕐 Last Year": (datetime.now() - timedelta(days=365), datetime.now()),
}

VIDEO_CATEGORIES = {
    "Any Category": "",
    "🎬 Film & Animation": "1", "🚗 Autos & Vehicles": "2",
    "🎵 Music": "10", "🐱 Pets & Animals": "15",
    "🏀 Sports": "17", "✈️ Travel & Events": "19",
    "🎮 Gaming": "20", "📹 Videoblog": "21",
    "👥 People & Blogs": "22", "😂 Comedy": "23",
    "🎭 Entertainment": "24", "📰 News & Politics": "25",
    "🎨 How-to & Style": "26", "📚 Education": "27",
    "🔬 Science & Tech": "28", "🏛️ Nonprofits": "29",
}

REGION_CODES = {
    "🌍 Any Region": "", "🇺🇸 US": "US", "🇬🇧 UK": "GB", "🇨🇦 Canada": "CA",
    "🇦🇺 Australia": "AU", "🇯🇵 Japan": "JP", "🇰🇷 S.Korea": "KR",
    "🇩🇪 Germany": "DE", "🇫🇷 France": "FR", "🇧🇷 Brazil": "BR",
    "🇮🇳 India": "IN", "🇷🇺 Russia": "RU", "🇲🇽 Mexico": "MX",
    "🇮🇩 Indonesia": "ID", "🇹🇷 Turkey": "TR", "🇹🇭 Thailand": "TH",
    "🇻🇳 Vietnam": "VN", "🇵🇭 Philippines": "PH", "🇪🇬 Egypt": "EG",
    "🇳🇬 Nigeria": "NG", "🇿🇦 S.Africa": "ZA", "🇦🇪 UAE": "AE",
    "🇦🇷 Argentina": "AR", "🇨🇱 Chile": "CL", "🇨🇴 Colombia": "CO", "🇪🇸 Spain": "ES",
    "🇮🇹 Italy": "IT", "🇵🇱 Poland": "PL", "🇳🇱 Netherlands": "NL",
    "🇸🇪 Sweden": "SE", "🇳🇴 Norway": "NO", "🇫🇮 Finland": "FI",
    "🇩🇰 Denmark": "DK", "🇨🇿 Czechia": "CZ", "🇬🇷 Greece": "GR",
    "🇵🇹 Portugal": "PT", "🇷🇴 Romania": "RO", "🇭🇺 Hungary": "HU",
    "🇮🇱 Israel": "IL", "🇸🇦 Saudi Arabia": "SA",
    "🇵🇰 Pakistan": "PK", "🇧🇩 Bangladesh": "BD", "🇲🇾 Malaysia": "MY",
    "🇸🇬 Singapore": "SG", "🇹🇼 Taiwan": "TW", "🇭🇰 Hong Kong": "HK",
    "🇳🇿 New Zealand": "NZ", "🇵🇪 Peru": "PE", "🇺🇦 Ukraine": "UA",
    "🇧🇪 Belgium": "BE", "🇦🇹 Austria": "AT", "🇨🇭 Switzerland": "CH",
    "🇮🇪 Ireland": "IE", "🇰🇪 Kenya": "KE",
}

RELEVANCE_LANGUAGES = {
    "Any Language": "", "English": "en", "Spanish": "es", "Japanese": "ja",
    "Korean": "ko", "Portuguese": "pt", "French": "fr", "German": "de",
    "Russian": "ru", "Hindi": "hi", "Arabic": "ar", "Chinese": "zh",
    "Thai": "th", "Vietnamese": "vi", "Indonesian": "id", "Turkish": "tr",
    "Italian": "it", "Dutch": "nl", "Polish": "pl", "Swedish": "sv",
    "Greek": "el", "Hebrew": "he", "Romanian": "ro", "Czech": "cs",
    "Hungarian": "hu", "Finnish": "fi", "Norwegian": "no", "Danish": "da",
    "Malay": "ms", "Filipino": "tl", "Ukrainian": "uk", "Bengali": "bn",
}

DEFAULT_FILENAME_RE = [
    r"^IMG[\s_-]\d{3,}", r"^DSC[NF]?[\s_-]?\d{3,}", r"^MOV[\s_-]\d{3,}",
    r"^VID[\s_-]?\d{4,}", r"^MVI[\s_-]\d{3,}", r"^GOPR?\d{3,}",
    r"^G[XHP]\d{4,}", r"^DJI[\s_-]\d{3,}", r"^SAM[\s_-]\d{3,}",
    r"^P\d{7}", r"^20\d{2}[\s_-]?\d{2}[\s_-]?\d{2}",
    r"^video[\s_-]?\d{1,4}$", r"^clip[\s_-]?\d",
    r"^trim[\s._]", r"^Untitled", r"^Movie on \d",
    r"^recording[\s_-]?\d", r"^Screen Recording",
    r"^Screencast", r"^capture[\s_-]?\d",
    r"^\d{3,4}[\s_-]\d{3,4}$", r"^CIMG\d{3,}",
    r"^PICT\d{3,}", r"^CRW[\s_-]\d{3,}", r"^IMGP\d{3,}",
    r"^_MG_\d{3,}", r"^100[\s_-]\d{3,}", r"^vlcsnap",
    r"^bandicam", r"^OBS[\s_-]", r"^Rec[\s_-]\d",
    r"^WIN[\s_-]\d", r"^FullSizeRender", r"^RPReplay",
    r"^InShot[\s_-]", r"^new video$", r"^test$",
    r"^copy of ", r"^video$", r"^\d{10,}$",
    r"^[0-9a-f]{8,}$", r"^[A-Z]{2,4}[\s_-]\d{4,}$",
]


# ═══════════════════════════════════════════════════════════════════════
#  CORE API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════
def build_search_queries(keywords="", filename_patterns=None, custom_pattern="", weirdness_keywords=None):
    queries = []
    if keywords.strip():
        queries.append(keywords.strip())
    if filename_patterns:
        for pk in filename_patterns:
            p = FILENAME_PATTERNS.get(pk, pk)
            queries.append(f"{p} {keywords.strip()}" if keywords.strip() else p)
    if custom_pattern.strip():
        queries.append(custom_pattern.strip())
    if weirdness_keywords:
        for wk in weirdness_keywords:
            queries.append(f"{wk} {keywords.strip()}" if keywords.strip() else wk)
    seen = set()
    result = []
    for q in queries:
        ql = q.strip().lower()
        if ql not in seen:
            seen.add(ql)
            result.append(q.strip())
    return result if result else ["IMG_"]


def search_youtube(
    service, query: str, max_results: int = 25,
    published_after: Optional[datetime] = None, published_before: Optional[datetime] = None,
    location: Optional[Tuple[float, float]] = None, location_radius: str = "10km",
    order: str = "date", video_duration: str = "any",
    page_token: Optional[str] = None, region_code: str = "",
    relevance_language: str = "", video_category_id: str = "",
    video_license: str = "any", video_definition: str = "any",
    safe_search: str = "none", event_type: str = "", channel_id: str = "",
    video_embeddable: str = "any", video_syndicated: str = "any",
    video_type: str = "any", topic_id: str = "",
) -> Dict[str, Any]:
    try:
        # Use page_token if provided, and cap per-page request at 50
        params = {"part": "snippet", "q": query, "type": "video",
                  "maxResults": min(max_results, 50), "order": order, "safeSearch": safe_search}
        
        if published_after: params["publishedAfter"] = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")
        if published_before: params["publishedBefore"] = published_before.strftime("%Y-%m-%dT%H:%M:%SZ")
        if location:
            params["location"] = f"{location[0]},{location[1]}"
            params["locationRadius"] = location_radius
        if video_duration != "any": params["videoDuration"] = video_duration
        
        # KEY CHANGE: Support Deep Paging
        if page_token: params["pageToken"] = page_token
            
        if region_code: params["regionCode"] = region_code
        if relevance_language: params["relevanceLanguage"] = relevance_language
        if video_category_id: params["videoCategoryId"] = video_category_id
        if video_license != "any": params["videoLicense"] = video_license
        if video_definition != "any": params["videoDefinition"] = video_definition
        if event_type: params["eventType"] = event_type
        if channel_id: params["channelId"] = channel_id
        if video_embeddable != "any": params["videoEmbeddable"] = video_embeddable
        if video_syndicated != "any": params["videoSyndicated"] = video_syndicated
        if video_type != "any": params["videoType"] = video_type
        if topic_id: params["topicId"] = topic_id
        
        response = service.search().list(**params).execute()
        return {"items": response.get("items", []), "nextPageToken": response.get("nextPageToken"),
                "prevPageToken": response.get("prevPageToken"),
                "totalResults": response.get("pageInfo", {}).get("totalEstimatedResults", 0)}
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return {"items": [], "nextPageToken": None, "prevPageToken": None, "totalResults": 0, "error": str(e)}


def get_video_details(service, video_ids: List[str]) -> List[Dict[str, Any]]:
    all_details = []
    # Batch details in groups of 50
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        try:
            response = service.videos().list(
                part="snippet,statistics,contentDetails,recordingDetails,topicDetails,status",
                id=",".join(batch)).execute()
            all_details.extend(response.get("items", []))
        except Exception as e:
            logger.error(f"Failed to get video details: {e}")
    return all_details


def get_channel_info(service, channel_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = service.channels().list(part="snippet,statistics,brandingSettings", id=channel_id).execute()
        items = response.get("items", [])
        if items:
            ch = items[0]; stats = ch.get("statistics", {}); snippet = ch.get("snippet", {})
            return {"channel_id": channel_id, "title": snippet.get("title", ""),
                    "description": snippet.get("description", "")[:400],
                    "created": snippet.get("publishedAt", ""), "country": snippet.get("country", ""),
                    "subscribers": int(stats.get("subscriberCount", 0)),
                    "total_views": int(stats.get("viewCount", 0)),
                    "video_count": int(stats.get("videoCount", 0)),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "hidden_subs": stats.get("hiddenSubscriberCount", False)}
    except Exception as e:
        logger.error(f"Channel info fetch failed: {e}")
    return None


def search_channel_videos(service, channel_id: str, max_results: int = 50, order: str = "date") -> List[Dict]:
    try:
        result = search_youtube(service=service, query="", max_results=max_results, order=order, channel_id=channel_id)
        return result.get("items", [])
    except Exception as e:
        logger.error(f"Channel video search failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════
#  DATA PARSING & ENRICHMENT
# ═══════════════════════════════════════════════════════════════════════
def parse_video_data(items: List[Dict], details: List[Dict]) -> pd.DataFrame:
    details_map = {d["id"]: d for d in details}
    rows = []
    for item in items:
        vid_id = item.get("id", {})
        vid_id = vid_id.get("videoId", "") if isinstance(vid_id, dict) else str(vid_id)
        snippet = item.get("snippet", {})
        detail = details_map.get(vid_id, {})
        stats = detail.get("statistics", {})
        content = detail.get("contentDetails", {})
        recording = detail.get("recordingDetails", {})
        status_info = detail.get("status", {})
        topic_info = detail.get("topicDetails", {})
        try: duration_seconds = _parse_duration(content.get("duration", "PT0S"))
        except: duration_seconds = 0
        loc = recording.get("location", {})
        lat, lng = loc.get("latitude"), loc.get("longitude")
        tags = detail.get("snippet", snippet).get("tags", [])
        topic_cats = topic_info.get("topicCategories", [])
        published_str = snippet.get("publishedAt", "")
        try:
            published_dt = datetime.strptime(published_str[:19], "%Y-%m-%dT%H:%M:%S")
            age_days = (datetime.now() - published_dt).days
        except:
            published_dt = None; age_days = 0
        title = snippet.get("title", "Untitled")
        description = snippet.get("description", "")
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        is_default = detect_default_filename(title)
        title_ent = _compute_title_entropy(title)
        desc_len = len(description)
        all_caps = title.isupper() and len(title) > 3
        nums_only = bool(re.match(r'^[\d\s._-]+$', title.strip()))
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0]', title + description))
        vpd = round(views / max(age_days, 1), 4)
        weirdness = compute_weirdness_score(
            title=title, description=description, views=views, likes=likes,
            comments=comments, duration_seconds=duration_seconds, age_days=age_days,
            tags=tags, has_location=bool(lat and lng), title_entropy=title_ent,
            desc_length=desc_len, all_caps=all_caps, numbers_only=nums_only, views_per_day=vpd)
        rows.append({
            "video_id": vid_id, "title": title,
            "channel": snippet.get("channelTitle", "Unknown"),
            "channel_id": snippet.get("channelId", ""),
            "published": published_str, "published_date": published_dt,
            "upload_day": published_dt.strftime("%A") if published_dt else "",
            "upload_hour": published_dt.hour if published_dt else -1,
            "age_days": age_days, "description": description,
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "views": views, "likes": likes, "comments": comments,
            "favorites": int(stats.get("favoriteCount", 0)),
            "views_per_day": vpd,
            "like_ratio": round((likes / views * 100), 2) if views > 0 else 0.0,
            "comment_ratio": round((comments / views * 100), 2) if views > 0 else 0.0,
            "engagement_total": likes + comments,
            "duration_seconds": duration_seconds, "duration_fmt": _format_duration(duration_seconds),
            "latitude": lat, "longitude": lng, "has_geo": bool(lat and lng),
            "tags": tags, "tag_count": len(tags), "topic_categories": topic_cats,
            "is_default_filename": is_default, "title_entropy": title_ent,
            "title_length": len(title), "all_caps_title": all_caps,
            "numbers_only_title": nums_only, "has_emoji": has_emoji,
            "desc_length": desc_len, "desc_word_count": len(description.split()) if description else 0,
            "has_links_in_desc": bool(re.search(r'https?://', description)),
            "has_hashtags": bool(re.search(r'#\w+', description + title)),
            "definition": content.get("definition", ""),
            "caption": content.get("caption", "false"),
            "licensed_content": content.get("licensedContent", False),
            "privacy": status_info.get("privacyStatus", ""),
            "weirdness_score": weirdness,
            "url": f"https://www.youtube.com/watch?v={vid_id}",
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════
#  WEIRDNESS SCORING
# ═══════════════════════════════════════════════════════════════════════
def compute_weirdness_score(title, description, views, likes, comments,
                            duration_seconds, age_days, tags, has_location,
                            title_entropy=0, desc_length=0, all_caps=False,
                            numbers_only=False, views_per_day=0) -> float:
    score = 0.0
    # View-based (max 30)
    if views == 0: score += 30
    elif views <= 3: score += 27
    elif views <= 10: score += 22
    elif views <= 50: score += 15
    elif views <= 200: score += 10
    elif views <= 1000: score += 5
    # Temporal decay (max 18)
    if age_days > 5475 and views <= 10: score += 18
    elif age_days > 3650 and views <= 10: score += 15
    elif age_days > 1825 and views <= 10: score += 12
    elif age_days > 730 and views <= 10: score += 8
    elif age_days > 365 and views <= 5: score += 5
    # Title (max 18)
    if detect_default_filename(title): score += 10
    if numbers_only: score += 5
    if all_caps and len(title) > 5: score += 3
    if title_entropy < 2.0 and len(title) > 3: score += 3
    elif title_entropy > 4.5: score += 2
    # Description (max 8)
    if not description or desc_length < 5: score += 5
    elif desc_length < 20: score += 3
    if not tags: score += 3
    # Duration (max 6)
    if 0 < duration_seconds < 3: score += 4
    elif 0 < duration_seconds < 10: score += 3
    elif duration_seconds > 7200: score += 4
    elif duration_seconds > 3600: score += 3
    # Engagement ghost (max 10)
    if likes == 0 and comments == 0:
        if views <= 10: score += 10
        elif views <= 100: score += 5
    # Views per day (max 4)
    if age_days > 365 and views_per_day < 0.01: score += 4
    elif age_days > 365 and views_per_day < 0.05: score += 2
    # Geo (max 3)
    if has_location: score += 3
    # Keywords (max 4)
    combined = (title + " " + (description or "")).lower()
    weird_hits = sum(1 for kw in WEIRDNESS_BOOSTERS if kw in combined)
    score += min(4, weird_hits * 2)
    return min(100.0, max(0.0, round(score, 1)))


def _compute_title_entropy(title: str) -> float:
    if not title: return 0.0
    freq = Counter(title.lower())
    length = len(title)
    return round(-sum((c / length) * math.log2(c / length) for c in freq.values() if c > 0), 2)


def detect_default_filename(title: str) -> bool:
    for pat in DEFAULT_FILENAME_RE:
        if re.match(pat, title.strip(), re.IGNORECASE):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════
#  FILTERS
# ═══════════════════════════════════════════════════════════════════════
def filter_by_views(df, max_views=0):
    if df.empty: return df
    return df[df["views"] <= max_views].copy()

def filter_by_min_views(df, min_views=0):
    if df.empty: return df
    return df[df["views"] >= min_views].copy()

def filter_by_duration(df, min_secs=0, max_secs=999999):
    if df.empty: return df
    return df[(df["duration_seconds"] >= min_secs) & (df["duration_seconds"] <= max_secs)].copy()

def filter_default_filenames_only(df):
    if df.empty: return df
    return df[df["is_default_filename"] == True].copy()

def filter_by_weirdness(df, min_score=0):
    if df.empty: return df
    return df[df["weirdness_score"] >= min_score].copy()

def filter_has_geolocation(df):
    if df.empty: return df
    return df[df["has_geo"] == True].copy()

def filter_no_engagement(df):
    if df.empty: return df
    return df[(df["likes"] == 0) & (df["comments"] == 0)].copy()

def filter_by_age(df, min_days=0, max_days=999999):
    if df.empty: return df
    return df[(df["age_days"] >= min_days) & (df["age_days"] <= max_days)].copy()

def filter_no_description(df):
    if df.empty: return df
    return df[df["desc_length"] < 10].copy()

def filter_no_tags(df):
    if df.empty: return df
    return df[df["tag_count"] == 0].copy()

def filter_by_upload_hour(df, min_hour=0, max_hour=23):
    if df.empty: return df
    return df[(df["upload_hour"] >= min_hour) & (df["upload_hour"] <= max_hour)].copy()

def filter_short_title(df, max_len=15):
    if df.empty: return df
    return df[df["title_length"] <= max_len].copy()

def filter_all_caps(df):
    if df.empty: return df
    return df[df["all_caps_title"] == True].copy()

def filter_has_emoji(df):
    if df.empty: return df
    return df[df["has_emoji"] == True].copy()

def filter_sd_only(df):
    if df.empty: return df
    return df[df["definition"] == "sd"].copy()

def filter_no_links(df):
    if df.empty: return df
    return df[df["has_links_in_desc"] == False].copy()

def filter_title_contains(df, substring: str):
    if df.empty or not substring: return df
    return df[df["title"].str.contains(substring, case=False, na=False)].copy()

def filter_title_regex(df, pattern: str):
    if df.empty or not pattern: return df
    try:
        return df[df["title"].str.contains(pattern, case=False, na=False, regex=True)].copy()
    except: return df

def filter_description_contains(df, substring: str):
    if df.empty or not substring: return df
    return df[df["description"].str.contains(substring, case=False, na=False)].copy()

def filter_channel_contains(df, substring: str):
    if df.empty or not substring: return df
    return df[df["channel"].str.contains(substring, case=False, na=False)].copy()

def filter_by_views_per_day(df, max_vpd: float = 1.0):
    if df.empty: return df
    return df[df["views_per_day"] <= max_vpd].copy()

def filter_exclude_licensed(df):
    if df.empty: return df
    return df[df["licensed_content"] == False].copy()


# ═══════════════════════════════════════════════════════════════════════
#  RABBIT HOLE & CHAOS
# ═══════════════════════════════════════════════════════════════════════
def generate_rabbit_hole_queries(tags, title="", channel="", description="", max_queries=10):
    queries = []
    if tags:
        for i in range(0, min(len(tags) - 1, 5)):
            queries.append(f"{tags[i]} {tags[i + 1]}")
    if tags:
        queries.append(f"IMG_ {tags[0]}")
        if len(tags) > 2: queries.append(f"VID_ {tags[2]}")
        if len(tags) > 4: queries.append(f"DSC_ {tags[4]}")
    all_text = f"{title} {description}"
    locs = re.findall(r'\b[A-Z][a-z]{3,}\b', all_text)
    if len(locs) >= 2: queries.append(f"{locs[0]} {locs[1]}")
    if locs: queries.append(f"IMG_ {locs[0]}")
    if channel and channel != "Unknown": queries.append(f'"{channel}"')
    ym = re.search(r'(20[0-2]\d)', all_text)
    if ym and tags: queries.append(f"{ym.group(1)} {tags[0]}")
    if tags: queries.append(f"{random.choice(WEIRDNESS_BOOSTERS[:15])} {tags[0]}")
    if description:
        stops = {'the','and','is','in','to','of','a','for','on','it','this','that','with','from'}
        words = re.findall(r'\b\w{4,}\b', description.lower())
        top = [w for w, _ in Counter(w for w in words if w not in stops).most_common(3)]
        if len(top) >= 2: queries.append(f"{top[0]} {top[1]}")
    seen = set()
    unique = []
    for q in queries:
        ql = q.strip().lower()
        if ql not in seen:
            seen.add(ql)
            unique.append(q.strip())
    return unique[:max_queries]


def generate_time_travel_query():
    days_back = random.randint(365, 7000)
    center = datetime.now() - timedelta(days=days_back)
    return random.choice(list(FILENAME_PATTERNS.values())), center - timedelta(days=5), center + timedelta(days=5)


def generate_chaos_queries(count=5):
    strategies = [
        lambda: f"{random.choice(['IMG_','DSC_','VID_','MOV_','MVI_','GOPR','DJI_'])}{random.randint(1000,9999)}",
        lambda: f"{random.randint(2005,2023)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        lambda: f"{random.choice(WEIRDNESS_BOOSTERS)} {random.choice(WEIRDNESS_BOOSTERS)}",
        lambda: hashlib.md5(str(random.random()).encode()).hexdigest()[:8],
        lambda: f"{random.choice(['iphone','samsung','nokia','motorola','lg'])} video {random.randint(2006,2015)}",
    ]
    return [random.choice(strategies)() for _ in range(count)]


def _format_duration(seconds):
    if seconds == 0: return "N/A"
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
