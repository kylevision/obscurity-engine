Obscurity Engine v7.0
The "Final Form" Deep-Web Media Discovery Dashboard

Mission: To illuminate the invisible. The Obscurity Engine is a reverse-search tool designed to find content that YouTube's algorithm actively hides: zero-view videos, raw uploads, forgotten history, and "glitch" content.

⚡ Quick Start
Option 1: Docker (Recommended)
The cleanest way to run the engine without dependency conflicts.

Clone the repository git clone https://github.com/YOUR_USERNAME/obscurity-engine.git cd obscurity-engine

Start the engine docker compose up -d --build

Access the dashboard Open your browser to http://localhost:8501

Option 2: Manual Install (Python 3.10+)
pip install -r requirements.txt

streamlit run app.py

🖥️ The Interface: Decoded
The interface uses "Cyberpunk/Terminal" shorthand to save space. Here is the translation guide for the main controls.

1. Main Search Bar
SYS>: The Command Line. Type your search query here.

EXEC: "Execute". Runs the search.

RAND: "Random". Generates a "Time Travel" query (a random filename from a random week in history).

CHAOS: Injects 5 completely random, system-breaking queries to clear the algorithm's cache.

2. Search Engines (Toggles)
API: Uses the official YouTube Data API. Fast, accurate, supports deep filtering. Requires API Key.

SCRAPE: Uses yt-dlp to scrape results. Slower, but unlimited. No Key Required.

ARCH: Searches the Internet Archive (Wayback Machine) simultaneously.

3. Control Panel (Hidden Filters)
Click "CONTROL PANEL" to expand the advanced filters.

Tab: FILT (Filters)

MIN_V: Minimum Views.

ZERO: Forces results to have exactly 0 Views.

PER_Q: "Per Query". The quantity slider. Controls how many results to fetch (Default: 50).

GHOST: Finds "True Voids" — videos with 0 Likes and 0 Comments.

DEF: Restricts results to Default Filenames only (e.g., IMG_1234, DSCN001).

Tab: PAT (Patterns)

Select specific camera naming conventions (e.g., Canon DSLRs IMG_, GoPro GOPR, Drones DJI_).

🛠️ The Modes: A Deep Dive
Select these modes from the sidebar menu.

🗺️ GEO-HUNT (The Stalker)
Finds videos based on where they were uploaded, ignoring title relevance.

What it is: A tool to find raw, unedited footage from specific coordinates.

How to use:

Select PICK A LOCATION (e.g., "Chernobyl") or click the map.

Set RADIUS (e.g., 10km).

Click SCAN LOCATION.

Use Case: Digital tourism, investigating local events, or finding "slice of life" videos from remote towns.

🐇 RABBIT HOLE (The Digger)
A recursive query generator.

What it is: If you find one weird video, this tool helps you find the rest of the cluster.

How to use:

Enter TAGS (comma-separated) or let the engine populate them from previous results.

Click GEN to create 10 new, specific search queries based on those tags.

Click EXEC ALL to run all 10 searches at once.

🕵️ CHANNEL AUTOPSY (The Forensic)
Analyzes a channel for bot-like behavior.

How to use: Paste a Channel ID (UC...) and click AUTOPSY.

Metrics:

Bot Fingerprint: Checks if uploads happen at mathematically perfect intervals (e.g., exactly every 4 hours).

Burst Detection: Finds days where the channel uploaded impossible amounts of video (e.g., 50 videos in 1 hour).

Obscurity Score: Rates the channel's "weirdness" from 0-100.

🕸️ CRAWL (The Spider)
Automates the "Related Video" chain.

What it is: Mimics a user clicking "Next Video" repeatedly for hours.

Inputs:

SEED: Starting Video ID.

DEPTH: How many "hops" away from the start to go.

PER_HOP: How many branches to take at each step.

Use Case: Finding content that is algorithmically adjacent to your topic but not searchable via keywords.

📺 ROULETTE (The Gambler)
NEXT: Picks a random video ID from the database or generates a "Smart Seed" ID.

QUEUE 10: Generates a playlist of 10 random candidates.

Note: True random YouTube IDs are rarely valid. This module uses heuristic guessing to find valid IDs.

💀 BRUTE FORCE (The Lockpicker)
RANDOM: Guesses 11-character strings. (Success rate: Low).

NEAR: Takes a known valid ID and guesses the IDs immediately next to it (e.g., ID+1, ID-1).

Why? YouTube IDs are not sequential, but they often cluster in time. This is the best way to find Unlisted or Deleted videos that were uploaded at the same second as a popular video.

WAYBACK: Checks if the videos in your current results have been saved to the Internet Archive.

⏳ CAPSULE (The Historian)
What it is: Restricts the entire engine to a single 24-hour period in history.

How to use: Pick a DATE (e.g., June 15, 2009) and click OPEN CAPSULE.

Result: See exactly what the world uploaded on that specific day, unfiltered by modern popularity.

🔒 The Vault & Compliance
Note on Downloading: To comply with Terms of Service and GitHub policies, the Direct Download ("DL") buttons are disabled by default in this repository.

The Code: The archival logic resides in modules/vault.py.

For Researchers/Archivists: The functionality can be restored for legal archiving purposes by:

Uncommenting yt-dlp in requirements.txt.

Uncommenting the download button logic in app.py.

Use at your own risk.

⚠️ Disclaimer
This tool is for educational and research purposes only.

Do not use this tool to infringe on copyright.

Do not use this tool to harass users found via Geo-Hunt.

Respect YouTube's API quotas and Terms of Service.

License: MIT License. Free to fork, modify, and distribute.

