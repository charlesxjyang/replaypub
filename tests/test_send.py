"""Tests for drip.send module."""

from unittest.mock import MagicMock, patch

import pytest

from drip.send import render_email, send_email, mark_sent


@pytest.fixture
def sample_item():
    return {
        'subscription_id': '550e8400-e29b-41d4-a716-446655440000',
        'subscriber_email': 'test@example.com',
        'subscriber_name': 'Test User',
        'blog_name': 'Test Blog',
        'blog_slug': 'test-blog',
        'post_id': '660e8400-e29b-41d4-a716-446655440000',
        'post_title': 'My Test Post',
        'post_content_html': '<p>This is the post content.</p>',
        'post_original_url': 'https://example.com/my-test-post',
        'post_index': 5,
        'total_posts': 20,
    }


class TestRenderEmail:
    def test_placeholders_replaced(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert '{{' not in html
        assert '}}' not in html

    def test_blog_name_present(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert 'Test Blog' in html

    def test_post_title_present(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert 'My Test Post' in html

    def test_post_content_present(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert 'This is the post content.' in html

    def test_footer_present(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert 'Replay' in html

    def test_unsubscribe_url(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        expected = f"https://replay.pub/unsubscribe?sid={sample_item['subscription_id']}"
        assert expected in html

    def test_app_url(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        assert 'https://replay.pub' in html

    def test_post_url_in_title_link(self, sample_item):
        html = render_email(sample_item, 'https://replay.pub')
        expected_url = f'{sample_item["post_original_url"]}?utm_source=replay&utm_medium=email&utm_campaign=drip'
        assert f'href="{expected_url}"' in html


class TestSendEmail:
    @patch('drip.send.resend')
    def test_returns_message_id(self, mock_resend):
        mock_resend.Emails.send.return_value = {'id': 'msg_123'}

        result = send_email(
            'test@example.com', 'Test User', 'Subject',
            '<p>HTML</p>', 'from@example.com', 'reply@example.com'
        )

        assert result == 'msg_123'
        mock_resend.Emails.send.assert_called_once()

    @patch('drip.send.resend')
    def test_includes_list_unsubscribe_header(self, mock_resend):
        mock_resend.Emails.send.return_value = {'id': 'msg_123'}

        send_email(
            'test@example.com', None, 'Subject',
            '<p>HTML</p>', 'from@example.com', 'reply@example.com'
        )

        call_args = mock_resend.Emails.send.call_args[0][0]
        assert 'List-Unsubscribe' in call_args['headers']

    @patch('drip.send.resend')
    def test_returns_none_on_error(self, mock_resend):
        mock_resend.Emails.send.side_effect = Exception("API error")

        result = send_email(
            'test@example.com', None, 'Subject',
            '<p>HTML</p>', 'from@example.com', 'reply@example.com'
        )

        assert result is None


class TestMarkSent:
    def test_calls_rpc(self):
        mock_supabase = MagicMock()

        mark_sent(
            mock_supabase,
            '550e8400-e29b-41d4-a716-446655440000',
            '660e8400-e29b-41d4-a716-446655440000',
            'msg_123',
        )

        mock_supabase.rpc.assert_called_once_with('mark_subscription_sent', {
            'p_subscription_id': '550e8400-e29b-41d4-a716-446655440000',
            'p_post_id': '660e8400-e29b-41d4-a716-446655440000',
            'p_resend_message_id': 'msg_123',
        })
        mock_supabase.rpc.return_value.execute.assert_called_once()

    def test_handles_rpc_error(self):
        mock_supabase = MagicMock()
        mock_supabase.rpc.side_effect = Exception("DB error")

        # Should not raise
        mark_sent(
            mock_supabase,
            '550e8400-e29b-41d4-a716-446655440000',
            '660e8400-e29b-41d4-a716-446655440000',
            'msg_123',
        )
