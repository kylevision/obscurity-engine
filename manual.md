📖 OBSCURITY ENGINE v7.0 — OPERATOR'S MANUAL
1. Core Philosophy
The Obscurity Engine is not just a search tool; it is a reverse-search engine. While YouTube's algorithm is designed to show you what is popular (high views, high engagement), this engine is designed to find what is invisible.

It relies on a custom "Weirdness Score" algorithm that rates videos from 0 to 100 based on:

Low Views: < 10 views is the gold standard.

Filename Patterns: Raw uploads like IMG_0492.MOV score higher.

Age: Older videos with fewer views score higher (Forgotten content).

Lack of Metadata: No description, no tags, default titles.

2. Feature Guide
🔍 Search (The Command Center)
The primary interface for locating content. It supports two modes: API (Official) and SCRAPE (No Key).

Inputs:

SYS>: Your search query.

QTY: How many results to fetch (Deep Paging is automatic).

ERA: Presets for specific time periods (e.g., "Pre-HD Era 2005-2009").

Filters (Control Panel):

0V / Zero: Hard filter for videos with exactly 0 views.

GHOST: Finds videos with 0 likes and 0 comments (true voids).

DEF: Restricts results to "Default Filenames" (e.g., DSCN1024, IMG_005).

Buttons:

EXEC: Runs the specific query.

RND: Generates a random "Time Travel" query (a random filename + a random week in history).

⚡ (Chaos): Injects 5 completely random queries (hashes, dates, broken unicode) to break the algorithm's context.

🗺️ Geo-Hunter
Finds "raw" reality by searching for video uploads geotagged to specific coordinates.

How it works: You pick a location (or click the map) and a radius (e.g., 5km). The engine searches for videos uploaded from that circle.

Use Case: Finding unedited footage of specific events, exploring remote towns, or digital tourism.

Pro Tip: Combining Geo-Hunter with 0V filters often yields personal vlogs or accidental uploads that no one has ever seen.

🐇 Rabbit Hole
A recursive discovery tool designed to dig deeper into a niche.

Logic: It takes the tags, titles, and channel names from your current search results and generates new, highly specific queries based on them.

Workflow:

Perform a normal search (e.g., "VHS tape").

Go to Rabbit Hole.

Click GEN. The system might generate queries like "Maxell T-120", "Family Trip 1993", or "Camcorder transfer".

Click EXEC ALL to search all those new terms simultaneously.

🕵️ Channel Autopsy
Performs a deep forensic analysis of a specific YouTube channel.

Bot Fingerprint: Analyzes the upload timestamps of the channel's videos. If a channel uploads 50 videos in one second, or exactly every 4 hours 00 minutes, it flags it as a BOT. Human uploads are erratic.

Burst Detection: Highlights days where the channel uploaded an abnormal amount of content (often indicates a data dump or hacked account).

Dead Channel: Calculates how long the channel has been inactive.

🕸️ Crawl
A "Spider" that moves through the "Related Videos" chain.

Depth: How many "hops" away from the start to go.

Per_Hop: How many related videos to grab at each step.

Concept: This mimics "falling down a YouTube hole" at 100x speed. It is excellent for finding content that is algorithmically adjacent to your topic but not directly searchable.

📺 Roulette
The "I'm Feeling Lucky" of the deep web.

Next: Generates a valid, random YouTube Video ID (e.g., dQw4w9WgXcQ) and checks if it exists.

Queue 10: Brute-forces a batch of random IDs.

Note: The hit rate for random 11-character IDs is astronomically low. This module uses a "Smart Seed" method to guess IDs that are mathematically likely to exist based on known clusters.

💀 Brute Force
A more aggressive version of Roulette, focused on Lost Media.

Near Scan: You input a video ID that you know exists (e.g., an old 2006 video). The engine scans ID+1, ID-1, etc. YouTube IDs are not sequential, but they often cluster in time.

Wayback: Checks if the videos found in your current results have been saved to the Internet Archive (Wayback Machine). Essential for verifying if a video is "safe" or at risk of total deletion.

⏳ Time Capsule
Opens a window to a specific day in history.

Logic: Generates queries for generic filenames (MVI_, IMG_) and restricts the search to a single 24-hour period (e.g., June 15, 2010).

Result: You see exactly what the world was uploading on that specific day, unfiltered by popularity.

🔬 Deep Analysis & 🔊 Media
Advanced forensics for the data hoarder.

Anomalies: Flags videos with weird metadata (e.g., "Upload date in the future", "Title contains Zalgo text").

Audio Scan: Uses FFprobe (if installed) to detect if a video is silent, has low bitrate, or has specific audio codecs.

Subtitle Mine: Downloads the auto-generated captions for all result videos and searches the text of the video (e.g., find videos where someone says "help me").

📦 The Vault (Archival)
Note: Disabled by default in the public release.

Function: A local archive manager.

Capabilities:

Downloads video (.mp4), thumbnail (.jpg), metadata (.json), and subtitles (.vtt).

Prevents duplicates (checks if video ID is already in the database).

Manual Download: Allows pasting any URL to archive it instantly.

3. Configuration Tips
API vs. Scraper
API (Recommended): Requires a Google Cloud API Key.

Pros: Fast, accurate date filtering, deep paging (up to 500 results).

Cons: Limited to 10,000 quota units per day (approx. 100 searches).

Scraper (No Key):

Pros: Unlimited searches, no setup.

Cons: Slower, date filtering is less precise, IP address can be soft-banned by YouTube if abused (returns "429 Too Many Requests").

Rate Limiting
To avoid getting blocked:

Do not set QTY to 500 repeatedly in Scraper mode.

If using Chaos or Crawl, add a small delay between requests (the engine does this automatically, but be patient).

Exporting Data
HTML: Generates a "clickable report" that looks like a webpage. Great for sharing finds.

Obsidian (.md): Exports results as Markdown notes, perfect for researchers using Obsidian or Notion.

RSS: Creates an XML feed of your findings, which you can plug into a news reader.
