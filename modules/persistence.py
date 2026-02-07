"""
Session Persistence Module
Saves search history, favorites, leaderboard, and results to disk.
Survives app restarts.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "search_history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"
LAST_RESULTS_FILE = DATA_DIR / "last_results.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default=None):
    if default is None:
        default = []
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
    return default


def _save_json(path: Path, data):
    ensure_data_dir()
    try:
        path.write_text(json.dumps(data, indent=2, default=str))
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  SEARCH HISTORY
# ═══════════════════════════════════════════════════════════════════════
def save_search_session(queries: List[str], result_count: int, source: str = "youtube", filters: Dict = None):
    """Save a search session to history."""
    history = load_search_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "queries": queries,
        "result_count": result_count,
        "source": source,
        "filters": filters or {},
    })
    # Keep last 500 sessions
    history = history[-500:]
    _save_json(HISTORY_FILE, history)


def load_search_history() -> List[Dict]:
    return _load_json(HISTORY_FILE, [])


def clear_search_history():
    _save_json(HISTORY_FILE, [])


# ═══════════════════════════════════════════════════════════════════════
#  FAVORITES
# ═══════════════════════════════════════════════════════════════════════
def add_favorite(video_data: Dict):
    """Add a video to favorites."""
    favs = load_favorites()
    # Deduplicate
    existing_ids = {f.get("video_id") for f in favs}
    vid_id = video_data.get("video_id", "")
    if vid_id and vid_id not in existing_ids:
        entry = {
            "video_id": vid_id,
            "title": video_data.get("title", "Untitled"),
            "channel": video_data.get("channel", "Unknown"),
            "views": int(video_data.get("views", 0)),
            "weirdness_score": float(video_data.get("weirdness_score", 0)),
            "url": video_data.get("url", ""),
            "thumbnail": video_data.get("thumbnail", ""),
            "duration_fmt": video_data.get("duration_fmt", ""),
            "age_days": int(video_data.get("age_days", 0)),
            "added_at": datetime.now().isoformat(),
            "tags": video_data.get("tags", []),
            "description": str(video_data.get("description", ""))[:200],
        }
        favs.append(entry)
        _save_json(FAVORITES_FILE, favs)
        return True
    return False


def remove_favorite(video_id: str):
    favs = load_favorites()
    favs = [f for f in favs if f.get("video_id") != video_id]
    _save_json(FAVORITES_FILE, favs)


def is_favorite(video_id: str) -> bool:
    favs = load_favorites()
    return any(f.get("video_id") == video_id for f in favs)


def load_favorites() -> List[Dict]:
    return _load_json(FAVORITES_FILE, [])


def favorites_to_df() -> pd.DataFrame:
    favs = load_favorites()
    if not favs:
        return pd.DataFrame()
    return pd.DataFrame(favs)


# ═══════════════════════════════════════════════════════════════════════
#  LEADERBOARD — Track weirdest finds across all sessions
# ═══════════════════════════════════════════════════════════════════════
def update_leaderboard(df: pd.DataFrame, max_entries: int = 100):
    """Merge new results into the all-time leaderboard."""
    if df.empty:
        return
    board = load_leaderboard()
    existing_ids = {e.get("video_id") for e in board}

    for _, row in df.iterrows():
        vid_id = row.get("video_id", "")
        if vid_id and vid_id not in existing_ids:
            board.append({
                "video_id": vid_id,
                "title": str(row.get("title", "Untitled")),
                "channel": str(row.get("channel", "Unknown")),
                "views": int(row.get("views", 0)),
                "weirdness_score": float(row.get("weirdness_score", 0)),
                "url": str(row.get("url", "")),
                "thumbnail": str(row.get("thumbnail", "")),
                "duration_fmt": str(row.get("duration_fmt", "")),
                "age_days": int(row.get("age_days", 0)),
                "found_at": datetime.now().isoformat(),
                "is_default_filename": bool(row.get("is_default_filename", False)),
                "has_geo": bool(row.get("has_geo", False)),
            })
            existing_ids.add(vid_id)

    # Sort by weirdness, keep top N
    board.sort(key=lambda x: x.get("weirdness_score", 0), reverse=True)
    board = board[:max_entries]
    _save_json(LEADERBOARD_FILE, board)


def load_leaderboard() -> List[Dict]:
    return _load_json(LEADERBOARD_FILE, [])


def leaderboard_to_df() -> pd.DataFrame:
    board = load_leaderboard()
    if not board:
        return pd.DataFrame()
    return pd.DataFrame(board)


def clear_leaderboard():
    _save_json(LEADERBOARD_FILE, [])


# ═══════════════════════════════════════════════════════════════════════
#  LAST RESULTS CACHE
# ═══════════════════════════════════════════════════════════════════════
def save_last_results(df: pd.DataFrame):
    """Cache the last search results so they survive reruns."""
    if df.empty:
        return
    ensure_data_dir()
    try:
        # Convert to serializable format
        records = []
        for _, row in df.iterrows():
            rec = {}
            for col in df.columns:
                val = row[col]
                if isinstance(val, (datetime, pd.Timestamp)):
                    rec[col] = str(val)
                elif isinstance(val, float) and pd.isna(val):
                    rec[col] = None
                elif isinstance(val, list):
                    rec[col] = val
                else:
                    rec[col] = val
                    try:
                        json.dumps(val)
                    except (TypeError, ValueError):
                        rec[col] = str(val)
            records.append(rec)
        _save_json(LAST_RESULTS_FILE, records)
    except Exception as e:
        logger.warning(f"Failed to cache results: {e}")


def load_last_results() -> pd.DataFrame:
    """Load cached results from disk."""
    records = _load_json(LAST_RESULTS_FILE, [])
    if not records:
        return pd.DataFrame()
    try:
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════════════════
def get_session_stats() -> Dict[str, Any]:
    """Overall stats across all sessions."""
    history = load_search_history()
    board = load_leaderboard()
    favs = load_favorites()
    return {
        "total_sessions": len(history),
        "total_queries": sum(len(s.get("queries", [])) for s in history),
        "total_results_found": sum(s.get("result_count", 0) for s in history),
        "leaderboard_entries": len(board),
        "favorites_count": len(favs),
        "top_weirdness": board[0]["weirdness_score"] if board else 0,
    }
