'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Subscription } from '@/lib/types'
import SubscriptionCard from '@/components/SubscriptionCard'

export default function Dashboard() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  const fetchSubscriptions = useCallback(async () => {
    const { data } = await supabase
      .from('subscriptions')
      .select('*, blogs(name, post_count, slug), feeds(name, slug)')
      .order('created_at', { ascending: false })

    setSubscriptions((data as Subscription[]) ?? [])
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchSubscriptions()
  }, [fetchSubscriptions])

  async function handleLogout() {
    await supabase.auth.signOut()
    window.location.href = '/'
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Your subscriptions</h1>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Sign out
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : subscriptions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No subscriptions yet.</p>
          <a
            href="/"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Browse blogs
          </a>
        </div>
      ) : (
        <div className="space-y-4">
          {subscriptions.map((sub) => (
            <SubscriptionCard
              key={sub.id}
              subscription={sub as Subscription & { blogs: { name: string; post_count: number; slug: string } }}
              onUpdate={fetchSubscriptions}
            />
          ))}
        </div>
      )}
    </div>
  )
}
