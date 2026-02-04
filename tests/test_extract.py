"""Tests for scraper.extract module."""

import json
from unittest.mock import MagicMock, patch

import pytest
import httpx

from scraper.extract import BlogExtractor, ExtractedPost, _slugify, _parse_date


class TestExtractedPost:
    def test_to_dict_has_required_keys(self):
        post = ExtractedPost(
            title="Test Post",
            url="https://example.com/test",
            content_html="<p>Hello</p>",
            slug="test-post",
            published_at="2023-01-15T00:00:00",
        )
        d = post.to_dict()
        assert set(d.keys()) == {'title', 'url', 'content_html', 'slug', 'published_at', 'tags'}
        assert d['title'] == "Test Post"
        assert d['url'] == "https://example.com/test"
        assert d['tags'] == []

    def test_to_dict_nullable_published_at(self):
        post = ExtractedPost(
            title="No Date",
            url="https://example.com/no-date",
            content_html="<p>Content</p>",
            slug="no-date",
        )
        d = post.to_dict()
        assert d['published_at'] is None


class TestSlugify:
    def test_basic(self):
        assert _slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert _slugify("What's up? (Part 2)") == "whats-up-part-2"

    def test_truncation(self):
        long_title = "A" * 100
        assert len(_slugify(long_title)) <= 80


class TestParseDate:
    def test_iso_format(self):
        result = _parse_date("2023-01-15T10:30:00")
        assert result == "2023-01-15T10:30:00"

    def test_date_only(self):
        result = _parse_date("2023-01-15")
        assert "2023-01-15" in result

    def test_human_format(self):
        result = _parse_date("January 15, 2023")
        assert "2023" in result

    def test_none(self):
        assert _parse_date(None) is None

    def test_unparseable(self):
        result = _parse_date("not a date")
        assert result == "not a date"


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/post-one</loc></url>
    <url><loc>https://example.com/post-two</loc></url>
    <url><loc>https://example.com/about</loc></url>
</urlset>"""

WP_API_RESPONSE = [
    {
        "title": {"rendered": "First Post"},
        "content": {"rendered": "<p>Content of first post, long enough to pass the length check for readability extraction minimum.</p>"},
        "link": "https://example.com/first-post",
        "slug": "first-post",
        "date": "2023-01-01T00:00:00",
    },
    {
        "title": {"rendered": "Second Post"},
        "content": {"rendered": "<p>Content of second post, also long enough to pass the length check for readability extraction.</p>"},
        "link": "https://example.com/second-post",
        "slug": "second-post",
        "date": "2023-02-01T00:00:00",
    },
]


class TestBlogExtractorSitemap:
    @patch.object(BlogExtractor, '_safe_fetch')
    @patch.object(BlogExtractor, '_extract_article')
    def test_sitemap_parses_urls(self, mock_extract, mock_fetch):
        # Sitemap response
        sitemap_resp = MagicMock()
        sitemap_resp.status_code = 200
        sitemap_resp.text = SITEMAP_XML

        # Post responses
        post_resp = MagicMock()
        post_resp.text = "<html><body><p>Post content</p></body></html>"

        def fetch_side_effect(url):
            if 'sitemap' in url:
                return sitemap_resp
            if '/about' in url:
                return post_resp
            return post_resp

        mock_fetch.side_effect = fetch_side_effect

        mock_extract.side_effect = [
            ExtractedPost("Post One", "https://example.com/post-one", "<p>One</p>", "post-one", "2023-01-01"),
            ExtractedPost("Post Two", "https://example.com/post-two", "<p>Two</p>", "post-two", "2023-02-01"),
        ]

        extractor = BlogExtractor("https://example.com")
        posts = extractor._try_sitemap()

        assert posts is not None
        # /about should be filtered out, but extract_article is called for post URLs
        assert len(posts) == 2


class TestBlogExtractorWPAPI:
    @patch.object(BlogExtractor, '_safe_fetch')
    def test_wp_api_maps_fields(self, mock_fetch):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = WP_API_RESPONSE
        resp.headers = {'X-WP-TotalPages': '1'}

        mock_fetch.return_value = resp

        extractor = BlogExtractor("https://example.com")
        posts = extractor._try_wp_api()

        assert posts is not None
        assert len(posts) == 2
        assert posts[0].title == "First Post"
        assert posts[0].slug == "first-post"
        assert posts[1].title == "Second Post"

    @patch.object(BlogExtractor, '_safe_fetch')
    def test_wp_api_returns_none_on_404(self, mock_fetch):
        resp = MagicMock()
        resp.status_code = 404
        mock_fetch.return_value = resp

        extractor = BlogExtractor("https://example.com")
        posts = extractor._try_wp_api()

        assert posts is None


class TestBlogExtractorSorting:
    def test_posts_sorted_oldest_first(self):
        posts = [
            ExtractedPost("C", "https://example.com/c", "<p>C</p>", "c", "2023-03-01"),
            ExtractedPost("A", "https://example.com/a", "<p>A</p>", "a", "2023-01-01"),
            ExtractedPost("B", "https://example.com/b", "<p>B</p>", "b", "2023-02-01"),
        ]
        posts.sort(key=lambda p: (p.published_at or '0000', p.url))
        assert [p.title for p in posts] == ["A", "B", "C"]
