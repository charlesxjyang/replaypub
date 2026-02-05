"""Email rendering and sending for drip campaigns."""

import os
from pathlib import Path
from typing import Optional

import resend


# Load template at module level
_TEMPLATE_DIR = Path(__file__).parent.parent / 'templates'
_TEMPLATE_CACHE = None


def _get_template() -> str:
    """Load email template, with fallback inline template."""
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE

    template_path = _TEMPLATE_DIR / 'email.html'
    if template_path.exists():
        _TEMPLATE_CACHE = template_path.read_text()
        return _TEMPLATE_CACHE

    # Fallback inline template
    _TEMPLATE_CACHE = """<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:20px;background:#f9fafb;font-family:Georgia,serif;">
<div style="max-width:600px;margin:0 auto;background:#fff;padding:40px 32px;border-radius:8px;">
<p style="text-align:center;color:#9ca3af;font-size:13px;"><a href="{{post_url_utm}}" style="color:#9ca3af;text-decoration:none;">{{blog_name}}</a></p>
<h1 style="font-size:28px;line-height:1.3;"><a href="{{post_url_utm}}" style="color:#1a1a1a;text-decoration:none;">{{post_title}}</a></h1>
<hr style="border:none;border-top:1px solid #e5e7eb;">
<div style="font-size:16px;line-height:1.7;">{{post_content}}</div>
<hr style="border:none;border-top:1px solid #e5e7eb;">
<p style="text-align:center;color:#6b7280;font-size:13px;">{{progress_text}}</p>
<div style="background:#e5e7eb;border-radius:4px;height:6px;">
<div style="background:#2563eb;border-radius:4px;height:6px;width:{{progress_pct}}%;"></div>
</div>
</div>
<p style="text-align:center;font-size:12px;color:#9ca3af;padding:16px;">
Delivered by <a href="{{app_url}}" style="color:#9ca3af;">Replay</a>
&middot; <a href="{{unsubscribe_url}}" style="color:#9ca3af;">Unsubscribe</a>
</p>
</body>
</html>"""
    return _TEMPLATE_CACHE


def render_email(item: dict, app_url: str) -> str:
    """Render email HTML from a due subscription item.

    Args:
        item: Dict from get_due_subscriptions RPC with keys:
            subscription_id, subscriber_email, subscriber_name,
            blog_name, blog_slug, post_id, post_title,
            post_content_html, post_index, total_posts
        app_url: Base URL of the web app

    Returns:
        Rendered HTML string
    """
    template = _get_template()

    post_index = item['post_index']
    total_posts = item['total_posts']
    progress_pct = round((post_index / total_posts) * 100) if total_posts > 0 else 0

    unsubscribe_url = f"{app_url}/unsubscribe?sid={item['subscription_id']}"

    # Build UTM-tagged URL for the original post
    post_url = item.get('post_original_url', '')
    if post_url:
        separator = '&' if '?' in post_url else '?'
        post_url_utm = f"{post_url}{separator}utm_source=replay&utm_medium=email&utm_campaign=drip"
    else:
        post_url_utm = ''

    replacements = {
        '{{blog_name}}': item.get('blog_name', ''),
        '{{post_title}}': item.get('post_title', ''),
        '{{post_url}}': post_url,
        '{{post_url_utm}}': post_url_utm,
        '{{post_content}}': item.get('post_content_html', ''),
        '{{progress_text}}': f"Post {post_index} of {total_posts}",
        '{{progress_pct}}': str(progress_pct),
        '{{unsubscribe_url}}': unsubscribe_url,
        '{{app_url}}': app_url,
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


def send_email(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html: str,
    from_email: str,
    reply_to: str,
) -> Optional[str]:
    """Send an email via Resend API.

    Returns:
        Resend message ID on success, None on failure.
    """
    try:
        to_addr = f"{to_name} <{to_email}>" if to_name else to_email

        params = {
            'from': from_email,
            'to': [to_addr],
            'subject': subject,
            'html': html,
            'reply_to': reply_to,
            'headers': {
                'List-Unsubscribe': f'<mailto:{reply_to}?subject=unsubscribe>',
            },
        }

        result = resend.Emails.send(params)
        return result.get('id') if isinstance(result, dict) else getattr(result, 'id', None)
    except Exception as e:
        print(f"  [send] Failed to send to {to_email}: {e}")
        return None


def mark_sent(supabase, subscription_id: str, post_id: str, resend_message_id: str):
    """Mark a subscription as sent by calling Supabase RPC."""
    try:
        supabase.rpc('mark_subscription_sent', {
            'p_subscription_id': subscription_id,
            'p_post_id': post_id,
            'p_resend_message_id': resend_message_id,
        }).execute()
    except Exception as e:
        print(f"  [send] Failed to mark sent for {subscription_id}: {e}")
