#!/usr/bin/env python3
"""Extract The Frailest Thing EPUB into a clean JSON for ReplayPub."""

import json
import re
import sys
import warnings
import zipfile
from datetime import datetime
from html import unescape

warnings.filterwarnings("ignore")

from bs4 import BeautifulSoup, Comment
from scraper.clean import HTMLCleaner


EPUB_FILE = "The-Frailest-Thing-1576008735.epub"
BASE_URL = "https://thefrailestthing.com"
OUTPUT_FILE = "sacasas_clean.json"


MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def parse_date(text: str):
    """Extract and ISO-format the publication date (last 'Month DD, YYYY') from text."""
    matches = re.findall(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(\d{1,2}),?\s+(\d{4})",
        text,
    )
    if not matches:
        return None
    month_str, day_str, year_str = matches[-1]
    month, day, year = MONTH_MAP[month_str], int(day_str), int(year_str)
    return datetime(year, month, day).isoformat()


def extract_chapter(z: zipfile.ZipFile, fname: str):
    html = z.read(fname).decode("utf-8")
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("h2", class_="chapter-title")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    chapter_div = soup.find("div", class_=lambda c: c and "chapter" in c.split())
    slug = chapter_div["id"] if chapter_div and chapter_div.get("id") else None
    if not slug or slug.startswith("slug-"):
        # Fall back to filename-derived slug
        slug = re.sub(r"^chapter-\d+-(?:slug-\d+-)?", "", fname.split("/")[-1]).replace(".html", "")

    content_div = soup.find("div", class_="chapter-ugc")
    if not content_div:
        return None

    # Remove the chapter-title-wrap from content (already captured as title)
    title_wrap = soup.find("div", class_="chapter-title-wrap")
    if title_wrap:
        title_wrap.decompose()

    # Pull raw text before cleaning (for date extraction)
    raw_text = content_div.get_text(separator=" ")
    published_at = parse_date(raw_text)

    content_html = str(content_div)
    return {
        "title": title,
        "slug": slug,
        "url": f"{BASE_URL}/{slug}/",
        "published_at": published_at,
        "content_html": content_html,
        "tags": [],
    }


def main():
    cleaner = HTMLCleaner(BASE_URL)
    posts = []

    with zipfile.ZipFile(EPUB_FILE) as z:
        chapter_files = sorted(
            f for f in z.namelist() if re.match(r"OEBPS/chapter-\d+-.+\.html$", f)
        )
        print(f"Found {len(chapter_files)} chapters")

        for i, fname in enumerate(chapter_files, 1):
            post = extract_chapter(z, fname)
            if not post:
                print(f"  Skipping {fname} — no title/content found")
                continue

            result = cleaner.clean(post["content_html"], post["title"])
            posts.append({
                "title": post["title"],
                "url": post["url"],
                "slug": post["slug"],
                "published_at": post["published_at"] or f"2026-01-{i:02d}T00:00:00",
                "content_html": result["html"],
                "content_text": result["text"],
                "excerpt": result["excerpt"],
                "word_count": result["word_count"],
                "reading_time_minutes": result["reading_time_minutes"],
                "tags": [],
                "post_index": i,
            })
            print(f"  [{i:3d}] {post['title'][:60]}  ({post['published_at'] or 'no date'})")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(posts)} posts to {OUTPUT_FILE}")


if __name__ == "__main__":
    sys.exit(main())
