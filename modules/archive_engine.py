"""
Internet Archive Search Engine Module
Search archive.org for deleted, legacy, or obscure media content.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import requests
import pandas as pd

logger = logging.getLogger(__name__)

IA_SEARCH_URL = "https://archive.org/advancedsearch.php"
IA_METADATA_URL = "https://archive.org/metadata"
IA_DETAILS_URL = "https://archive.org/details"
IA_DOWNLOAD_URL = "https://archive.org/download"


def search_archive(
    query: str,
    media_type: str = "movies",
    max_results: int = 25,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    sort: str = "date desc",
    page: int = 1,
) -> Dict[str, Any]:
    """
    Search Internet Archive using the advanced search API.

    Args:
        query: Search query string
        media_type: Type filter (movies, audio, texts, image, etc.)
        max_results: Number of results per page
        date_start: Filter start date (YYYY-MM-DD)
        date_end: Filter end date (YYYY-MM-DD)
        sort: Sort order
        page: Page number

    Returns:
        Dict with 'items', 'total', 'page'
    """
    try:
        # Build the query with filters
        q_parts = [query]
        if media_type:
            q_parts.append(f"mediatype:{media_type}")
        if date_start:
            q_parts.append(f"date:[{date_start} TO {date_end or '*'}]")
        elif date_end:
            q_parts.append(f"date:[* TO {date_end}]")

        full_query = " AND ".join(q_parts)

        params = {
            "q": full_query,
            "fl[]": [
                "identifier",
                "title",
                "mediatype",
                "date",
                "description",
                "creator",
                "downloads",
                "collection",
                "subject",
                "source",
            ],
            "sort[]": sort,
            "rows": max_results,
            "page": page,
            "output": "json",
        }

        response = requests.get(IA_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get("response", {})
        docs = results.get("docs", [])
        total = results.get("numFound", 0)

        items = []
        for doc in docs:
            identifier = doc.get("identifier", "")
            items.append(
                {
                    "identifier": identifier,
                    "title": doc.get("title", "Untitled"),
                    "mediatype": doc.get("mediatype", "unknown"),
                    "date": doc.get("date", ""),
                    "description": _truncate(doc.get("description", ""), 300),
                    "creator": doc.get("creator", "Unknown"),
                    "downloads": doc.get("downloads", 0),
                    "collection": doc.get("collection", []),
                    "subject": doc.get("subject", []),
                    "url": f"{IA_DETAILS_URL}/{identifier}",
                    "thumbnail": f"https://archive.org/services/img/{identifier}",
                    "download_url": f"{IA_DOWNLOAD_URL}/{identifier}",
                }
            )

        return {"items": items, "total": total, "page": page}

    except Exception as e:
        logger.error(f"Internet Archive search failed: {e}")
        return {"items": [], "total": 0, "page": page, "error": str(e)}


def get_item_metadata(identifier: str) -> Optional[Dict[str, Any]]:
    """Fetch full metadata for an Internet Archive item."""
    try:
        response = requests.get(f"{IA_METADATA_URL}/{identifier}", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get IA metadata for {identifier}: {e}")
        return None


def get_item_files(identifier: str) -> List[Dict[str, str]]:
    """Get downloadable files for an Internet Archive item."""
    metadata = get_item_metadata(identifier)
    if not metadata:
        return []

    files = []
    for f in metadata.get("files", []):
        name = f.get("name", "")
        # Filter for media files
        if any(
            name.lower().endswith(ext)
            for ext in [".mp4", ".webm", ".avi", ".mkv", ".mp3", ".ogg", ".flac", ".pdf", ".jpg", ".png"]
        ):
            files.append(
                {
                    "name": name,
                    "size": f.get("size", "0"),
                    "format": f.get("format", "unknown"),
                    "url": f"{IA_DOWNLOAD_URL}/{identifier}/{name}",
                }
            )

    return files


def parse_archive_results(items: List[Dict]) -> pd.DataFrame:
    """Convert archive search results to a DataFrame."""
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    # Clean up date field
    if "date" in df.columns:
        df["date"] = df["date"].apply(_parse_ia_date)

    # Convert downloads to int
    if "downloads" in df.columns:
        df["downloads"] = pd.to_numeric(df["downloads"], errors="coerce").fillna(0).astype(int)

    return df


def search_wayback_availability(url: str) -> Optional[Dict[str, Any]]:
    """Check if a URL has been archived in the Wayback Machine."""
    try:
        response = requests.get(
            "https://archive.org/wayback/available",
            params={"url": url},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        snapshot = data.get("archived_snapshots", {}).get("closest")
        return snapshot
    except Exception as e:
        logger.error(f"Wayback availability check failed: {e}")
        return None


def _parse_ia_date(date_str) -> str:
    """Parse various IA date formats into a consistent string."""
    if not date_str or pd.isna(date_str):
        return ""
    try:
        if isinstance(date_str, str):
            for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y"]:
                try:
                    return datetime.strptime(date_str[:len(fmt.replace("%", "0"))], fmt).strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    continue
        return str(date_str)[:10]
    except Exception:
        return str(date_str)[:10]


def _truncate(text: str, max_len: int = 300) -> str:
    """Truncate text to max length."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
