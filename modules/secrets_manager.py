"""
Secrets Manager Module
Handles OAuth 2.0 flow, API key storage, and credential management.
Stores secrets in .env file with optional keyring integration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
SECRETS_DIR = BASE_DIR / ".secrets"
ENV_FILE = BASE_DIR / ".env"
TOKEN_FILE = SECRETS_DIR / "youtube_token.json"
CLIENT_SECRETS_FILE = SECRETS_DIR / "client_secrets.json"

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def ensure_secrets_dir():
    """Create .secrets directory if it doesn't exist."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    gitignore = SECRETS_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")


def load_env() -> Dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
                os.environ[key.strip()] = env_vars[key.strip()]
    return env_vars


def save_env(key: str, value: str):
    """Save or update a key-value pair in .env file."""
    env_vars = load_env()
    env_vars[key] = value
    lines = [f'{k}="{v}"' for k, v in env_vars.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n")
    os.environ[key] = value


def get_api_key() -> Optional[str]:
    """Get the current YouTube API key (first working one from pool)."""
    load_env()
    # Try single key first
    single = os.environ.get("YOUTUBE_API_KEY")
    keys = get_all_api_keys()
    if keys:
        # Rotate: use the key at current index
        idx = int(os.environ.get("_YT_KEY_IDX", "0")) % len(keys)
        return keys[idx]
    return single


def get_all_api_keys() -> List[str]:
    """Get all configured API keys."""
    load_env()
    keys = []
    # Check YOUTUBE_API_KEY (single)
    single = os.environ.get("YOUTUBE_API_KEY", "")
    if single:
        keys.append(single)
    # Check YOUTUBE_API_KEY_2, _3, etc.
    for i in range(2, 21):
        k = os.environ.get(f"YOUTUBE_API_KEY_{i}", "")
        if k:
            keys.append(k)
    # Deduplicate preserving order
    seen = set()
    unique = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique


def rotate_api_key():
    """Advance to the next API key in the pool."""
    keys = get_all_api_keys()
    if len(keys) <= 1:
        return
    idx = int(os.environ.get("_YT_KEY_IDX", "0"))
    os.environ["_YT_KEY_IDX"] = str((idx + 1) % len(keys))


def save_api_key(api_key: str):
    """Save YouTube API key."""
    ensure_secrets_dir()
    save_env("YOUTUBE_API_KEY", api_key)


def save_additional_api_key(api_key: str, slot: int):
    """Save an additional API key to a numbered slot (2-20)."""
    ensure_secrets_dir()
    save_env(f"YOUTUBE_API_KEY_{slot}", api_key)


def has_client_secrets() -> bool:
    """Check if OAuth client secrets file exists."""
    return CLIENT_SECRETS_FILE.exists()


def save_client_secrets(client_json: str):
    """Save OAuth client secrets JSON."""
    ensure_secrets_dir()
    parsed = json.loads(client_json)
    CLIENT_SECRETS_FILE.write_text(json.dumps(parsed, indent=2))


def get_youtube_oauth_credentials():
    """
    Get authenticated YouTube OAuth credentials.
    Returns a google.oauth2.credentials.Credentials object or None.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        creds = None

        # Load existing token
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), YOUTUBE_SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
                creds = None

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json())
                return creds
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                creds = None

        if creds and creds.valid:
            return creds

        # Need new auth flow
        if not has_client_secrets():
            return None

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE), YOUTUBE_SCOPES
        )
        creds = flow.run_local_server(port=8090, prompt="consent")
        TOKEN_FILE.write_text(creds.to_json())
        return creds

    except ImportError:
        logger.error("google-auth-oauthlib not installed")
        return None
    except Exception as e:
        logger.error(f"OAuth flow failed: {e}")
        return None


def get_youtube_service(use_oauth: bool = False):
    """
    Build and return a YouTube API service object.
    Supports multi-key rotation. Returns None if no keys configured.
    """
    try:
        from googleapiclient.discovery import build

        if use_oauth:
            creds = get_youtube_oauth_credentials()
            if creds:
                return build("youtube", "v3", credentials=creds)

        api_key = get_api_key()
        if api_key:
            return build("youtube", "v3", developerKey=api_key)

        return None
    except Exception as e:
        logger.error(f"Failed to build YouTube service: {e}")
        # If quota error, try rotating
        if "quota" in str(e).lower() or "403" in str(e):
            rotate_api_key()
            logger.info("Rotated to next API key")
        return None


def get_credential_status() -> Dict[str, Any]:
    """Return status of all credentials."""
    load_env()
    keys = get_all_api_keys()
    return {
        "api_key_set": len(keys) > 0,
        "api_key_count": len(keys),
        "oauth_client_configured": has_client_secrets(),
        "oauth_token_exists": TOKEN_FILE.exists(),
        "vault_dir": str(BASE_DIR / "vault"),
    }


def get_archive_credentials() -> Optional[Dict[str, str]]:
    """Get Internet Archive credentials if configured."""
    load_env()
    email = os.environ.get("IA_EMAIL")
    password = os.environ.get("IA_PASSWORD")
    if email and password:
        return {"email": email, "password": password}
    return None


def save_archive_credentials(email: str, password: str):
    """Save Internet Archive credentials."""
    save_env("IA_EMAIL", email)
    save_env("IA_PASSWORD", password)
