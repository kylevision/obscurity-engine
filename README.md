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

## ⚠️ Disclaimer
This tool is for educational and archival purposes only. Please respect the Terms of Service of all platforms and the copyright of content creators.

---
##  The Vault & Compliance
Note on Downloading: To comply with Terms of Service and GitHub policies, the Direct Download ("DL") buttons are disabled by default in this repository.

The Code: The archival logic resides in modules/vault.py.

For Researchers/Archivists: The functionality can be restored for legal archiving purposes by:

Uncommenting yt-dlp in requirements.txt.

Uncommenting the download button logic in app.py.

Use at your own risk.

##  Disclaimer
This tool is for educational and research purposes only.

Do not use this tool to infringe on copyright.

Do not use this tool to harass users found via Geo-Hunt.

Respect YouTube's API quotas and Terms of Service.

License: MIT License. Free to fork, modify, and distribute.

## License

For personal/research use. Respect YouTube's Terms of Service and the Internet Archive's usage policies when using this tool.


[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/YOUR_USERNAME)




