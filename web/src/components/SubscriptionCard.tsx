'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Subscription } from '@/lib/types'
import ProgressBar from './ProgressBar'
import FrequencyPicker from './FrequencyPicker'
import DayPicker from './DayPicker'
import TimePicker from './TimePicker'

export default function SubscriptionCard({
  subscription,
  onUpdate,
}: {
  subscription: Subscription & { blogs: { name: string; post_count: number; slug: string }; feeds?: { name: string; slug: string } | null }
  onUpdate: () => void
}) {
  const [loading, setLoading] = useState(false)
  const supabase = createClient()
  const blog = subscription.blogs
  const feed = subscription.feeds

  async function updateSubscription(updates: Record<string, unknown>) {
    setLoading(true)
    await supabase
      .from('subscriptions')
      .update(updates)
      .eq('id', subscription.id)
    setLoading(false)
    onUpdate()
  }

  function computeNextSend(freqDays: number, day: number | null, hour: number, tz: string): string {
    // Calculate next send in user's local time, then convert to ISO
    const now = new Date()
    const next = new Date(now.getTime() + freqDays * 86400000)
    // Create a date string in the user's timezone and snap to preferred hour
    const localStr = next.toLocaleDateString('en-CA', { timeZone: tz }) // YYYY-MM-DD
    const snapped = new Date(`${localStr}T${String(hour).padStart(2, '0')}:00:00`)

    // If preferred_day set and frequency >= 7, advance to that weekday
    if (day !== null && freqDays >= 7) {
      while (snapped.getDay() !== day) {
        snapped.setDate(snapped.getDate() + 1)
      }
    }

    // Convert local time in tz to UTC by using the timezone offset
    // We'll use a simple approach: format as ISO and let the DB handle it
    return snapped.toISOString()
  }

  const isPaused = !subscription.is_active

  return (
    <div className="border border-gray-200 rounded-lg p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{feed?.name ?? blog.name}</h3>
          {subscription.next_send_at && subscription.is_active && (
            <p className="text-xs text-gray-500 mt-0.5">
              Next email: {new Date(subscription.next_send_at).toLocaleDateString()}
            </p>
          )}
          {isPaused && (
            <p className="text-xs text-amber-600 mt-0.5">Paused</p>
          )}
          {subscription.is_completed && (
            <p className="text-xs text-green-600 mt-0.5">Completed</p>
          )}
        </div>
        <FrequencyPicker
          value={subscription.frequency_days}
          onChange={(days) => {
            const nextSend = computeNextSend(days, subscription.preferred_day, subscription.preferred_hour, subscription.timezone)
            updateSubscription({ frequency_days: days, next_send_at: nextSend })
          }}
          disabled={loading || subscription.is_completed}
        />
      </div>

      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs text-gray-500">At:</span>
        <TimePicker
          value={subscription.preferred_hour}
          onChange={(hour) => {
            const nextSend = computeNextSend(subscription.frequency_days, subscription.preferred_day, hour, subscription.timezone)
            updateSubscription({ preferred_hour: hour, next_send_at: nextSend })
          }}
          disabled={loading || subscription.is_completed}
        />
      </div>

      {subscription.frequency_days >= 7 && (
        <div className="flex items-center gap-3 mb-3">
          <span className="text-xs text-gray-500">On:</span>
          <DayPicker
            value={subscription.preferred_day}
            onChange={(day) => {
              const nextSend = computeNextSend(subscription.frequency_days, day, subscription.preferred_hour, subscription.timezone)
              updateSubscription({ preferred_day: day, next_send_at: nextSend })
            }}
            disabled={loading || subscription.is_completed}
          />
        </div>
      )}

      <ProgressBar
        current={subscription.current_post_index}
        total={blog.post_count}
      />

      <div className="flex gap-2 mt-3">
        {!subscription.is_completed && (
          <button
            onClick={() =>
              updateSubscription({
                is_active: !subscription.is_active,
                paused_at: subscription.is_active ? new Date().toISOString() : null,
              })
            }
            disabled={loading}
            className="text-xs px-3 py-1 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        )}
        <button
          onClick={async () => {
            if (confirm('Unsubscribe from this blog?')) {
              setLoading(true)
              await supabase
                .from('subscriptions')
                .delete()
                .eq('id', subscription.id)
              setLoading(false)
              onUpdate()
            }
          }}
          disabled={loading}
          className="text-xs px-3 py-1 text-red-600 border border-red-200 rounded-md hover:bg-red-50 disabled:opacity-50"
        >
          Unsubscribe
        </button>
      </div>
    </div>
  )
}
