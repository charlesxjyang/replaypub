import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'
import { createHmac } from 'crypto'

function signParams(params: Record<string, string>, secret: string): string {
  const payload = Object.keys(params).sort().map(k => `${k}=${params[k]}`).join('&')
  return createHmac('sha256', secret).update(payload).digest('hex')
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const email = searchParams.get('email')
  const feedId = searchParams.get('feed_id')
  const blogId = searchParams.get('blog_id')
  const frequency = parseInt(searchParams.get('frequency') ?? '7', 10)
  const timezone = searchParams.get('timezone') ?? 'UTC'
  const ts = searchParams.get('ts')
  const sig = searchParams.get('sig')

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://replaypub.vercel.app'

  if (!email || !feedId || !blogId || !ts || !sig) {
    return NextResponse.redirect(`${appUrl}/?error=invalid_link`)
  }

  // Verify HMAC signature
  const secret = process.env.SUPABASE_SERVICE_KEY!
  const params: Record<string, string> = {
    email,
    feed_id: feedId,
    blog_id: blogId,
    frequency: String(frequency),
    timezone,
    ts,
  }

  const expectedSig = signParams(params, secret)
  if (sig !== expectedSig) {
    return NextResponse.redirect(`${appUrl}/?error=invalid_link`)
  }

  // Check expiry (24 hours)
  const linkAge = Math.floor(Date.now() / 1000) - parseInt(ts, 10)
  if (linkAge > 86400) {
    return NextResponse.redirect(`${appUrl}/?error=link_expired`)
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  try {
    // Get or create auth user
    let userId: string

    // Check if user already exists via subscribers table
    const { data: existingSub } = await supabase
      .from('subscribers')
      .select('id')
      .eq('email', email.toLowerCase())
      .maybeSingle()

    if (existingSub) {
      userId = existingSub.id
    } else {
      // Create new auth user (triggers subscriber creation via DB trigger)
      const { data: newUser, error: createError } = await supabase.auth.admin.createUser({
        email,
        email_confirm: true,
      })
      if (createError || !newUser.user) {
        console.error('Failed to create user:', createError)
        return NextResponse.redirect(`${appUrl}/?error=subscription_failed`)
      }
      userId = newUser.user.id
    }

    // Ensure subscriber row exists (trigger might not have fired yet)
    await supabase.from('subscribers').upsert({
      id: userId,
      email: email.toLowerCase(),
      is_confirmed: true,
      confirmed_at: new Date().toISOString(),
    }, { onConflict: 'id' })

    // Check if already subscribed
    const { data: existing } = await supabase
      .from('subscriptions')
      .select('id')
      .eq('subscriber_id', userId)
      .eq('feed_id', feedId)
      .maybeSingle()

    if (existing) {
      return NextResponse.redirect(`${appUrl}/embed/success?already=1`)
    }

    // Create subscription
    const { error: subError } = await supabase.from('subscriptions').insert({
      subscriber_id: userId,
      blog_id: blogId,
      feed_id: feedId,
      frequency_days: frequency,
      preferred_hour: 9,
      timezone,
      current_post_index: 0,
      next_send_at: new Date().toISOString(),
      is_active: true,
    })

    if (subError) {
      console.error('Subscription error:', subError)
      if (subError.code === '23505') {
        return NextResponse.redirect(`${appUrl}/embed/success?already=1`)
      }
      return NextResponse.redirect(`${appUrl}/?error=subscription_failed`)
    }

    // Get feed name for the success page
    const { data: feed } = await supabase
      .from('feeds')
      .select('name')
      .eq('id', feedId)
      .single()

    const feedName = feed?.name ? encodeURIComponent(feed.name) : ''
    return NextResponse.redirect(`${appUrl}/embed/success?feed=${feedName}`)
  } catch (err) {
    console.error('Embed confirm error:', err)
    return NextResponse.redirect(`${appUrl}/?error=subscription_failed`)
  }
}
