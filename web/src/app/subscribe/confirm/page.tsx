'use client'

import { useSearchParams } from 'next/navigation'
import { useEffect, useState, Suspense } from 'react'
import { createClient } from '@/lib/supabase/client'

function ConfirmContent() {
  const searchParams = useSearchParams()
  const feedId = searchParams.get('feed_id')
  const blogId = searchParams.get('blog_id')
  const frequency = parseInt(searchParams.get('frequency') ?? '7', 10)
  const [status, setStatus] = useState<'loading' | 'done' | 'error' | 'already_subscribed'>('loading')
  const [errorDetail, setErrorDetail] = useState<string>('')
  const supabase = createClient()

  useEffect(() => {
    async function createSubscription() {
      if (!feedId || !blogId) {
        setErrorDetail(`Missing params: feedId=${feedId}, blogId=${blogId}`)
        setStatus('error')
        return
      }

      const {
        data: { user },
        error: authError,
      } = await supabase.auth.getUser()

      if (!user) {
        setErrorDetail(`No user session: ${authError?.message || 'not authenticated'}`)
        setStatus('error')
        return
      }

      // Check if already subscribed
      const { data: existing } = await supabase
        .from('subscriptions')
        .select('id')
        .eq('subscriber_id', user.id)
        .eq('feed_id', feedId)
        .maybeSingle()

      if (existing) {
        setStatus('already_subscribed')
        return
      }

      // Create subscription
      const { error } = await supabase.from('subscriptions').insert({
        subscriber_id: user.id,
        blog_id: blogId,
        feed_id: feedId,
        frequency_days: frequency,
        current_post_index: 0,
        next_send_at: new Date().toISOString(),
        is_active: true,
      })

      if (error) {
        console.error('Subscription error:', error)
        // Check if it's a unique constraint violation (already subscribed)
        if (error.code === '23505') {
          setStatus('already_subscribed')
          return
        }
        setErrorDetail(`Insert failed: ${error.message} (code: ${error.code})`)
      }
      setStatus(error ? 'error' : 'done')
    }

    createSubscription()
  }, [feedId, blogId, frequency])

  if (status === 'loading') {
    return <p className="text-gray-500">Setting up your subscription...</p>
  }

  if (status === 'error') {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
        <p className="text-gray-600 mb-4">
          We couldn&apos;t create your subscription. Please try again.
        </p>
        {errorDetail && (
          <p className="text-xs text-red-500 bg-red-50 p-3 rounded mb-4 font-mono">
            {errorDetail}
          </p>
        )}
        <a href="/" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
          Back to home
        </a>
      </div>
    )
  }

  if (status === 'already_subscribed') {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-2">You&apos;re already subscribed!</h1>
        <p className="text-gray-600 mb-6">
          You already have an active subscription to this feed. You can manage it from your dashboard.
        </p>
        <div className="flex gap-3">
          <a
            href="/dashboard"
            className="bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800"
          >
            Go to dashboard
          </a>
          <a href="/" className="text-gray-600 hover:text-gray-900 px-4 py-2 text-sm font-medium">
            Back to home
          </a>
        </div>
      </div>
    )
  }

  const baseUrl = process.env.NEXT_PUBLIC_STRIPE_DONATE_URL
  const donateUrl = baseUrl ? `${baseUrl}?client_reference_id=${encodeURIComponent(feedId || '')}` : null

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">You&apos;re subscribed!</h1>
      <p className="text-gray-600 mb-6">
        Your first post will arrive soon. You can manage your subscription
        from your dashboard.
      </p>

      {donateUrl && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 mb-6 text-left">
          <p className="text-amber-900 font-medium mb-2">
            Enjoying Replay?
          </p>
          <p className="text-amber-800 text-sm mb-4">
            This project is free to use. If you find it valuable, consider buying me a coffee to help keep it running.
          </p>
          <a
            href={donateUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-amber-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-amber-600"
          >
            Support Replay
          </a>
        </div>
      )}

      <div className="flex gap-3 justify-center">
        <a
          href="/dashboard"
          className="bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800"
        >
          Go to dashboard
        </a>
        <a href="/" className="text-gray-600 hover:text-gray-900 px-4 py-2 text-sm font-medium">
          Back to home
        </a>
      </div>
    </div>
  )
}

export default function ConfirmPage() {
  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <Suspense fallback={<p className="text-gray-500">Loading...</p>}>
        <ConfirmContent />
      </Suspense>
    </div>
  )
}
