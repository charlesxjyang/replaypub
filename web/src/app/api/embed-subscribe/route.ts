import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { email, feed_id, blog_id, frequency, timezone } = await request.json()

    if (!email || !feed_id || !blog_id) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )

    const normalEmail = email.toLowerCase()

    // Get or create user
    let userId: string

    const { data: existingSub } = await supabase
      .from('subscribers')
      .select('id')
      .eq('email', normalEmail)
      .maybeSingle()

    if (existingSub) {
      userId = existingSub.id

      // Check if already subscribed
      const { data: existing } = await supabase
        .from('subscriptions')
        .select('id')
        .eq('subscriber_id', userId)
        .eq('feed_id', feed_id)
        .maybeSingle()

      if (existing) {
        return NextResponse.json({ status: 'already_subscribed' })
      }
    } else {
      // Create auth user (triggers subscriber row via DB trigger)
      const { data: newUser, error: createError } = await supabase.auth.admin.createUser({
        email: normalEmail,
        email_confirm: true,
      })
      if (createError || !newUser.user) {
        console.error('Failed to create user:', createError)
        return NextResponse.json({ error: 'Failed to create account' }, { status: 500 })
      }
      userId = newUser.user.id
    }

    // Ensure subscriber row exists
    await supabase.from('subscribers').upsert({
      id: userId,
      email: normalEmail,
      is_confirmed: true,
      confirmed_at: new Date().toISOString(),
    }, { onConflict: 'id' })

    // Create subscription
    const { error: subError } = await supabase.from('subscriptions').insert({
      subscriber_id: userId,
      blog_id,
      feed_id,
      frequency_days: frequency || 7,
      preferred_hour: 9,
      timezone: timezone || 'UTC',
      current_post_index: 0,
      next_send_at: new Date().toISOString(),
      is_active: true,
    })

    if (subError) {
      console.error('Subscription error:', subError)
      if (subError.code === '23505') {
        return NextResponse.json({ status: 'already_subscribed' })
      }
      return NextResponse.json({ error: 'Failed to create subscription' }, { status: 500 })
    }

    return NextResponse.json({ status: 'subscribed' })
  } catch (err) {
    console.error('embed-subscribe error:', err)
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'Internal server error' },
      { status: 500 }
    )
  }
}
