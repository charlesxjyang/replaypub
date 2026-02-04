"""Blog post extraction with multiple strategies."""

import re
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class ExtractedPost:
    title: str
    url: str
    content_html: str
    slug: str
    published_at: Optional[str] = None
    tags: Optional[List[str]] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d['tags'] is None:
            d['tags'] = []
        return d


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')[:80]


def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Try to parse a date string into ISO format."""
    if not date_str:
        return None
    # Common date formats
    for fmt in (
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
        '%Y/%m/%d',
    ):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return date_str


class BlogExtractor:
    """Extract posts from a blog using multiple strategies."""

    HEADERS = {
        'User-Agent': 'Replay/0.1 (blog archiver; +https://replay.pub)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    def __init__(self, url: str, verbose: bool = False):
        self.url = url.rstrip('/')
        self.verbose = verbose
        self.client = httpx.Client(
            headers=self.HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [extract] {msg}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
    )
    def _fetch(self, url: str) -> httpx.Response:
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp

    def _safe_fetch(self, url: str) -> Optional[httpx.Response]:
        try:
            return self._fetch(url)
        except Exception as e:
            self._log(f"Failed to fetch {url}: {e}")
            return None

    def extract(self) -> List[ExtractedPost]:
        """Try extraction strategies in order, return first that works."""
        strategies = [
            ('structured archive', self._try_structured_archive),
            ('sitemap', self._try_sitemap),
            ('WordPress API', self._try_wp_api),
            ('archive page', self._try_archive),
            ('Wayback Machine', self._try_wayback),
        ]

        for name, strategy in strategies:
            self._log(f"Trying {name}...")
            try:
                posts = strategy()
                if posts:
                    self._log(f"{name} found {len(posts)} posts")
                    # Sort by published_at (oldest first), then by URL as fallback
                    posts.sort(key=lambda p: (p.published_at or '0000', p.url))
                    return posts
            except Exception as e:
                self._log(f"{name} failed: {e}")
                continue

        self._log("All strategies failed")
        return []

    def _extract_article(self, url: str, html: str) -> Optional[ExtractedPost]:
        """Use readability to extract article content from HTML."""
        try:
            doc = Document(html, url=url)
            title = doc.short_title()
            content = doc.summary()

            if not title or not content or len(content) < 100:
                return None

            # Try to extract date from HTML
            soup = BeautifulSoup(html, 'lxml')
            published_at = None

            # Check <time> tags
            time_tag = soup.find('time', attrs={'datetime': True})
            if time_tag:
                published_at = _parse_date(time_tag['datetime'])

            # Check meta tags
            if not published_at:
                for prop in ('article:published_time', 'datePublished', 'date'):
                    meta = soup.find('meta', attrs={'property': prop}) or soup.find('meta', attrs={'name': prop})
                    if meta and meta.get('content'):
                        published_at = _parse_date(meta['content'])
                        if published_at:
                            break

            return ExtractedPost(
                title=title,
                url=url,
                content_html=content,
                slug=_slugify(title),
                published_at=published_at,
            )
        except Exception as e:
            self._log(f"Failed to extract article from {url}: {e}")
            return None

    # ----- Strategy: Structured archive -----

    def _try_structured_archive(self) -> Optional[List[ExtractedPost]]:
        """Parse a structured archive page with <article> elements containing tags and dates."""
        archive_urls = [
            f"{self.url}/posts",
            f"{self.url}/archive",
            f"{self.url}/archives",
            self.url,
        ]

        for archive_url in archive_urls:
            resp = self._safe_fetch(archive_url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, 'lxml')
            articles = soup.find_all('article')

            if len(articles) < 5:
                continue

            self._log(f"Found {len(articles)} <article> elements on {archive_url}")

            # Parse metadata from each article
            post_meta = []
            for article in articles:
                title_tag = article.find(['h1', 'h2', 'h3'], class_=lambda c: c is None or 'title' in (c or ''))
                if not title_tag:
                    continue
                link = title_tag.find('a', href=True)
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = urljoin(archive_url, link['href'])

                # Extract tags from links to /tag/ paths
                tags = []
                for tag_link in article.find_all('a', href=True):
                    tag_href = tag_link['href']
                    if '/tag/' in tag_href or '/category/' in tag_href:
                        tags.append(tag_link.get_text(strip=True).lower())

                # Extract date
                date_str = None
                date_el = article.find(class_=lambda c: c and 'date' in c)
                if date_el:
                    date_str = date_el.get_text(strip=True)
                if not date_str:
                    time_el = article.find('time', attrs={'datetime': True})
                    if time_el:
                        date_str = time_el['datetime']

                post_meta.append({
                    'title': title,
                    'url': href,
                    'tags': tags,
                    'date_str': date_str,
                })

            if not post_meta:
                continue

            self._log(f"Parsed {len(post_meta)} posts with metadata, fetching content...")

            # Fetch and extract each post, attaching tags
            posts = []
            for i, meta in enumerate(post_meta):
                self._log(f"Fetching {i+1}/{len(post_meta)}: {meta['url']}")
                resp = self._safe_fetch(meta['url'])
                if not resp:
                    continue
                post = self._extract_article(meta['url'], resp.text)
                if post:
                    post.tags = meta['tags']
                    # Use the slug from the URL path if available
                    path = urlparse(meta['url']).path.strip('/')
                    if path:
                        post.slug = path.split('/')[-1]
                    # Override date from archive if we didn't get one from the page
                    if not post.published_at and meta['date_str']:
                        post.published_at = _parse_date(meta['date_str'])
                    posts.append(post)

            return posts if posts else None

        return None

    # ----- Strategy: Sitemap -----

    def _try_sitemap(self) -> Optional[List[ExtractedPost]]:
        """Parse sitemap.xml for post URLs."""
        sitemap_urls = [
            f"{self.url}/sitemap.xml",
            f"{self.url}/sitemap_index.xml",
            f"{self.url}/post-sitemap.xml",
        ]

        post_urls = []
        for sitemap_url in sitemap_urls:
            resp = self._safe_fetch(sitemap_url)
            if resp and resp.status_code == 200:
                urls = self._parse_sitemap(resp.text)
                if urls:
                    post_urls.extend(urls)
                    break

        if not post_urls:
            return None

        # Filter to likely post URLs (skip pages like /about, /contact)
        post_urls = self._filter_post_urls(post_urls)
        self._log(f"Found {len(post_urls)} URLs in sitemap")

        return self._fetch_and_extract(post_urls)

    def _parse_sitemap(self, xml_text: str) -> List[str]:
        """Parse sitemap XML and return URLs."""
        soup = BeautifulSoup(xml_text, 'lxml-xml')
        urls = []

        # Check for sitemap index (contains other sitemaps)
        sitemaps = soup.find_all('sitemap')
        if sitemaps:
            for sm in sitemaps:
                loc = sm.find('loc')
                if loc and loc.text:
                    # Fetch sub-sitemap
                    resp = self._safe_fetch(loc.text.strip())
                    if resp:
                        urls.extend(self._parse_sitemap(resp.text))
            return urls

        # Regular sitemap
        for url_tag in soup.find_all('url'):
            loc = url_tag.find('loc')
            if loc and loc.text:
                urls.append(loc.text.strip())

        return urls

    def _filter_post_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to likely blog posts."""
        skip_patterns = (
            '/tag/', '/category/', '/author/', '/page/',
            '/about', '/contact', '/privacy', '/terms',
            '/feed', '/sitemap', '/wp-content/', '/wp-admin/',
        )
        parsed_base = urlparse(self.url)
        filtered = []
        for url in urls:
            parsed = urlparse(url)
            path = parsed.path.rstrip('/')
            # Must be on the same domain
            if parsed.netloc != parsed_base.netloc:
                continue
            # Skip root
            if not path or path == '/':
                continue
            # Skip common non-post paths
            if any(pat in path.lower() for pat in skip_patterns):
                continue
            # Posts usually have a deeper path
            if path.count('/') >= 1:
                filtered.append(url)
        return filtered

    def _fetch_and_extract(self, urls: List[str]) -> List[ExtractedPost]:
        """Fetch each URL and extract article content."""
        posts = []
        for i, url in enumerate(urls):
            self._log(f"Fetching {i+1}/{len(urls)}: {url}")
            resp = self._safe_fetch(url)
            if not resp:
                continue
            post = self._extract_article(url, resp.text)
            if post:
                posts.append(post)
        return posts if posts else None

    # ----- Strategy: WordPress API -----

    def _try_wp_api(self) -> Optional[List[ExtractedPost]]:
        """Try WordPress REST API."""
        api_url = f"{self.url}/wp-json/wp/v2/posts"
        posts = []
        page = 1

        while True:
            resp = self._safe_fetch(f"{api_url}?per_page=100&page={page}&orderby=date&order=asc")
            if not resp or resp.status_code != 200:
                break

            data = resp.json()
            if not data:
                break

            for item in data:
                title = BeautifulSoup(item.get('title', {}).get('rendered', ''), 'html.parser').get_text()
                content = item.get('content', {}).get('rendered', '')
                link = item.get('link', '')
                slug = item.get('slug', _slugify(title))
                date = item.get('date')

                if title and content:
                    posts.append(ExtractedPost(
                        title=title,
                        url=link,
                        content_html=content,
                        slug=slug,
                        published_at=_parse_date(date),
                    ))

            # Check for more pages
            total_pages = int(resp.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break
            page += 1

        return posts if posts else None

    # ----- Strategy: Archive page -----

    def _try_archive(self) -> Optional[List[ExtractedPost]]:
        """Scrape post links from the blog's main/archive pages."""
        # Try common archive patterns
        archive_urls = [
            self.url,
            f"{self.url}/archive",
            f"{self.url}/archives",
            f"{self.url}/blog",
            f"{self.url}/posts",
            f"{self.url}/all",
        ]

        post_links = set()
        for archive_url in archive_urls:
            resp = self._safe_fetch(archive_url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, 'lxml')

            # Find all links that look like blog posts
            for link in soup.find_all('a', href=True):
                href = urljoin(archive_url, link['href'])
                parsed = urlparse(href)
                path = parsed.path.rstrip('/')

                if not path or path == '/':
                    continue
                if parsed.netloc != urlparse(self.url).netloc:
                    continue

                # Heuristic: posts tend to have longer paths
                segments = [s for s in path.split('/') if s]
                if len(segments) >= 2 or (len(segments) == 1 and len(segments[0]) > 10):
                    post_links.add(href)

            if post_links:
                break

        post_links = list(self._filter_post_urls(list(post_links)))
        if not post_links:
            return None

        self._log(f"Found {len(post_links)} post links on archive page")
        return self._fetch_and_extract(post_links)

    # ----- Strategy: Wayback Machine -----

    def _try_wayback(self) -> Optional[List[ExtractedPost]]:
        """Use Wayback Machine CDX API to find archived posts."""
        parsed = urlparse(self.url)
        domain = parsed.netloc

        cdx_url = (
            f"https://web.archive.org/cdx/search/cdx"
            f"?url={domain}/*&output=json&fl=timestamp,original,statuscode"
            f"&filter=statuscode:200&filter=mimetype:text/html"
            f"&collapse=urlkey&limit=500"
        )

        resp = self._safe_fetch(cdx_url)
        if not resp:
            return None

        data = resp.json()
        if len(data) < 2:  # First row is headers
            return None

        # Build wayback URLs
        post_urls = []
        seen = set()
        for row in data[1:]:
            timestamp, original_url, status = row
            if original_url in seen:
                continue
            seen.add(original_url)

            # Filter to likely posts
            parsed_url = urlparse(original_url)
            path = parsed_url.path.rstrip('/')
            if not path or path == '/':
                continue

            wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
            post_urls.append((original_url, wayback_url))

        post_urls = [(orig, wb) for orig, wb in post_urls
                     if orig in self._filter_post_urls([orig])]

        if not post_urls:
            return None

        self._log(f"Found {len(post_urls)} archived URLs")

        posts = []
        for orig_url, wayback_url in post_urls:
            self._log(f"Fetching from Wayback: {orig_url}")
            resp = self._safe_fetch(wayback_url)
            if not resp:
                continue
            post = self._extract_article(orig_url, resp.text)
            if post:
                posts.append(post)

        return posts if posts else None


class IllichExtractor:
    """Extract chapters from henryzoo.com/illich books."""

    BASE_URL = "https://henryzoo.com"
    HEADERS = {
        'User-Agent': 'Replay/0.1 (blog archiver; +https://replay.pub)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    def __init__(self, book_url: str, verbose: bool = False):
        """
        Initialize with a book URL.

        Args:
            book_url: URL to book index, e.g. https://henryzoo.com/illich/celebration-of-awareness/
        """
        self.book_url = book_url.rstrip('/')
        self.verbose = verbose
        self.client = httpx.Client(
            headers=self.HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [illich] {msg}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
    )
    def _fetch(self, url: str) -> httpx.Response:
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp

    def _safe_fetch(self, url: str) -> Optional[httpx.Response]:
        try:
            return self._fetch(url)
        except Exception as e:
            self._log(f"Failed to fetch {url}: {e}")
            return None

    def extract(self) -> List[ExtractedPost]:
        """Extract all chapters from the book as posts."""
        self._log(f"Fetching book index: {self.book_url}")
        resp = self._safe_fetch(self.book_url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, 'lxml')

        # Extract book name from the URL path (last segment)
        # e.g., /illich/celebration-of-awareness/ -> celebration-of-awareness
        path_segments = [s for s in self.book_url.split('/') if s]
        book_slug = path_segments[-1] if path_segments else None

        # Convert slug to title case: celebration-of-awareness -> Celebration of Awareness
        book_name = None
        if book_slug:
            book_name = ' '.join(word.capitalize() for word in book_slug.split('-'))

        self._log(f"Book: {book_name}")

        # Find all chapter links - they follow pattern /illich/slug
        chapter_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match /illich/something but not /illich/something/something (book indexes)
            if href.startswith('/illich/') and href.count('/') == 2:
                full_url = urljoin(self.BASE_URL, href)
                title = link.get_text(strip=True)
                if title and full_url not in [c['url'] for c in chapter_links]:
                    chapter_links.append({'url': full_url, 'title': title})

        # Filter out navigation links (Back to archive, etc.)
        chapter_links = [c for c in chapter_links if not c['title'].startswith('←')]

        self._log(f"Found {len(chapter_links)} chapters")

        posts = []
        for i, chapter in enumerate(chapter_links):
            self._log(f"Fetching chapter {i+1}/{len(chapter_links)}: {chapter['title']}")
            resp = self._safe_fetch(chapter['url'])
            if not resp:
                continue

            post = self._extract_chapter(chapter['url'], resp.text, book_name)
            if post:
                # Use the chapter title from the index if extraction gave a bad title
                if not post.title or post.title.startswith('1.') or len(post.title) > 100:
                    post.title = chapter['title']
                # Store chapter order for sorting
                post._chapter_order = i
                posts.append(post)

        # Sort by chapter order (as they appear in the book index)
        posts.sort(key=lambda p: getattr(p, '_chapter_order', 999))

        return posts

    def _extract_chapter(self, url: str, html: str, book_name: Optional[str]) -> Optional[ExtractedPost]:
        """Extract chapter content from HTML."""
        soup = BeautifulSoup(html, 'lxml')

        # Extract title - prefer h1, then h2, then title tag
        title = None
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text(strip=True)
            # Skip if it's just the site name
            if h1_text and h1_text.lower() not in ('henry\'s zoo', 'henrys zoo', 'ivan illich'):
                title = h1_text
        if not title:
            h2 = soup.find('h2')
            if h2:
                title = h2.get_text(strip=True)
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True).split('|')[0].strip()

        if not title:
            return None

        # Extract date - look for common patterns
        published_at = None
        # Try meta tags
        for prop in ('article:published_time', 'datePublished', 'date'):
            meta = soup.find('meta', attrs={'property': prop}) or soup.find('meta', attrs={'name': prop})
            if meta and meta.get('content'):
                published_at = _parse_date(meta['content'])
                if published_at:
                    break

        # Try to find date in text (e.g., "January 3rd, 1971")
        if not published_at:
            # Look for date patterns in the first few paragraphs
            date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}', re.IGNORECASE)
            text = soup.get_text()[:2000]
            match = date_pattern.search(text)
            if match:
                date_str = match.group(0).replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                published_at = _parse_date(date_str)

        # Extract main content using readability
        try:
            doc = Document(html, url=url)
            content_html = doc.summary()
        except Exception:
            # Fallback: find main content area
            main = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main:
                content_html = str(main)
            else:
                return None

        if not content_html or len(content_html) < 100:
            return None

        # Generate slug from URL
        slug = url.rstrip('/').split('/')[-1]

        # Tag with book name if available
        tags = []
        if book_name:
            tags.append(_slugify(book_name))

        return ExtractedPost(
            title=title,
            url=url,
            content_html=content_html,
            slug=slug,
            published_at=published_at,
            tags=tags,
        )
