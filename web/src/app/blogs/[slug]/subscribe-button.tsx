'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import FrequencyPicker from '@/components/FrequencyPicker'

export default function SubscribeButton({
  blogId,
  blogSlug,
  isLoggedIn,
}: {
  blogId: string
  blogSlug: string
  isLoggedIn: boolean
}) {
  const [frequency, setFrequency] = useState(7)
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const router = useRouter()
  const supabase = createClient()

  if (!isLoggedIn) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600 mb-3">Sign in to subscribe to this blog.</p>
        <a
          href="/#login"
          className="inline-block bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800"
        >
          Sign in
        </a>
      </div>
    )
  }

  async function handleSubscribe() {
    setStatus('loading')

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) {
      setStatus('error')
      return
    }

    const { error } = await supabase.from('subscriptions').insert({
      subscriber_id: user.id,
      blog_id: blogId,
      frequency_days: frequency,
      current_post_index: 0,
      next_send_at: new Date().toISOString(),
      is_active: true,
    })

    if (error) {
      if (error.code === '23505') {
        // Already subscribed
        router.push('/dashboard')
        return
      }
      setStatus('error')
      return
    }

    setStatus('done')
    router.push('/dashboard')
  }

  if (status === 'done') {
    return (
      <p className="text-center text-green-700 bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
        Subscribed! Redirecting to dashboard...
      </p>
    )
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <h3 className="font-semibold mb-3">Subscribe</h3>
      <div className="flex items-center gap-4 mb-4">
        <span className="text-sm text-gray-600">Receive posts:</span>
        <FrequencyPicker value={frequency} onChange={setFrequency} />
      </div>
      <button
        onClick={handleSubscribe}
        disabled={status === 'loading'}
        className="w-full bg-blue-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {status === 'loading' ? 'Subscribing...' : 'Start reading'}
      </button>
      {status === 'error' && (
        <p className="text-sm text-red-600 text-center mt-2">
          Something went wrong. Please try again.
        </p>
      )}
    </div>
  )
}
