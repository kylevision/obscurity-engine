# ⌬ OBSCURITY ENGINE v2.0
**Deep-Web Media Discovery & Preservation Dashboard**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30-FF4B4B.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)

A professional-grade, locally-hosted dashboard for discovering "Zero-View" content, obscure media, and lost footage across YouTube and the Internet Archive. Includes a built-in Vault for preserving content locally before it disappears.

---

## ⚡ Quick Start (Docker - Recommended)
The easiest way to run the engine without installing Python or FFmpeg manually.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/kylevision/obscurity-engine.git](https://github.com/kylevision/obscurity-engine.git)
    cd obscurity-engine
    ```

2.  **Run with Docker Compose:**
    ```bash
    docker compose up -d --build
    ```

3.  **Access the Dashboard:**
    Open `http://localhost:8501` in your browser.

---

## 🛠 Manual Installation
If you prefer to run it directly on your machine (Windows/Mac/Linux):

1.  **Prerequisites:**
    * Python 3.10+ installed.
    * **FFmpeg** installed and added to your system PATH (Required for video processing).

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

---

## 🔑 Configuration & API Keys
To use the search features, you must provide your own API keys. **Your keys are stored locally on your machine in a `.env` file and are never sent to us.**

### 1. YouTube Data API (Required for Search)
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project (e.g., "Obscurity Engine").
3.  Search for and enable the **YouTube Data API v3**.
4.  Go to **Credentials** → **Create Credentials** → **API Key**.
5.  Copy the key (starts with `AIza...`).
6.  Open the app, go to **⚙️ Setup** in the sidebar, and paste the key.

### 2. OAuth 2.0 (Optional)
Required only if you want to use "Rabbit Hole" modes that require user context.
1.  In Google Cloud Console, create an **OAuth 2.0 Client ID** (Desktop App).
2.  Download the `client_secrets.json`.
3.  Upload it in the **⚙️ Setup** tab.

---

## 📦 Features

* **🔍 Dual-Engine Search:** Simultaneously scan YouTube (with zero-view filters) and Archive.org.
* **🗺️ Geo-Hunter:** Find raw video uploads from specific GPS coordinates and radiuses.
* **🐇 Rabbit Hole Mode:** Generate related search queries automatically to dig deeper into niche topics.
* **💾 The Vault:** One-click preservation. Downloads video, metadata, thumbnail, and subtitles to your local drive.
* **🚫 Privacy Focused:** No tracking. All data lives on your hardware.

---
### 💾 The Vault (Archival)
*Note: To ensure compliance with platform Terms of Service, the direct download functionality ('Preserve' button) is disabled by default in this repository.*

* **Developer Note:** The `modules/vault.py` logic remains intact for educational purposes. Users with legal authorization to archive content can re-enable the UI buttons in `app.py` and install `yt-dlp` to restore full functionality.

## ⚠️ Disclaimer

This tool is for educational and archival purposes only. Please respect the Terms of Service of all platforms and the copyright of content creators.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kylevision)



