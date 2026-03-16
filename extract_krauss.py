#!/usr/bin/env python3
"""
Extract 'The Engine of Scientific Discovery' by Alexander Krauss into clean JSON
for the backstack.py upload tool.

Book page 1 = PDF page index 11 (0-indexed). So pdf_index = book_page + 10.
Chapters 1-11 + Introduction span book pages 1-295.
"""

import json
import re
from pypdf import PdfReader

PDF_PATH = "/Users/charl/Programming/replaypub/polanyi_engine.pdf"
OUTPUT_PATH = "/Users/charl/Programming/replaypub/krauss_clean.json"
BASE_URL = "https://personal.lse.ac.uk/kraussa/The%20Engine%20of%20Scientific%20Discovery.pdf"
PAGE_OFFSET = 10  # pdf_index = book_page + 10

# Chapter definitions: (chapter_id, short_title, tag, book_page_start, book_page_end)
CHAPTERS = [
    ("intro", "Introduction", "introduction", 1, 20),
    ("ch1", "Sparking Discovery", "ch1-sparking-discovery", 21, 57),
    ("ch2", "Engineering Serendipity", "ch2-engineering-serendipity", 58, 76),
    ("ch3", "Paradigm Shifts or Cumulative Progress", "ch3-paradigm-shifts-or-cumulative-progress", 77, 99),
    ("ch4", "Discovery-Makers", "ch4-discovery-makers", 100, 117),
    ("ch5", "The Birth of Fields", "ch5-birth-of-fields", 118, 134),
    ("ch6", "The Discovery Engine", "ch6-discovery-engine", 135, 194),
    ("ch7", "The Origins of Our Toolbox", "ch7-origins-of-our-toolbox", 195, 226),
    ("ch8", "Homo Methodologicus", "ch8-homo-methodologicus", 227, 240),
    ("ch9", "The New Methods-Driven Discovery Theory", "ch9-methods-driven-discovery-theory", 241, 260),
    ("ch10", "The Edge of Discovery", "ch10-edge-of-discovery", 261, 275),
    ("ch11", "Pushing the Limits of Science", "ch11-pushing-limits-of-science", 276, 295),
]

# Subsection headings per chapter (in order of appearance).
# These must match the text as it appears AFTER rejoining split initials.
CHAPTER_HEADINGS = {
    "intro": [
        "Sparking a method revolution in science",
        "Mapping discovery: the book\u2019s structure and key insights",
    ],
    "ch1": [
        "Summary",
        "Overview",
        "How we measure and track science\u2019s major discoveries",
        "Five key insights: how powerful new methods and tools trigger discovery",
        "We spark science\u2019s major discoveries by developing a new method or tool",
        "Our powerful tools trigger new breakthroughs by extending what and how we can observe, detect and measure the world",
        "There are three ways new methods and tools power new discoveries",
        "New breakthroughs often follow soon after developing the new enabling tools",
        "Creating a new method or tool is often more foundational to scientific progress",
        "The causal effect: how new tools trigger new discoveries",
        "Conclusion",
    ],
    "ch2": [
        "Summary",
        "Overview",
        "Measuring serendipitous discoveries",
        "Uncovering the elusive role of serendipitous moments in scientific discoveries",
        "Vision-enhancing tools trigger unexpected discoveries most often",
        "Serendipitous discoveries triggered by new tools and methods",
        "The powerful role of our tool innovations",
        "The odds of uncovering serendipitous breakthroughs are zero before we develop the tools of discovery",
        "The scientific toolbox view of discovery",
        "Conclusion",
    ],
    "ch3": [
        "Summary",
        "Overview",
        "Measuring revolutionary and cumulative scientific progress",
        "A conceptual framework of the cumulative nature of science",
        "Evolution over revolution in science",
        "Redefining the scientific method",
        "Conclusion",
    ],
    "ch4": [
        "Summary",
        "Overview",
        "Most discoverers have an interdisciplinary education with training",
        "Greater productivity and impact of younger scientists",
        "Only about a third of discoverers since 1950 worked at top 25",
        "Funding and the scientific community",
        "Conclusion",
    ],
    "ch5": [
        "Summary",
        "Overview",
        "Measuring and tracking the birth of scientific fields",
        "The origins of new fields: the power of new methods and tools",
        "The most powerful tools we leverage to drive new fields across",
        "Conclusion",
    ],
    "ch6": [
        "Summary",
        "Overview",
        "Establishing new methods and tools as the engine of science and discovery",
        "How our powerful tools drive scientific progress and make our best",
        "New tools stretch our imagination and provide an intentional",
        "New transformative method innovations unlock new discoveries and fields",
        "Methods labs and methods hubs: why we need to establish",
        "Eight pathways to invent and reinvent our methods",
        "Developing the new field of Methodology of Science",
        "Conclusion",
    ],
    "ch7": [
        "Summary",
        "Overview",
        "Rethinking the origins of science and civilisation, beyond culture and geography: the missing role of methods",
        "Our early ancestors sparked major early breakthroughs through method revolutions",
        "Science of smart animals",
        "Science of early humans",
        "Homo sapiens science (until about 11,000 years ago)",
        "Early civilisation science",
        "Ancient Chinese and Ancient Greek science",
        "How did we develop modern science around the 17th century?",
        "The invention of the microscope and telescope: the key turning point",
        "Greater use of mathematics to describe what new tools uncovered",
        "Tools and methods sparked a deeper understanding of scientific methodology",
        "National scientific societies, the growing scientific community and systematic observational methods took off after, not before, the microscope and telescope",
        "The enabling conditions for science and civilisation: a framework",
        "Conclusion",
    ],
    "ch8": [
        "Summary",
        "Overview",
        "Where does the mind end and the methods we create begin?",
        "Expanding our toolbox: a strategy for survival, solving problems and gaining knowledge",
        "Our species\u2019 most unique capacity: cumulative method-making",
        "Our universal toolbox: an early, unified method for gaining knowledge over human history",
        "On the origin of science: how our mind\u2019s method-making capacity drove human evolution",
        "Mimicking, upgrading and outsourcing our evolved mind with better tools",
        "Conclusion",
    ],
    "ch9": [
        "Summary",
        "Overview",
        "Before-and-after (statistical) explanation",
        "Evolutionary explanation",
        "Cognitive constraint explanation",
        "Scientific practice explanation",
        "Philosophical explanation",
        "The new methods-driven discovery theory: backed by five different perspectives",
        "A method revolution in science",
        "Conclusion",
    ],
    "ch10": [
        "Summary",
        "Overview",
        "The evolution of science: expanding the boundaries of science",
        "The five factors shaping the current limits of science",
        "How the current boundaries of our toolbox shape the current boundaries of science",
        "Conclusion",
    ],
    "ch11": [
        "Summary",
        "Overview",
        "Redrawing the edges of science by reinventing our toolbox",
        "How artificial intelligence can be combined with our scientific tools to accelerate science",
        "Are there set limits to human knowledge and what we can discover?",
        "Inventing the future of science",
        "Conclusion: the science of discovery",
    ],
}

# Long heading display names (for titles) - maps from search prefix to full display name
HEADING_DISPLAY = {
    "Most discoverers have an interdisciplinary education with training": "Most discoverers have an interdisciplinary education",
    "Only about a third of discoverers since 1950 worked at top 25": "Only about a third of discoverers worked at top 25 universities",
    "Establishing new methods and tools as the engine of science and discovery": "Establishing new methods and tools as the engine of science",
    "How our powerful tools drive scientific progress and make our best": "How our powerful tools drive scientific progress",
    "New tools stretch our imagination and provide an intentional": "New tools stretch our imagination",
    "New transformative method innovations unlock new discoveries and fields": "New method innovations unlock new discoveries and fields",
    "Methods labs and methods hubs: why we need to establish": "Methods labs and methods hubs",
    "Developing the new field of Methodology of Science": "Developing the new field of Methodology of Science",
    "Eight pathways to invent and reinvent our methods": "Eight pathways to invent and reinvent our methods",
    "The invention of the microscope and telescope: the key turning point": "The invention of the microscope and telescope",
    "Expanding our toolbox: a strategy for survival, solving problems and gaining knowledge": "Expanding our toolbox",
    "Mimicking, upgrading and outsourcing our evolved mind with better tools": "Mimicking, upgrading and outsourcing our evolved mind with better tools",
    "The most powerful tools we leverage to drive new fields across": "The most powerful tools we leverage to drive new fields",
    "Measuring and tracking the birth of scientific fields": "Measuring and tracking the birth of scientific fields",
    "The origins of new fields: the power of new methods and tools": "The origins of new fields",
    "Measuring revolutionary and cumulative scientific progress": "Measuring revolutionary and cumulative scientific progress",
    "A conceptual framework of the cumulative nature of science": "A conceptual framework of the cumulative nature of science",
    "Evolution over revolution in science": "Evolution over revolution in science",
    "Redefining the scientific method": "Redefining the scientific method",
    "Conclusion: the science of discovery": "Conclusion: the science of discovery",
    "Inventing the future of science": "Inventing the future of science",
}


def extract_chapter_text(reader, book_start, book_end):
    """Extract text from a range of book pages and rejoin split initial capitals."""
    all_lines = []
    for book_page in range(book_start, book_end + 1):
        pdf_index = book_page + PAGE_OFFSET
        if pdf_index < len(reader.pages):
            page = reader.pages[pdf_index]
            text = page.extract_text() or ""
            all_lines.extend(text.split("\n"))

    # Rejoin split initial capitals (decorative drop caps)
    # Pattern: single uppercase letter on one line, rest of word on next line starting lowercase
    rejoined = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        stripped = line.strip()
        if len(stripped) <= 2 and stripped and stripped[0].isupper() and i + 1 < len(all_lines):
            next_line = all_lines[i + 1].strip()
            if next_line and next_line[0].islower():
                rejoined.append(stripped + next_line)
                i += 2
                continue
        rejoined.append(line)
        i += 1

    return "\n".join(rejoined)


def clean_page_headers(text):
    """Remove page headers like 'SPARKING DISCOVERY 23' or '42 THE ENGINE OF SCIENTIFIC DISCOVERY'."""
    lines = text.split("\n")
    cleaned = []

    # Known header patterns (case-insensitive)
    header_patterns = [
        r"^the engine of scientific discovery$",
        r"^sparking discovery$",
        r"^engineering serendipity$",
        r"^revolutionary paradigm shifts or cumulative progress$",
        r"^discovery-makers$",
        r"^the birth of fields$",
        r"^the discovery engine$",
        r"^the origins of our toolbox$",
        r"^homo methodologicus$",
        r"^the new methods-driven discovery theory$",
        r"^the edge of discovery$",
        r"^pushing the limits of science$",
        r"^introduction$",
    ]

    for line in lines:
        stripped = line.strip()

        # Skip empty lines (keep them for paragraph detection)
        if not stripped:
            cleaned.append(line)
            continue

        # Pattern: NUMBER + TITLE (e.g., "42 THE ENGINE OF SCIENTIFIC DISCOVERY")
        if re.match(r"^\d{1,3}\s+[A-Z]", stripped):
            rest = re.sub(r"^\d{1,3}\s+", "", stripped).strip()
            if any(re.match(p, rest, re.IGNORECASE) for p in header_patterns):
                continue

        # Pattern: TITLE + NUMBER (e.g., "SPARKING DISCOVERY 23")
        if re.match(r"^[A-Z].*\s+\d{1,3}$", stripped):
            rest = re.sub(r"\s+\d{1,3}$", "", stripped).strip()
            if any(re.match(p, rest, re.IGNORECASE) for p in header_patterns):
                continue

        # Pattern: ALL CAPS headers with numbers
        if re.match(r"^[A-Z][A-Z\s\u2019\u2014\-,]+\d{1,3}$", stripped):
            continue

        # Skip DOI lines and copyright lines (these appear at bottom of chapter-opening pages)
        if stripped.startswith("DOI:") or stripped.startswith("The Engine of Scientific Discovery. Alexander Krauss"):
            continue
        if "Oxford University Press" in stripped and ("DOI:" in stripped or "\u00a9" in stripped or "©" in stripped):
            continue

        cleaned.append(line)
    return "\n".join(cleaned)


def strip_citations(text):
    """Remove citation numbers like (1), (1,2), (1-3), (17,25,28) from text."""
    # Remove parenthetical citation numbers with various separators
    text = re.sub(r"\(\d{1,3}(?:\s*[,\u2013\u2014\-]\s*\d{1,3})*\)", "", text)
    return text


def normalize_text(text):
    """Normalize unicode characters."""
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"  +", " ", text)
    return text


def find_heading_in_text(text, heading):
    """Find a heading in text. Must match at the start of a line to avoid false matches in body text."""
    lower_heading = heading.lower()

    # Build search variants (different quote/dash styles)
    variants = [lower_heading]
    for old, new in [("'", "\u2019"), ("\u2019", "'"), ("\u2014", "-"), ("-", "\u2014"), ("\u2013", "-")]:
        v = lower_heading.replace(old, new)
        if v not in variants:
            variants.append(v)

    # For each variant, try to find it at the start of a line
    for variant in variants:
        # Try full heading at line start
        pattern = r"(?:^|\n)\s*" + re.escape(variant)
        m = re.search(pattern, text.lower())
        if m:
            # Return position of the heading text itself (skip the newline)
            actual_start = text.lower().find(variant, m.start())
            if actual_start != -1:
                return actual_start

    # Try prefix matching at line start (first 35 chars)
    for variant in variants:
        prefix = variant[:35]
        pattern = r"(?:^|\n)\s*" + re.escape(prefix)
        m = re.search(pattern, text.lower())
        if m:
            actual_start = text.lower().find(prefix, m.start())
            if actual_start != -1:
                return actual_start

    # Try even shorter prefix at line start (first 20 chars)
    for variant in variants:
        prefix = variant[:20]
        pattern = r"(?:^|\n)\s*" + re.escape(prefix)
        m = re.search(pattern, text.lower())
        if m:
            actual_start = text.lower().find(prefix, m.start())
            if actual_start != -1:
                return actual_start

    return -1


def split_by_headings(text, headings):
    """Split text into sections based on headings.

    Headings are searched in order, and each must appear after the previous one.
    This prevents matching chapter title/subtitle text instead of actual section headings.
    """
    positions = []
    min_pos = 0  # Each heading must be found after the previous one
    for heading in headings:
        pos = find_heading_in_text(text[min_pos:], heading)
        if pos != -1:
            actual_pos = min_pos + pos
            positions.append((actual_pos, heading))
            min_pos = actual_pos + 1
        else:
            print(f"  WARNING: Could not find heading: '{heading[:60]}...'")

    # Already in order, but sort just in case
    positions.sort(key=lambda x: x[0])

    sections = []
    for i, (pos, heading) in enumerate(positions):
        # Find the end of the heading text (just skip to the next newline)
        heading_end = text.find("\n", pos)
        if heading_end == -1:
            heading_end = pos + len(heading)
        else:
            heading_end += 1  # skip past the newline

        if i + 1 < len(positions):
            next_pos = positions[i + 1][0]
            content = text[heading_end:next_pos].strip()
        else:
            content = text[heading_end:].strip()

        sections.append((heading, content))

    return sections


def text_to_paragraphs(text):
    """Convert raw text to paragraphs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split on double newlines
    raw_paragraphs = re.split(r"\n\s*\n", text)

    paragraphs = []
    for para in raw_paragraphs:
        # Join single line breaks (word wrapping)
        para = re.sub(r"(?<![.\n])\n(?!\n)", " ", para)
        # Fix hyphenation at line breaks
        para = re.sub(r"(\w)-\s+(\w)", r"\1\2", para)
        para = para.strip()

        if not para or len(para) < 20:
            continue

        # Skip figure/table/picture/box captions
        if re.match(r"^(?:Figure|Table|Picture|Box)\s+\d", para, re.IGNORECASE):
            continue

        # Skip page numbers
        if re.match(r"^\d{1,3}$", para):
            continue

        # Skip copyright/DOI lines (only if they start with it)
        if para.startswith("DOI:"):
            continue
        if para.startswith("The Engine of Scientific Discovery. Alexander Krauss"):
            continue

        # Skip Part headers
        if re.match(r"^PART\s+[IVX]+", para):
            continue

        # Skip chart data lines
        if re.match(r"^[\d\s.,<>%]+$", para):
            continue

        paragraphs.append(para)

    return paragraphs


def get_display_heading(heading):
    """Get the display name for a heading."""
    return HEADING_DISPLAY.get(heading, heading)


def make_slug(chapter_id, heading):
    """Generate a URL-friendly slug."""
    prefix = "introduction" if chapter_id == "intro" else chapter_id
    display = get_display_heading(heading)

    slug_text = display.lower()
    slug_text = slug_text.replace("\u2014", "-").replace("\u2013", "-")
    slug_text = slug_text.replace("'", "").replace("\u2019", "")
    slug_text = re.sub(r"[^a-z0-9\s-]", "", slug_text)
    slug_text = re.sub(r"\s+", "-", slug_text.strip())
    slug_text = re.sub(r"-+", "-", slug_text)

    if len(slug_text) > 60:
        slug_text = slug_text[:60].rsplit("-", 1)[0]

    return f"{prefix}-{slug_text}"


def make_title(chapter_id, chapter_short_title, heading):
    """Generate the display title."""
    display = get_display_heading(heading)
    if chapter_id == "intro":
        return f"Introduction \u2014 {display}"
    else:
        ch_num = chapter_id.replace("ch", "")
        return f"Ch {ch_num}: {chapter_short_title} \u2014 {display}"


def main():
    print("Reading PDF...")
    reader = PdfReader(PDF_PATH)
    print(f"Total pages: {len(reader.pages)}")

    posts = []
    post_index = 1

    for chapter_id, short_title, tag, page_start, page_end in CHAPTERS:
        print(f"\nProcessing {chapter_id}: {short_title} (pages {page_start}-{page_end})...")

        raw_text = extract_chapter_text(reader, page_start, page_end)
        text = clean_page_headers(raw_text)
        text = strip_citations(text)
        text = normalize_text(text)

        headings = CHAPTER_HEADINGS.get(chapter_id, [])
        if not headings:
            print(f"  No headings defined for {chapter_id}, skipping")
            continue

        sections = split_by_headings(text, headings)
        if not sections:
            print(f"  WARNING: No sections found for {chapter_id}")
            continue

        print(f"  Found {len(sections)} sections")

        for heading, content in sections:
            paragraphs = text_to_paragraphs(content)

            if not paragraphs:
                print(f"  Skipping empty section: {heading[:50]}")
                continue

            content_html = "".join(f"<p>{p}</p>" for p in paragraphs)
            content_text = "\n\n".join(paragraphs)

            excerpt = content_text[:150]
            if len(content_text) > 150:
                last_space = excerpt.rfind(" ")
                if last_space > 100:
                    excerpt = excerpt[:last_space]
                excerpt += "..."

            word_count = len(content_text.split())
            reading_time = max(1, round(word_count / 250))

            title = make_title(chapter_id, short_title, heading)
            slug = make_slug(chapter_id, heading)

            post = {
                "title": title,
                "url": BASE_URL,
                "content_html": content_html,
                "content_text": content_text,
                "excerpt": excerpt,
                "slug": slug,
                "published_at": "2026-01-01T00:00:00",
                "tags": [tag],
                "post_index": post_index,
                "word_count": word_count,
                "reading_time_minutes": reading_time,
            }

            posts.append(post)
            print(f"  [{post_index}] {title} ({word_count} words)")
            post_index += 1

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    total_words = sum(p["word_count"] for p in posts)
    print(f"\n{'='*60}")
    print(f"Total posts: {len(posts)}")
    print(f"Total words: {total_words:,}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
