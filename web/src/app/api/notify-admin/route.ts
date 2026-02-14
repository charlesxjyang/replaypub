import { NextRequest, NextResponse } from 'next/server'
import { sendAdminNotification } from '@/lib/admin-notify'

export async function POST(request: NextRequest) {
  try {
    const { type, details } = await request.json()

    if (!type || !details) {
      return NextResponse.json({ error: 'Missing type or details' }, { status: 400 })
    }

    await sendAdminNotification(type, details)
    return NextResponse.json({ success: true })
  } catch (err) {
    console.error('Notify admin route error:', err)
    return NextResponse.json({ error: 'Failed to notify' }, { status: 500 })
  }
}
