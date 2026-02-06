import { createClient as createServiceClient } from '@supabase/supabase-js'
import { createClient as createSSRClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const feedId = searchParams.get('feed_id')
  const blogId = searchParams.get('blog_id')
  const frequency = parseInt(searchParams.get('frequency') ?? '7', 10)
  const timezone = searchParams.get('timezone') ?? 'UTC'

  if (!feedId || !blogId) {
    return NextResponse.redirect(`${origin}/?error=invalid_link`)
  }

  // Exchange auth code for session (sets browser cookies)
  if (code) {
    const supabaseSSR = await createSSRClient()
    const { error } = await supabaseSSR.auth.exchangeCodeForSession(code)
    if (error) {
      console.error('Code exchange error:', error)
    }
  }

  // Use service client for subscription creation
  const supabase = createServiceClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  try {
    // Get user from SSR client (now has session from code exchange)
    const supabaseSSR = await createSSRClient()
    const { data: { user } } = await supabaseSSR.auth.getUser()

    if (!user) {
      return NextResponse.redirect(`${origin}/?error=auth`)
    }

    // Ensure subscriber row exists
    await supabase.from('subscribers').upsert({
      id: user.id,
      email: user.email!.toLowerCase(),
      is_confirmed: true,
      confirmed_at: new Date().toISOString(),
    }, { onConflict: 'id' })

    // Check if already subscribed
    const { data: existing } = await supabase
      .from('subscriptions')
      .select('id')
      .eq('subscriber_id', user.id)
      .eq('feed_id', feedId)
      .maybeSingle()

    if (existing) {
      return NextResponse.redirect(`${origin}/embed/success?already=1`)
    }

    // Create subscription
    const { error: subError } = await supabase.from('subscriptions').insert({
      subscriber_id: user.id,
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
        return NextResponse.redirect(`${origin}/embed/success?already=1`)
      }
      return NextResponse.redirect(`${origin}/?error=subscription_failed`)
    }

    // Get feed name for the success page
    const { data: feed } = await supabase
      .from('feeds')
      .select('name')
      .eq('id', feedId)
      .single()

    const feedName = feed?.name ? encodeURIComponent(feed.name) : ''
    return NextResponse.redirect(`${origin}/embed/success?feed=${feedName}`)
  } catch (err) {
    console.error('Embed confirm error:', err)
    return NextResponse.redirect(`${origin}/?error=subscription_failed`)
  }
}
