"""HTML cleaning and sanitization for email delivery."""

import re
from urllib.parse import urljoin
from typing import Dict, List, Optional

import bleach
from bs4 import BeautifulSoup
from premailer import Premailer


# Tags safe for email rendering
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code',
    'dd', 'del', 'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3',
    'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre',
    'q', 's', 'span', 'strong', 'sub', 'sup', 'table', 'tbody',
    'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul', 'figure',
    'figcaption', 'cite', 'mark', 'small',
]

ALLOWED_ATTRS = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height', 'title'],
    'td': ['colspan', 'rowspan', 'align', 'valign'],
    'th': ['colspan', 'rowspan', 'align', 'valign'],
    'ol': ['start', 'type'],
    'blockquote': ['cite'],
}

# Elements to remove entirely (including content)
STRIP_ELEMENTS = [
    'script', 'style', 'nav', 'iframe', 'form', 'input',
    'button', 'select', 'textarea', 'noscript', 'header',
    'footer', 'aside', 'svg', 'canvas', 'video', 'audio',
    'object', 'embed',
]


class HTMLCleaner:
    """Clean and sanitize HTML for email delivery."""

    def __init__(self, base_url: str, cdn_url: Optional[str] = None, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.cdn_url = cdn_url.rstrip('/') if cdn_url else None
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [clean] {msg}")

    def clean(self, html: str, title: Optional[str] = None) -> Dict:
        """Clean HTML for email delivery.

        Returns dict with: html, text, excerpt, word_count, reading_time_minutes, images
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements entirely
        for tag_name in STRIP_ELEMENTS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Fix relative URLs
        self._fix_urls(soup)

        # Collect image URLs before potential removal
        images = self._collect_images(soup)

        # Get the cleaned HTML string
        # Use body contents if present, otherwise use the whole soup
        body = soup.find('body')
        if body:
            cleaned_html = ''.join(str(child) for child in body.children)
        else:
            cleaned_html = str(soup)

        # Sanitize with bleach
        cleaned_html = bleach.clean(
            cleaned_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )

        # Inline CSS with premailer
        try:
            cleaned_html = Premailer(
                cleaned_html,
                remove_classes=True,
                strip_important=True,
                keep_style_tags=False,
                cssutils_logging_level='CRITICAL',
            ).transform()
            # Premailer wraps in <html><body>, extract just the body content
            pm_soup = BeautifulSoup(cleaned_html, 'lxml')
            pm_body = pm_soup.find('body')
            if pm_body:
                cleaned_html = ''.join(str(child) for child in pm_body.children)
        except Exception as e:
            self._log(f"Premailer failed (using unstyled): {e}")

        # Extract plain text
        text_soup = BeautifulSoup(cleaned_html, 'lxml')
        plain_text = text_soup.get_text(separator='\n', strip=True)

        # Generate excerpt
        excerpt = self._generate_excerpt(plain_text)

        # Calculate word count and reading time
        words = plain_text.split()
        word_count = len(words)
        reading_time = max(1, round(word_count / 250))

        self._log(f"Cleaned: {word_count} words, ~{reading_time} min read, {len(images)} images")

        return {
            'html': cleaned_html,
            'text': plain_text,
            'excerpt': excerpt,
            'word_count': word_count,
            'reading_time_minutes': reading_time,
            'images': images,
        }

    def _fix_urls(self, soup: BeautifulSoup):
        """Convert relative URLs to absolute."""
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            tag['href'] = urljoin(self.base_url + '/', href)
            # Open external links in new tab
            tag['target'] = '_blank'
            tag['rel'] = 'noopener noreferrer'

        for tag in soup.find_all('img', src=True):
            src = tag['src']
            if src.startswith(('http://', 'https://', 'data:')):
                continue
            tag['src'] = urljoin(self.base_url + '/', src)

    def _collect_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Collect image information from the HTML."""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('data:'):
                continue
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
            })
        return images

    def _generate_excerpt(self, text: str, max_length: int = 200) -> str:
        """Generate excerpt from plain text."""
        if not text:
            return ''
        # Take first chunk
        excerpt = text[:max_length + 50]
        # Try to break at a sentence boundary
        for end_char in ('.', '!', '?'):
            idx = excerpt.rfind(end_char, 0, max_length)
            if idx > 50:
                return excerpt[:idx + 1]
        # Fall back to word boundary
        if len(excerpt) > max_length:
            idx = excerpt.rfind(' ', 0, max_length)
            if idx > 50:
                return excerpt[:idx] + '...'
        return excerpt[:max_length] + ('...' if len(text) > max_length else '')
