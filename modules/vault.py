"""
Vault Module
Handles downloading and preserving media content using yt-dlp.
Manages the local vault directory structure and metadata.
"""

import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "vault"
VAULT_META_FILE = VAULT_DIR / "_vault_index.json"


def ensure_vault():
    """Create vault directory structure."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    (VAULT_DIR / "youtube").mkdir(exist_ok=True)
    (VAULT_DIR / "archive_org").mkdir(exist_ok=True)
    (VAULT_DIR / "metadata").mkdir(exist_ok=True)
    if not VAULT_META_FILE.exists():
        VAULT_META_FILE.write_text(json.dumps({"items": []}, indent=2))


def get_vault_index() -> Dict[str, Any]:
    """Load the vault index."""
    ensure_vault()
    try:
        return json.loads(VAULT_META_FILE.read_text())
    except Exception:
        return {"items": []}


def save_vault_index(index: Dict[str, Any]):
    """Save the vault index."""
    ensure_vault()
    VAULT_META_FILE.write_text(json.dumps(index, indent=2))


def add_to_vault_index(entry: Dict[str, Any]):
    """Add an entry to the vault index."""
    index = get_vault_index()
    # Deduplicate
    existing_ids = {item.get("id") for item in index["items"]}
    if entry.get("id") not in existing_ids:
        entry["archived_at"] = datetime.now().isoformat()
        index["items"].append(entry)
        save_vault_index(index)


def download_youtube_video(
    url: str,
    video_id: str,
    title: str = "",
    quality: str = "best",
    metadata: Optional[Dict] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Download a YouTube video using yt-dlp.

    Returns:
        Dict with 'success', 'filepath', 'error' keys.
    """
    ensure_vault()
    output_dir = VAULT_DIR / "youtube" / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build yt-dlp command
    output_template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--write-info-json",
        "--write-thumbnail",
        "--write-description",
        "--write-subs",
        "--sub-langs", "all",
        "--embed-subs",
        "--embed-thumbnail",
        "--embed-metadata",
        "-o", output_template,
        "--progress",
        "--newline",
    ]

    # Quality presets
    if quality == "best":
        cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])
    elif quality == "720p":
        cmd.extend(["-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"])
    elif quality == "audio_only":
        cmd.extend(["-x", "--audio-format", "mp3"])
    else:
        cmd.extend(["-f", "best"])

    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=str(output_dir),
        )

        if result.returncode == 0:
            # Save additional metadata
            if metadata:
                meta_file = output_dir / "custom_metadata.json"
                meta_file.write_text(json.dumps(metadata, indent=2, default=str))

            # Find the downloaded file
            media_files = list(output_dir.glob("*.mp4")) + list(output_dir.glob("*.mkv")) + \
                          list(output_dir.glob("*.webm")) + list(output_dir.glob("*.mp3"))

            filepath = str(media_files[0]) if media_files else str(output_dir)

            # Add to vault index
            add_to_vault_index({
                "id": video_id,
                "source": "youtube",
                "title": title or video_id,
                "url": url,
                "filepath": filepath,
                "directory": str(output_dir),
                "metadata": metadata,
            })

            return {"success": True, "filepath": filepath, "directory": str(output_dir)}
        else:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
            return {"success": False, "error": error_msg}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Download timed out (10 min limit)"}
    except FileNotFoundError:
        return {"success": False, "error": "yt-dlp not found. Install with: pip install yt-dlp"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_archive_item(
    identifier: str,
    file_url: str,
    filename: str,
    metadata: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Download a file from Internet Archive.
    """
    ensure_vault()
    import requests

    output_dir = VAULT_DIR / "archive_org" / identifier
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    try:
        response = requests.get(file_url, stream=True, timeout=300)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Save metadata
        if metadata:
            meta_file = output_dir / "metadata.json"
            meta_file.write_text(json.dumps(metadata, indent=2, default=str))

        add_to_vault_index({
            "id": identifier,
            "source": "archive_org",
            "title": metadata.get("title", identifier) if metadata else identifier,
            "url": file_url,
            "filepath": str(filepath),
            "directory": str(output_dir),
            "metadata": metadata,
        })

        return {"success": True, "filepath": str(filepath)}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_vault_stats() -> Dict[str, Any]:
    """Get statistics about the vault."""
    ensure_vault()
    index = get_vault_index()
    items = index.get("items", [])

    total_size = 0
    for item in items:
        dirpath = item.get("directory", "")
        if dirpath and Path(dirpath).exists():
            for f in Path(dirpath).rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

    return {
        "total_items": len(items),
        "youtube_items": len([i for i in items if i.get("source") == "youtube"]),
        "archive_items": len([i for i in items if i.get("source") == "archive_org"]),
        "total_size_bytes": total_size,
        "total_size_human": _human_size(total_size),
        "vault_path": str(VAULT_DIR),
    }


def is_in_vault(item_id: str) -> bool:
    """Check if an item is already in the vault."""
    index = get_vault_index()
    return any(item.get("id") == item_id for item in index.get("items", []))


def _human_size(num_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"
