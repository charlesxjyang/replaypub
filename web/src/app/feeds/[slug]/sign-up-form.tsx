'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import FrequencyPicker from '@/components/FrequencyPicker'
import DayPicker from '@/components/DayPicker'
import TimePicker from '@/components/TimePicker'
import type { User } from '@supabase/supabase-js'

export default function SignUpForm({
  feedId,
  blogId,
  feedName,
}: {
  feedId: string
  blogId: string
  feedName: string
}) {
  const [email, setEmail] = useState('')
  const [frequency, setFrequency] = useState(7)
  const [preferredDay, setPreferredDay] = useState<number | null>(null)
  const [preferredHour, setPreferredHour] = useState(9)
  const [timezone, setTimezone] = useState('UTC')
  const [status, setStatus] = useState<'idle' | 'loading' | 'sent' | 'error' | 'already_subscribed' | 'subscribed' | 'limit_reached'>('idle')
  const [user, setUser] = useState<User | null>(null)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const supabase = createClient()

  // Auto-detect timezone on mount
  useEffect(() => {
    try {
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone)
    } catch {
      // Fall back to UTC
    }
  }, [])

  // Check if user is already logged in
  useEffect(() => {
    async function checkAuth() {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      setCheckingAuth(false)

      // If logged in, check if already subscribed to this feed
      if (user) {
        const { data: existing } = await supabase
          .from('subscriptions')
          .select('id')
          .eq('subscriber_id', user.id)
          .eq('feed_id', feedId)
          .maybeSingle()

        if (existing) {
          setStatus('already_subscribed')
        }
      }
    }
    checkAuth()
  }, [feedId])

  // For logged-in users: subscribe directly
  async function handleDirectSubscribe() {
    if (!user) return
    setStatus('loading')

    // Check subscription limit (max 3 active feeds)
    const { count } = await supabase
      .from('subscriptions')
      .select('*', { count: 'exact', head: true })
      .eq('subscriber_id', user.id)
      .eq('is_active', true)

    if (count !== null && count >= 3) {
      setStatus('limit_reached')
      return
    }

    const { error } = await supabase.from('subscriptions').insert({
      subscriber_id: user.id,
      blog_id: blogId,
      feed_id: feedId,
      frequency_days: frequency,
      preferred_day: preferredDay,
      preferred_hour: preferredHour,
      timezone,
      current_post_index: 0,
      next_send_at: new Date().toISOString(),
      is_active: true,
    })

    if (error) {
      console.error('Subscription error:', error)
      if (error.code === '23505') {
        setStatus('already_subscribed')
        return
      }
      setStatus('error')
      return
    }

    // Send confirmation email
    try {
      await fetch('/api/send-confirmation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email, feedName }),
      })
    } catch {
      // Email is non-critical, don't fail the subscription
      console.error('Failed to send confirmation email')
    }

    setStatus('subscribed')
  }

  // For new users: send magic link
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')

    // Check if already subscribed before sending magic link
    try {
      const checkRes = await fetch('/api/check-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, feed_id: feedId }),
      })
      const { subscribed } = await checkRes.json()

      if (subscribed) {
        setStatus('already_subscribed')
        return
      }
    } catch {
      // If check fails, proceed anyway — confirm page will handle duplicates
    }

    // Sign up / sign in with magic link
    // Encode all subscription params into the `next` path so they survive the auth redirect
    const confirmParams = new URLSearchParams({
      feed_id: feedId,
      blog_id: blogId,
      frequency: String(frequency),
      preferred_hour: String(preferredHour),
      timezone,
    })
    if (preferredDay !== null) {
      confirmParams.set('preferred_day', String(preferredDay))
    }
    const nextPath = `/subscribe/confirm?${confirmParams.toString()}`
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(nextPath)}`,
      },
    })

    setStatus(error ? 'error' : 'sent')
  }

  // Loading auth state
  if (checkingAuth) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-500 text-sm">Loading...</p>
      </div>
    )
  }

  if (status === 'sent') {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <p className="text-green-800 font-medium mb-1">Check your email</p>
        <p className="text-green-700 text-sm">
          We sent a verification link to <strong>{email}</strong>.
          Click it to start receiving posts from {feedName}.
        </p>
      </div>
    )
  }

  if (status === 'subscribed') {
    const baseUrl = process.env.NEXT_PUBLIC_STRIPE_DONATE_URL
    const donateUrl = baseUrl && user?.email
      ? `${baseUrl}?prefilled_email=${encodeURIComponent(user.email)}`
      : baseUrl
    return (
      <div className="space-y-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <p className="text-green-800 font-medium mb-1">You&apos;re subscribed!</p>
          <p className="text-green-700 text-sm mb-3">
            Your first post from {feedName} will arrive soon.
          </p>
          <a href="/dashboard" className="text-green-700 text-sm underline">
            Go to dashboard
          </a>
        </div>
        {donateUrl && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-left">
            <p className="text-amber-900 font-medium mb-2">
              Enjoying Replay?
            </p>
            <p className="text-amber-800 text-sm mb-3">
              If you find it valuable, consider supporting the project.
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
      </div>
    )
  }

  if (status === 'already_subscribed') {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <p className="text-blue-800 font-medium mb-1">You&apos;re already subscribed</p>
        <p className="text-blue-700 text-sm mb-3">
          You&apos;re already receiving posts from {feedName}.
        </p>
        <a href="/dashboard" className="text-blue-700 text-sm underline">
          Go to dashboard
        </a>
      </div>
    )
  }

  if (status === 'limit_reached') {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
        <p className="text-amber-800 font-medium mb-1">Subscription limit reached</p>
        <p className="text-amber-700 text-sm mb-3">
          We currently limit users to 3 active feeds at a time. Unsubscribe from a feed to add a new one.
        </p>
        <a href="/dashboard" className="text-amber-700 text-sm underline">
          Manage subscriptions
        </a>
      </div>
    )
  }

  // Logged-in user: show direct subscribe button
  if (user) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold mb-1">Subscribe to this feed</h3>
        <p className="text-sm text-gray-500 mb-4">
          Get posts from {feedName} delivered to your inbox on a schedule.
        </p>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">Receive posts:</span>
            <FrequencyPicker value={frequency} onChange={setFrequency} />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">Deliver at:</span>
            <TimePicker value={preferredHour} onChange={setPreferredHour} />
          </div>
          {frequency >= 7 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">On:</span>
              <DayPicker value={preferredDay} onChange={setPreferredDay} />
            </div>
          )}
          <button
            onClick={handleDirectSubscribe}
            disabled={status === 'loading'}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {status === 'loading' ? 'Subscribing...' : 'Start reading'}
          </button>
          {status === 'error' && (
            <p className="text-sm text-red-600 text-center">
              Something went wrong. Please try again.
            </p>
          )}
        </div>
      </div>
    )
  }

  // Not logged in: show email form
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <h3 className="font-semibold mb-1">Sign up to receive posts</h3>
      <p className="text-sm text-gray-500 mb-4">
        Get posts from {feedName} delivered to your inbox on a schedule.
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
        />
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">Receive posts:</span>
          <FrequencyPicker value={frequency} onChange={setFrequency} />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">Deliver at:</span>
          <TimePicker value={preferredHour} onChange={setPreferredHour} />
        </div>
        {frequency >= 7 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">On:</span>
            <DayPicker value={preferredDay} onChange={setPreferredDay} />
          </div>
        )}
        <button
          type="submit"
          disabled={status === 'loading'}
          className="w-full bg-blue-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {status === 'loading' ? 'Sending...' : 'Start reading'}
        </button>
        {status === 'error' && (
          <p className="text-sm text-red-600 text-center">
            Something went wrong. Please try again.
          </p>
        )}
      </form>
    </div>
  )
}
