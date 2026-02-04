"""Tests for scraper.clean module."""

import pytest

from scraper.clean import HTMLCleaner


@pytest.fixture
def cleaner():
    return HTMLCleaner("https://example.com", verbose=False)


class TestScriptRemoval:
    def test_scripts_removed(self, cleaner):
        html = '<p>Hello</p><script>alert("xss")</script><p>World</p>'
        result = cleaner.clean(html)
        assert '<script>' not in result['html']
        assert 'alert' not in result['html']
        assert 'Hello' in result['text']
        assert 'World' in result['text']

    def test_styles_removed(self, cleaner):
        html = '<style>.foo{color:red}</style><p>Content</p>'
        result = cleaner.clean(html)
        assert '<style>' not in result['html']

    def test_iframes_removed(self, cleaner):
        html = '<p>Before</p><iframe src="https://evil.com"></iframe><p>After</p>'
        result = cleaner.clean(html)
        assert '<iframe' not in result['html']

    def test_nav_removed(self, cleaner):
        html = '<nav><a href="/">Home</a></nav><p>Article content</p>'
        result = cleaner.clean(html)
        assert '<nav>' not in result['html']


class TestURLResolution:
    def test_relative_links_resolved(self, cleaner):
        html = '<a href="/about">About</a>'
        result = cleaner.clean(html)
        assert 'https://example.com/about' in result['html']

    def test_absolute_links_unchanged(self, cleaner):
        html = '<a href="https://other.com/page">Other</a>'
        result = cleaner.clean(html)
        assert 'https://other.com/page' in result['html']

    def test_relative_images_resolved(self, cleaner):
        html = '<img src="/img/photo.jpg" alt="Photo">'
        result = cleaner.clean(html)
        assert 'https://example.com/img/photo.jpg' in result['html']


class TestExcerptGeneration:
    def test_excerpt_length(self, cleaner):
        html = '<p>' + 'Word ' * 100 + '</p>'
        result = cleaner.clean(html)
        assert len(result['excerpt']) <= 250  # 200 + room for word boundary

    def test_excerpt_sentence_boundary(self, cleaner):
        html = '<p>First sentence here. Second sentence here. Third sentence that goes on.</p>'
        result = cleaner.clean(html)
        assert result['excerpt'].endswith('.')

    def test_short_content_no_ellipsis(self, cleaner):
        html = '<p>Short.</p>'
        result = cleaner.clean(html)
        assert result['excerpt'] == 'Short.'


class TestWordCount:
    def test_word_count(self, cleaner):
        html = '<p>One two three four five</p>'
        result = cleaner.clean(html)
        assert result['word_count'] == 5

    def test_reading_time(self, cleaner):
        # 500 words ≈ 2 min at 250 wpm
        html = '<p>' + 'word ' * 500 + '</p>'
        result = cleaner.clean(html)
        assert result['reading_time_minutes'] == 2

    def test_reading_time_minimum_one(self, cleaner):
        html = '<p>Short</p>'
        result = cleaner.clean(html)
        assert result['reading_time_minutes'] >= 1


class TestImageCollection:
    def test_images_collected(self, cleaner):
        html = '<img src="https://example.com/photo.jpg" alt="Photo"><p>Text</p>'
        result = cleaner.clean(html)
        assert len(result['images']) == 1
        assert result['images'][0]['src'] == 'https://example.com/photo.jpg'
        assert result['images'][0]['alt'] == 'Photo'

    def test_data_uris_excluded(self, cleaner):
        html = '<img src="data:image/gif;base64,R0lGODlhAQ" alt="pixel"><p>Text</p>'
        result = cleaner.clean(html)
        assert len(result['images']) == 0


class TestReturnKeys:
    def test_all_keys_present(self, cleaner):
        html = '<p>Test content</p>'
        result = cleaner.clean(html)
        assert set(result.keys()) == {'html', 'text', 'excerpt', 'word_count', 'reading_time_minutes', 'images'}
