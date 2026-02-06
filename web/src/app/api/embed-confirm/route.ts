import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const tokenHash = searchParams.get('token_hash')
  const email = searchParams.get('email')
  const feedId = searchParams.get('feed_id')
  const blogId = searchParams.get('blog_id')
  const frequency = parseInt(searchParams.get('frequency') ?? '7', 10)
  const timezone = searchParams.get('timezone') ?? 'UTC'

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://replaypub.vercel.app'

  if (!tokenHash || !email || !feedId || !blogId) {
    return NextResponse.redirect(`${appUrl}/?error=invalid_link`)
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  try {
    // Verify the magic link token via Supabase
    const { error: verifyError } = await supabase.auth.verifyOtp({
      token_hash: tokenHash,
      type: 'magiclink',
    })

    if (verifyError) {
      console.error('Token verification error:', verifyError)
      return NextResponse.redirect(`${appUrl}/?error=invalid_link`)
    }

    // Get or create the subscriber
    let userId: string

    const { data: existingSub } = await supabase
      .from('subscribers')
      .select('id')
      .eq('email', email.toLowerCase())
      .maybeSingle()

    if (existingSub) {
      userId = existingSub.id
    } else {
      // User was created by generateLink, find them via auth
      const { data: { users } } = await supabase.auth.admin.listUsers()
      const authUser = users?.find(u => u.email === email.toLowerCase())
      if (!authUser) {
        return NextResponse.redirect(`${appUrl}/?error=subscription_failed`)
      }
      userId = authUser.id
    }

    // Ensure subscriber row exists
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
