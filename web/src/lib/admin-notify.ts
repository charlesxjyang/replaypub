export async function sendAdminNotification(
  type: 'subscription' | 'request',
  details: Record<string, string | number | null | undefined>
) {
  const adminEmail = process.env.ADMIN_EMAIL
  const resendKey = process.env.RESEND_API_KEY
  const fromEmail = process.env.FROM_EMAIL

  if (!adminEmail || !resendKey || !fromEmail) {
    console.warn('Admin notification skipped: missing ADMIN_EMAIL, RESEND_API_KEY, or FROM_EMAIL')
    return
  }

  const subject =
    type === 'subscription'
      ? `New subscription: ${details.feedName ?? 'unknown feed'}`
      : `Blog request: ${details.url ?? 'unknown URL'}`

  const lines = Object.entries(details)
    .filter(([, v]) => v != null)
    .map(([k, v]) => `<strong>${k}:</strong> ${v}`)
    .join('<br>')

  const html = `
<div style="font-family: sans-serif; font-size: 14px; color: #333;">
  <p style="margin: 0 0 12px 0;">New <strong>${type}</strong> on Replay:</p>
  <div style="background: #f5f5f5; padding: 12px; border-radius: 6px;">${lines}</div>
</div>`

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${resendKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from: fromEmail, to: adminEmail, subject, html }),
    })

    if (!res.ok) {
      console.error('Admin notification failed:', await res.text())
    }
  } catch (err) {
    console.error('Admin notification error:', err)
  }
}
