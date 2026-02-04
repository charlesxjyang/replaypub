import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(request: Request) {
  const body = await request.json()
  const { type, data } = body

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  )

  const messageId = data?.email_id

  if (!messageId) {
    return NextResponse.json({ ok: true })
  }

  if (type === 'email.opened') {
    await supabase
      .from('email_log')
      .update({ opened_at: new Date().toISOString() })
      .eq('resend_message_id', messageId)
      .is('opened_at', null)
  }

  if (type === 'email.clicked') {
    await supabase
      .from('email_log')
      .update({ clicked_at: new Date().toISOString() })
      .eq('resend_message_id', messageId)
      .is('clicked_at', null)
  }

  return NextResponse.json({ ok: true })
}
