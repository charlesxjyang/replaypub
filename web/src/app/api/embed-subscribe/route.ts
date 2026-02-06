import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { email, feed_id, blog_id, frequency, timezone, feed_name } = await request.json()

  if (!email || !feed_id || !blog_id) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  // Check if already subscribed
  const { data: subscriber } = await supabase
    .from('subscribers')
    .select('id')
    .eq('email', email.toLowerCase())
    .maybeSingle()

  if (subscriber) {
    const { data: existing } = await supabase
      .from('subscriptions')
      .select('id')
      .eq('subscriber_id', subscriber.id)
      .eq('feed_id', feed_id)
      .eq('is_active', true)
      .maybeSingle()

    if (existing) {
      return NextResponse.json({ status: 'already_subscribed' })
    }
  }

  // Build the confirm page URL
  const confirmParams = new URLSearchParams({
    feed_id,
    blog_id,
    frequency: String(frequency || 7),
    preferred_hour: '9',
    timezone: timezone || 'UTC',
  })

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://replaypub.vercel.app'
  const redirectTo = `${appUrl}/auth/callback?next=${encodeURIComponent(`/subscribe/confirm?${confirmParams.toString()}`)}`

  // Generate magic link via admin API (bypasses PKCE)
  const { data: linkData, error: linkError } = await supabase.auth.admin.generateLink({
    type: 'magiclink',
    email,
    options: { redirectTo },
  })

  if (linkError || !linkData) {
    console.error('generateLink error:', linkError)
    return NextResponse.json({ error: 'Failed to generate link' }, { status: 500 })
  }

  // The admin API returns the full verification URL
  // We need to extract the token_hash and build the proper link
  const verificationUrl = linkData.properties?.action_link
  if (!verificationUrl) {
    console.error('No action_link in response:', linkData)
    return NextResponse.json({ error: 'Failed to generate link' }, { status: 500 })
  }

  // Send the magic link email via Resend
  const resendKey = process.env.RESEND_API_KEY
  if (!resendKey) {
    return NextResponse.json({ error: 'Email not configured' }, { status: 500 })
  }

  const displayName = feed_name || 'this feed'

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${resendKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: process.env.FROM_EMAIL || 'posts@replay.pub',
      to: email,
      subject: `Confirm your subscription to ${displayName}`,
      html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin: 0; padding: 0; background-color: #f9fafb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f9fafb;">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="480" style="background-color: #ffffff; border-radius: 8px;">
          <tr>
            <td style="padding: 40px 32px; text-align: center;">
              <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 600; color: #111827;">
                Confirm your subscription
              </h1>
              <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Click the button below to start receiving posts from <strong>${displayName}</strong>.
              </p>
              <a href="${verificationUrl}" style="display: inline-block; background-color: #111827; color: #ffffff; font-size: 15px; font-weight: 500; text-decoration: none; padding: 12px 32px; border-radius: 6px;">
                Confirm &amp; subscribe
              </a>
              <p style="margin: 24px 0 0 0; font-size: 13px; color: #9ca3af;">
                If you didn't request this, you can ignore this email.
              </p>
            </td>
          </tr>
        </table>
        <p style="margin: 16px 0 0 0; font-size: 12px; color: #9ca3af;">
          Replay — Great blogs, delivered over time
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
      `,
    }),
  })

  if (!res.ok) {
    const error = await res.text()
    console.error('Resend error:', error)
    return NextResponse.json({ error: 'Failed to send email' }, { status: 500 })
  }

  return NextResponse.json({ status: 'sent' })
}
