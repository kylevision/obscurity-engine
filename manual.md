📖 OBSCURITY ENGINE v7.0 — OPERATOR'S MANUAL (CORRECTED)
2. Feature Guide
🔍 Search (The Command Center)
The primary interface. By default, many controls are tucked away to keep the interface clean.

Main Controls:

QUERY... (Text Box): This is where you type your search terms. (The label "SYS>" is hidden).

EXEC: The "Execute" button. Runs the search.

RAND: Generates a random "Time Travel" query.

CHAOS: Injects 5 random queries to confuse the algorithm.

Visible Filters:

API / SCRAPE / ARCH: Toggles for the different search engines.

MAX_V: "Max Views". The most important filter. Defaults to 10. Videos with more views than this are hidden.

ERA: A dropdown to pick a time period (e.g., "Pre-HD Era").

FROM / TO: Specific date ranges.

Control Panel (The Hidden Menu):

Click "CONTROL PANEL" to expand this area.

Tab: FILT (Filters):

PER_Q: "Per Query". This is your Quantity slider. It defaults to 25 or 50. This is where you increase the number of results.

ZERO: Check this to force exactly 0 views.

GHOST: Check this to find videos with 0 likes and 0 comments.

SORT: Change from "date" to "viewCount" or "relevance".

Tab: PAT (Patterns):

Checkboxes for filename patterns like IMG_XXXX or DSC_XXXX.

Tab: ADV (Advanced):

TIT_HAS: Filter results to only those containing a specific word in the title.

MIN_AGE: Filter for videos at least X days old.

🗺️ Geo-Hunter
Location Picker: "📍 PICK A LOCATION".

Radius: Slider from 1km to 500km.

MAX VIEWS: Separate max view filter for geo-results.

SCAN LOCATION: The execute button for this mode.

🐇 Rabbit Hole
Q1, Q2...: Input boxes for recursive queries.

TAGS: Input comma-separated tags here.

GEN: Generates new queries based on your tags.

EXEC ALL: Runs all the queries in the Q boxes at once.

🕵️ Channel Autopsy
CHANNEL ID: Paste the ID here (e.g., UC...).

SCRAPER: Checkbox to use the scrape engine (no API key needed).

AUTOPSY: Runs the analysis.

🕸️ Crawl
SEED: The starting video ID or URL.

DEPTH: How many "hops" to go from the seed.

PER_HOP: How many related videos to grab per hop.

CRAWL: Starts the spider.

📺 Roulette
NEXT: Finds one random video.

QUEUE 10: Finds a batch of 10.

SKIP: Moves to the next video in the queue.

DL: Disabled in this version.

💀 Brute Force
Tab: RANDOM:

BATCH: Slider for how many IDs to guess.

SCAN: Starts guessing.

Tab: NEAR:

SEED ID: A known valid video ID.

COUNT: How many adjacent IDs to check.

SCAN NEAR: Runs the neighbor check.

Tab: WAYBACK:

CHECK: Checks if current search results are saved in the Internet Archive.

📦 Vault
N / YT / IA / SIZE: Stats counters for your local archive.

Manual Download: Displays "Manual download disabled for GitHub release."

💡 Quick Tips for V7.0
Where is the quantity slider? It is hidden! You must click CONTROL PANEL > FILT tab > PER_Q.

How do I get more than 50 results? In the default V7.0, you can't easily do "Deep Paging" without the code modification I sent earlier. The PER_Q slider is capped at 50 to protect your API quota.

Why am I seeing 0 results? Check your MAX_V. If it is set to 10, and you search for "Minecraft", you will get 0 results because all Minecraft videos have >10 views. Try increasing MAX_V or searching for something more obscure.
