#!/usr/bin/env python3
"""Extract Michael Polanyi's Duke and Wesleyan lectures from PDFs into JSON."""

import json
import re
import fitz  # pymupdf

DUKE_LECTURES = [
    {
        "file": "polanyi_pdfs/Duke1-searchable.pdf",
        "title": "The Metaphysical Reach of Science",
        "date": "1964-02-10",
        "url": "https://www.polanyisociety.org/Duke/Duke1-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Duke2-searchable.pdf",
        "title": "The Structure of Tacit Knowing",
        "date": "1964-02-17",
        "url": "https://www.polanyisociety.org/Duke/Duke2-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Duke3-searchable.pdf",
        "title": "Commitment to Science",
        "date": "1964-02-24",
        "url": "https://www.polanyisociety.org/Duke/Duke3-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Duke4-searchable.pdf",
        "title": "The Emergence of Man",
        "date": "1964-03-02",
        "url": "https://www.polanyisociety.org/Duke/Duke4-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Duke5-searchable.pdf",
        "title": "Thought in Society",
        "date": "1964-03-09",
        "url": "https://www.polanyisociety.org/Duke/Duke5-searchable.pdf",
    },
]

WESLEYAN_LECTURES = [
    {
        "file": "polanyi_pdfs/Weslyn-lec1--9-29-65-searchable.pdf",
        "title": "Science and Reality",
        "date": "1965-09-29",
        "url": "https://www.polanyisociety.org/WesleyanLectures/Weslyn-lec1--9-29-65-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Weslyn-lec2--10-14-65-searchable.pdf",
        "title": "The Structure of Tacit Knowing",
        "date": "1965-10-14",
        "url": "https://www.polanyisociety.org/WesleyanLectures/Weslyn-lec2--10-14-65-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Weslyn-lec3-10-21-65-searchable.pdf",
        "title": "The Creative Imagination",
        "date": "1965-10-21",
        "url": "https://www.polanyisociety.org/WesleyanLectures/Weslyn-lec3-10-21-65-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Weslyn-lec4--10-28-65-searchable.pdf",
        "title": "The Growth of Science in Society",
        "date": "1965-10-28",
        "url": "https://www.polanyisociety.org/WesleyanLectures/Weslyn-lec4--10-28-65-searchable.pdf",
    },
    {
        "file": "polanyi_pdfs/Weslyn-lec5-11-11-65-searchable.pdf",
        "title": "Levels of Reality",
        "date": "1965-11-11",
        "url": "https://www.polanyisociety.org/WesleyanLectures/Weslyn-lec5-11-11-65-searchable.pdf",
    },
]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')[:80]


def extract_pdf_text(filepath):
    """Extract text from PDF, cleaning up OCR artifacts."""
    doc = fitz.open(filepath)
    pages = []
    for page in doc:
        text = page.get_text()
        pages.append(text)
    doc.close()

    full_text = "\n\n".join(pages)

    # Clean up common OCR artifacts
    # Remove page numbers like "- 1 -", "- 2 -"
    full_text = re.sub(r'\n\s*-\s*\d+\s*-\s*\n', '\n', full_text)
    # Remove "FOR PRIVATE DISTRIBUTION/CIRCULATION ONLY" headers
    full_text = re.sub(r'FOR PRIVATE (?:DISTRIBUTION|CIRCULATION)(?: ONLY)?\s*\n?', '', full_text)
    # Clean up multiple blank lines
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    # Fix common OCR issues
    full_text = full_text.replace('~ichael', 'Michael')
    full_text = full_text.replace('becture', 'Lecture')

    return full_text.strip()


def text_to_html(text):
    """Convert plain text to simple HTML paragraphs."""
    import html
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Escape HTML entities
        p = html.escape(p)
        # Join lines within a paragraph
        p = re.sub(r'\n', ' ', p)
        # Clean up multiple spaces
        p = re.sub(r'  +', ' ', p)
        html_parts.append(f'<p>{p}</p>')
    return '\n'.join(html_parts)


def process_lectures(lectures, tag):
    """Process a series of lectures into post format."""
    posts = []
    for i, lec in enumerate(lectures, 1):
        print(f"  Extracting: {lec['title']}...")
        text = extract_pdf_text(lec['file'])
        content_html = text_to_html(text)

        # Word count
        words = len(text.split())
        reading_time = max(1, words // 250)

        # Excerpt: first ~200 chars of clean text
        excerpt = text[:200].rsplit(' ', 1)[0] + '...'

        posts.append({
            'title': lec['title'],
            'url': lec['url'],
            'slug': slugify(lec['title']),
            'content_html': content_html,
            'content_text': text,
            'excerpt': excerpt,
            'published_at': lec['date'] + 'T00:00:00',
            'post_index': i,
            'word_count': words,
            'reading_time_minutes': reading_time,
            'tags': [tag],
        })

    return posts


def main():
    print("Extracting Duke Lectures (1964)...")
    duke_posts = process_lectures(DUKE_LECTURES, 'duke-lectures')

    print(f"\nExtracted {len(duke_posts)} Duke lectures")
    for p in duke_posts:
        print(f"  {p['post_index']}. {p['title']} ({p['word_count']} words)")

    print("\nExtracting Wesleyan Lectures (1965)...")
    wesleyan_posts = process_lectures(WESLEYAN_LECTURES, 'wesleyan-lectures')

    print(f"\nExtracted {len(wesleyan_posts)} Wesleyan lectures")
    for p in wesleyan_posts:
        print(f"  {p['post_index']}. {p['title']} ({p['word_count']} words)")

    # Combine all posts for the single blog, re-index
    all_posts = duke_posts + wesleyan_posts
    for i, p in enumerate(all_posts, 1):
        p['post_index'] = i

    with open('polanyi_raw.json', 'w') as f:
        json.dump(all_posts, f, indent=2)

    print(f"\nSaved {len(all_posts)} total posts to polanyi_raw.json")


if __name__ == '__main__':
    main()
