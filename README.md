# ⌬ OBSCURITY ENGINE & ARCHIVAL SUITE v2.0

**Deep-Web Media Discovery & Preservation Dashboard**

A professional-grade, locally-hosted web application for discovering obscure, zero-view, and forgotten media across YouTube and the Internet Archive — then preserving it locally before it disappears.

---

## Quick Start

```bash
# 1. Clone / copy the project
cd obscurity-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
streamlit run app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

---

## First-Time Setup

1. **Navigate to ⚙️ Setup** in the sidebar
2. **YouTube API Key** (required for search):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project → Enable **YouTube Data API v3**
   - Create an API Key under Credentials
   - Paste it into the Setup page — it's saved to `.env` locally
3. **OAuth 2.0** (optional, for user-specific features):
   - Create an OAuth 2.0 Client ID (Desktop app type)
   - Download the `client_secrets.json` and upload it in Setup
   - Add `http://localhost:8090/` as an authorized redirect URI
4. **Internet Archive** (optional):
   - Enter your archive.org email/password if you need access to restricted items

---

## Features

### 🔍 Dual-Engine Search
- **YouTube API**: Search with advanced filters for zero-view videos, camera filename patterns (IMG_, DSC_, MOV_, etc.), date ranges, and view count thresholds
- **Internet Archive**: Simultaneously search archive.org for deleted/legacy content
- Deduplicated results with full statistics (views, likes, duration, tags)
- Export results as CSV

### 🗺️ Geo-Hunter
- Map-based search using Folium with dark CartoDB tiles
- Set coordinates + radius to find videos uploaded from specific locations
- Color-coded markers by view count (green = 0 views, cyan = <100, etc.)
- Interactive popups with video details and direct links

### 🐇 Rabbit Hole Mode
- Auto-generates related search queries from a video's tags
- Hardcoded 10,000 view ceiling — stays in the obscure zone
- Chain multiple queries for deep exploration
- Manual tag input for custom deep dives

### 📦 The Vault
- Integrated `yt-dlp` downloader with quality presets (best, 720p, audio-only)
- One-click **Preserve** button on every search result
- Downloads video + metadata + thumbnail + subtitles
- Internet Archive item downloading
- Full vault index with metadata viewer
- Manual URL download support

### ⚙️ Setup Wizard
- Secure credential storage in `.env` (never hardcoded)
- OAuth 2.0 flow with automatic token refresh
- Visual status indicators for all configured services

---

## Project Structure

```
obscurity-engine/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env                      # Auto-generated credentials (gitignored)
├── .streamlit/
│   └── config.toml           # Streamlit theme config
├── static/
│   └── style.css             # Cyberpunk CSS theme
├── modules/
│   ├── __init__.py
│   ├── secrets_manager.py    # Credential & OAuth management
│   ├── youtube_engine.py     # YouTube API search engine
│   ├── archive_engine.py     # Internet Archive search
│   ├── geo_hunter.py         # Folium map generation
│   └── vault.py              # yt-dlp integration & local archival
├── vault/                    # Downloaded media (auto-created)
│   ├── youtube/
│   ├── archive_org/
│   └── metadata/
└── .secrets/                 # OAuth tokens (auto-created, gitignored)
```

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | Streamlit |
| YouTube API | google-api-python-client + google-auth-oauthlib |
| Archive Search | Internet Archive Advanced Search API |
| Downloader | yt-dlp (subprocess) |
| Maps | Folium + streamlit-folium |
| Data | Pandas |
| Theme | Custom CSS (Cyberpunk dark) |

---

## API Quota Notes

- YouTube Data API v3 has a default quota of **10,000 units/day**
- Each `search.list` call costs **100 units**
- Each `videos.list` call costs **1 unit per video**
- A typical search session (3 queries + details) ≈ **325 units**
- That's roughly **30 search sessions per day** on the free tier

---

## Security

- API keys stored in local `.env` file only
- OAuth tokens stored in `.secrets/` directory
- Both directories are auto-gitignored
- No credentials are ever logged or transmitted to third parties
- All processing happens locally on your machine

---

## License

For personal/research use. Respect YouTube's Terms of Service and the Internet Archive's usage policies when using this tool.
