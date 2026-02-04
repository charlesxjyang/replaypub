import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { email, feed_id } = await request.json()

  if (!email || !feed_id) {
    return NextResponse.json({ error: 'Missing email or feed_id' }, { status: 400 })
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  // Find subscriber by email
  const { data: subscriber } = await supabase
    .from('subscribers')
    .select('id')
    .eq('email', email.toLowerCase())
    .maybeSingle()

  if (!subscriber) {
    return NextResponse.json({ subscribed: false })
  }

  // Check if they have an active subscription to this feed
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('id')
    .eq('subscriber_id', subscriber.id)
    .eq('feed_id', feed_id)
    .eq('is_active', true)
    .maybeSingle()

  return NextResponse.json({ subscribed: !!subscription })
}
