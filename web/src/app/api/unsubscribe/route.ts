import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(request: Request) {
  const { subscription_id } = await request.json()

  if (!subscription_id) {
    return NextResponse.json({ error: 'Missing subscription_id' }, { status: 400 })
  }

  // Use service key for server-side operations
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  const { error } = await supabase
    .from('subscriptions')
    .delete()
    .eq('id', subscription_id)

  if (error) {
    return NextResponse.json({ error: 'Failed to unsubscribe' }, { status: 500 })
  }

  return NextResponse.json({ ok: true })
}
