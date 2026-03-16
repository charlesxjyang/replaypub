/**
 * Compute the next send time for a subscription based on frequency, preferred day/hour, and timezone.
 * Returns an ISO string in UTC.
 */
export function computeNextSend(freqDays: number, day: number | null, hour: number, tz: string): string {
  const now = new Date()

  // Get tomorrow+ date in the user's timezone
  const future = new Date(now.getTime() + freqDays * 86400000)
  const localDate = future.toLocaleDateString('en-CA', { timeZone: tz }) // YYYY-MM-DD

  // Build a target Date at the preferred hour in the user's timezone.
  // We find the UTC offset by comparing a known format in that timezone.
  const target = findUTCForLocalTime(localDate, hour, tz)

  // If preferred_day set and frequency >= 7, advance to that weekday
  if (day !== null && freqDays >= 7) {
    // Get the current weekday in the user's tz
    const targetDay = new Date(target).toLocaleDateString('en-US', { weekday: 'short', timeZone: tz })
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    let currentDay = dayNames.indexOf(targetDay)
    while (currentDay !== day) {
      target.setTime(target.getTime() + 86400000)
      currentDay = (currentDay + 1) % 7
    }
  }

  return target.toISOString()
}

/**
 * Given a date string (YYYY-MM-DD), an hour (0-23), and a timezone,
 * return a Date object representing that local time in UTC.
 */
function findUTCForLocalTime(dateStr: string, hour: number, tz: string): Date {
  // Start with a rough guess: parse as UTC
  const [y, m, d] = dateStr.split('-').map(Number)
  let guess = new Date(Date.UTC(y, m - 1, d, hour, 0, 0))

  // Iteratively correct: check what hour it is in the target tz and adjust
  for (let i = 0; i < 3; i++) {
    const localHour = parseInt(guess.toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: tz }), 10)
    const localDateStr = guess.toLocaleDateString('en-CA', { timeZone: tz })
    const diff = hour - localHour
    if (diff === 0 && localDateStr === dateStr) break
    // Adjust by hour difference
    if (localDateStr !== dateStr) {
      // Date is off, adjust by a day's worth in the right direction
      const localD = new Date(localDateStr)
      const targetD = new Date(dateStr)
      const dayDiff = (targetD.getTime() - localD.getTime()) / 86400000
      guess = new Date(guess.getTime() + dayDiff * 86400000)
    }
    guess = new Date(guess.getTime() + diff * 3600000)
  }

  return guess
}
