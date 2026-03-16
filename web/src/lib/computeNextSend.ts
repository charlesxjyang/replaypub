/**
 * Compute the next send time for a subscription based on frequency, preferred day/hour, and timezone.
 * Returns an ISO string in UTC.
 */
export function computeNextSend(freqDays: number, day: number | null, hour: number, tz: string): string {
  const now = new Date()
  const next = new Date(now.getTime() + freqDays * 86400000)
  const localStr = next.toLocaleDateString('en-CA', { timeZone: tz }) // YYYY-MM-DD
  const snapped = new Date(`${localStr}T${String(hour).padStart(2, '0')}:00:00`)

  // If preferred_day set and frequency >= 7, advance to that weekday
  if (day !== null && freqDays >= 7) {
    while (snapped.getDay() !== day) {
      snapped.setDate(snapped.getDate() + 1)
    }
  }

  return snapped.toISOString()
}
