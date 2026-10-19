"""Tests for the upload change-detection helpers in backstack."""

import pytest

from backstack import blog_changed, post_changed


def make_post(**overrides):
    post = {
        'blog_id': '550e8400-e29b-41d4-a716-446655440000',
        'title': 'Part One, §1: To man the world is twofold',
        'slug': 'part-one-1',
        'content_html': '<p>To man the world is twofold.</p>',
        'content_text': 'To man the world is twofold.',
        'excerpt': 'To man the world is twofold.',
        'original_url': 'https://example.com/i-and-thou.pdf',
        'published_at': '2026-09-20T00:00:00+00:00',
        'post_index': 1,
        'word_count': 102,
        'reading_time_minutes': 1,
        'tags': ['philosophy'],
    }
    post.update(overrides)
    return post


class TestPostChanged:
    def test_identical_rows_are_unchanged(self):
        assert post_changed(make_post(), make_post()) is False

    def test_missing_row_counts_as_changed(self):
        assert post_changed(make_post(), None) is True
        assert post_changed(make_post(), {}) is True

    @pytest.mark.parametrize('field,value', [
        ('title', 'A different title'),
        ('content_html', '<p>Rewritten body.</p>'),
        ('excerpt', 'Something else'),
        ('original_url', 'https://example.com/other'),
        ('word_count', 250),
        ('reading_time_minutes', 4),
    ])
    def test_field_edits_are_detected(self, field, value):
        assert post_changed(make_post(**{field: value}), make_post()) is True

    def test_null_and_empty_text_are_equivalent(self):
        # Postgres stores NULL where the uploader sends ''.
        incoming = make_post(content_text='', excerpt='')
        stored = make_post(content_text=None, excerpt=None)
        assert post_changed(incoming, stored) is False

    def test_surrounding_whitespace_is_ignored(self):
        assert post_changed(make_post(title='  Title  '), make_post(title='Title')) is False

    def test_equivalent_timestamps_do_not_trigger_a_write(self):
        incoming = make_post(published_at='2026-09-20T00:00:00Z')
        stored = make_post(published_at='2026-09-20T00:00:00+00:00')
        assert post_changed(incoming, stored) is False

    def test_different_instants_trigger_a_write(self):
        incoming = make_post(published_at='2026-09-21T00:00:00Z')
        assert post_changed(incoming, make_post()) is True

    def test_absent_timestamps_match(self):
        assert post_changed(make_post(published_at=None), make_post(published_at='')) is False

    def test_numeric_strings_match_integers(self):
        assert post_changed(make_post(word_count='102'), make_post()) is False

    def test_tag_changes_are_detected(self):
        assert post_changed(make_post(tags=['philosophy', 'religion']), make_post()) is True
        assert post_changed(make_post(tags=[]), make_post(tags=None)) is False


class TestBlogChanged:
    def make_blog(self, **overrides):
        blog = {
            'slug': 'martin-buber',
            'name': 'I and Thou',
            'url': 'https://example.com/i-and-thou.pdf',
            'author': 'Martin Buber',
            'author_email': None,
            'post_count': 61,
        }
        blog.update(overrides)
        return blog

    def test_identical_blog_is_unchanged(self):
        assert blog_changed(self.make_blog(), self.make_blog()) is False

    def test_new_blog_is_changed(self):
        assert blog_changed(self.make_blog(), None) is True

    def test_post_count_change_is_detected(self):
        assert blog_changed(self.make_blog(post_count=62), self.make_blog()) is True

    def test_description_is_not_compared(self):
        # upload never writes description, so a stored one must not force a write.
        stored = self.make_blog(description='A long description set via SQL.')
        assert blog_changed(self.make_blog(), stored) is False
