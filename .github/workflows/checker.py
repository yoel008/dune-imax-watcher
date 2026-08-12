"""
Checks the Cineplex Scotiabank Montreal theatre page for
"Dune: Part Three" showing in IMAX 70mm, and sends a push
notification to your phone (via ntfy.sh) the moment it appears.

Personal use only. This visits one public page at a low
frequency (every ~15 min, set in the GitHub Actions workflow) —
it does not hit Cineplex's internal booking APIs or try to
buy anything. It just watches and pings you.
"""

import os
import sys

import requests
from playwright.sync_api import sync_playwright

THEATRE_URL = "https://www.cineplex.com/theatre/cinema-banque-scotia-montreal"

# If Cineplex ever phrases things slightly differently, tweak these.
MOVIE_KEYWORDS = ["dune: part three", "dune part three", "dune: part 3"]
FORMAT_KEYWORDS = ["70mm", "70 mm", "imax 70"]

FLAG_FILE = "found.flag"


def page_mentions_dune_70mm(text: str) -> bool:
    lowered = text.lower()
    has_movie = any(k in lowered for k in MOVIE_KEYWORDS)
    has_format = any(k in lowered for k in FORMAT_KEYWORDS)
    return has_movie and has_format


def fetch_theatre_page_text() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (compatible; personal-ticket-alert-script/1.0; "
                "single user, checks every 15 min, no ticketing calls)"
            )
        )
        # networkidle waits for the page's JS to finish loading data
        page.goto(THEATRE_URL, wait_until="networkidle", timeout=45000)
        text = page.inner_text("body")
        browser.close()
        return text


def send_push_notification():
    topic = os.environ["NTFY_TOPIC"]
    requests.post(
        f"https://ntfy.sh/{topic}",
        data="Dune: Part Three IMAX 70mm may be listed at Scotiabank Montreal. Go check now!".encode("utf-8"),
        headers={
            "Title": "Dune Part 3 - 70mm tickets!",
            "Priority": "urgent",
            "Click": THEATRE_URL,
        },
        timeout=15,
    )


def main():
    if os.path.exists(FLAG_FILE):
        print("Already notified once - skipping. Delete found.flag in the repo to re-arm.")
        return

    try:
        text = fetch_theatre_page_text()
    except Exception as e:
        # Don't crash the whole workflow over one flaky load - just log it.
        print(f"Couldn't load the page this time: {e}")
        sys.exit(0)

    if page_mentions_dune_70mm(text):
        print("Match found! Sending notification...")
        send_push_notification()
        with open(FLAG_FILE, "w") as f:
            f.write("found")
    else:
        print("No Dune Part 3 70mm showtimes yet.")


if __name__ == "__main__":
    main()
