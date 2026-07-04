#!/usr/bin/env python3
"""One-off scraper for The Federalist Papers from the Avalon Project (Yale Law School).

Each of the 85 papers lives on its own page:
    https://avalon.law.yale.edu/18th_century/fedNN.asp

Every page carries the essay body as a run of <p> tags (all site navigation lives
in <div>/<table> chrome), and a leading heading of the form
    "{subject}  {journal/edition}.  {date}."
We derive the canonical subject and original publication date straight from that
heading — faithful to the source, no hand transcription — and take the <p> run as
the body. Output: federalist_raw.json, in the ExtractedPost dict shape expected by
`backstack.py clean`.
"""

import re
import json
import time
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

BASE = "https://avalon.law.yale.edu/18th_century/fed{:02d}.asp"
HEADERS = {
    "User-Agent": "Replay/0.1 (blog archiver; +https://replay.pub)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Phrases that mark the end of the subject and the start of publication metadata.
# A marker only counts when a publication word follows shortly after — otherwise a
# subject that itself contains "From the ..." (e.g. No. 45) would be truncated.
JOURNAL_MARKERS = [" For the ", " From the ", " From MCLEAN", " From McLEAN", " From MC"]
PUBLICATION_WORDS = ("Journal", "Fournal", "Packet", "Advertiser", "Edition",
                     "McLEAN", "MCLEAN", "Independent", "Daily", "New York", "New-York")
DATE_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4})"
)
AUTHOR_RE = re.compile(r"^(HAMILTON|MADISON|JAY|MCLEAN)(\s+(AND|OR)\s+(HAMILTON|MADISON|JAY))?$")

client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
)
def fetch(url: str) -> httpx.Response:
    resp = client.get(url)
    resp.raise_for_status()
    return resp


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_page(html: str, n: int):
    """Return (subject, author, published_date_or_None, body_html)."""
    soup = BeautifulSoup(html, "html.parser")

    # --- Subject line: first heading that isn't site chrome or a bare byline ---
    subject_heading = None
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        t = norm(el.get_text(" "))
        if not t or "Avalon" in t or "Federalist Papers" in t:
            continue
        if AUTHOR_RE.match(t):  # a standalone author byline
            continue
        subject_heading = t
        break

    subject, author, published = "", None, None
    if subject_heading:
        head = subject_heading
        # Split subject off from the journal/edition + date tail. Only accept a
        # marker whose following ~45 chars actually name a publication.
        cut = len(head)
        for mk in JOURNAL_MARKERS:
            start = 0
            while True:
                i = head.find(mk, start)
                if i == -1:
                    break
                tail = head[i + len(mk): i + len(mk) + 45]
                if any(w in tail for w in PUBLICATION_WORDS):
                    cut = min(cut, i)
                    break
                start = i + len(mk)
        subject = head[:cut].strip(" .:")
        subject = re.sub(r"(\w)\(", r"\1 (", subject)  # "Continued(The" -> "Continued (The"
        dm = DATE_RE.search(head)
        if dm:
            published = dm.group(1)

    # Author byline (captured for the sanity log only; not stored per-post).
    for el in soup.find_all(["h3", "h4", "h5"]):
        t = norm(el.get_text(" "))
        if AUTHOR_RE.match(t):
            author = t.title().replace(" And ", " and ").replace(" Or ", " or ")
            break

    # --- Body: the run of non-empty <p> tags ---
    paras = [p for p in soup.find_all("p") if p.get_text(strip=True)]
    body_html = "\n".join(str(p) for p in paras)

    return subject, author, published, body_html


def main():
    posts = []
    for n in range(1, 86):
        url = BASE.format(n)
        resp = fetch(url)
        subject, author, published_str, body_html = parse_page(resp.text, n)

        title = f"No. {n}: {subject}" if subject else f"No. {n}"

        published_at = None
        if published_str:
            try:
                published_at = datetime.strptime(published_str, "%B %d, %Y").isoformat()
            except ValueError:
                published_at = None
        if not published_at:
            # Synthetic monotonic fallback keeps chronological ordering.
            published_at = (datetime(1787, 10, 27) + timedelta(days=n)).isoformat()

        posts.append({
            "title": title,
            "url": url,
            "content_html": body_html,
            "slug": f"federalist-no-{n}",
            "published_at": published_at,
            "tags": [],
            "post_index": n,
        })
        print(f"[{n:>2}/85] {title}  | {author or '?'}  | {published_str or '(synthetic)'}  | {len(body_html)}B")
        time.sleep(0.4)

    with open("federalist_raw.json", "w") as f:
        json.dump(posts, f, indent=2)

    empties = [p["post_index"] for p in posts if not p["content_html"]]
    no_subject = [p["post_index"] for p in posts if p["title"].strip().endswith(str(p["post_index"])) and ":" not in p["title"]]
    real_dates = sum(1 for p in posts if not p["published_at"].startswith("1787-10"))
    print(f"\nSaved {len(posts)} papers to federalist_raw.json")
    print(f"Real dates: {real_dates}/85 | empty bodies: {empties or 'none'} | missing subject: {no_subject or 'none'}")


if __name__ == "__main__":
    main()
