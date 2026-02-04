'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Subscription } from '@/lib/types'
import ProgressBar from './ProgressBar'
import FrequencyPicker from './FrequencyPicker'

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

  async function updateSubscription(updates: Partial<Subscription>) {
    setLoading(true)
    await supabase
      .from('subscriptions')
      .update(updates)
      .eq('id', subscription.id)
    setLoading(false)
    onUpdate()
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
          onChange={(days) => updateSubscription({ frequency_days: days })}
          disabled={loading || subscription.is_completed}
        />
      </div>

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
          onClick={() => {
            if (confirm('Unsubscribe from this blog?')) {
              updateSubscription({ is_active: false })
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
