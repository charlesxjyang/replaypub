'use client'

import { useState, useEffect } from 'react'

interface FeedOption {
  id: string
  slug: string
  name: string
  tag_filter: string | null
  blog_id: string
  post_count: number
}

export default function EmbedForm({
  blogId,
  blogName,
  author,
  feeds,
}: {
  blogId: string
  blogName: string
  author: string | null
  feeds: FeedOption[]
}) {
  const [selectedFeed, setSelectedFeed] = useState<FeedOption>(feeds[0])
  const [email, setEmail] = useState('')
  const [frequency, setFrequency] = useState(7)
  const [status, setStatus] = useState<'idle' | 'loading' | 'sent' | 'error' | 'already_subscribed'>('idle')
  const [timezone, setTimezone] = useState('UTC')

  useEffect(() => {
    try {
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone)
    } catch {
      // Fall back to UTC
    }
  }, [])

  function feedLabel(feed: FeedOption) {
    if (!feed.tag_filter) return 'All'
    return feed.tag_filter
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')

    try {
      const res = await fetch('/api/embed-subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          feed_id: selectedFeed.id,
          blog_id: blogId,
          frequency,
          timezone,
          feed_name: selectedFeed.name,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setStatus('error')
        return
      }

      if (data.status === 'already_subscribed') {
        setStatus('already_subscribed')
        return
      }

      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <div className="text-center py-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-5">
          <p className="text-green-800 font-medium mb-1">Check your email</p>
          <p className="text-green-700 text-sm">
            We sent a confirmation link to <strong>{email}</strong>.
            Click it to start receiving {selectedFeed.tag_filter ? feedLabel(selectedFeed) : ''} posts
            {author ? ` from ${author}` : ''}.
          </p>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Powered by <a href="https://replay.pub" target="_blank" rel="noopener noreferrer" className="underline">Replay</a>
        </p>
      </div>
    )
  }

  if (status === 'already_subscribed') {
    return (
      <div className="text-center py-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
          <p className="text-blue-800 font-medium mb-1">Already subscribed</p>
          <p className="text-blue-700 text-sm">
            You&apos;re already receiving this feed. Manage it on your{' '}
            <a href="https://replay.pub/dashboard" target="_blank" rel="noopener noreferrer" className="underline">
              dashboard
            </a>.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h3 className="font-semibold text-gray-900 mb-1 text-base">
        Get {blogName} in your inbox
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        Receive one {author ? `${author} ` : ''}speech at a time, on your schedule.
      </p>

      {/* Feed picker */}
      {feeds.length > 1 && (
        <div className="mb-4">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">
            Choose a theme
          </label>
          <div className="flex flex-wrap gap-1.5">
            {feeds.map((feed) => (
              <button
                key={feed.id}
                type="button"
                onClick={() => setSelectedFeed(feed)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  selectedFeed.id === feed.id
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {feedLabel(feed)}
                <span className="text-xs ml-1 opacity-60">{feed.post_count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Description of selected feed */}
      <p className="text-xs text-gray-400 mb-4">
        {selectedFeed.post_count} posts
        {selectedFeed.tag_filter ? ` on ${selectedFeed.tag_filter}` : ''}
        {' '}delivered to your inbox
      </p>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent bg-white"
          />
          <select
            value={frequency}
            onChange={(e) => setFrequency(Number(e.target.value))}
            className="border border-gray-200 rounded-lg px-2 py-2 text-sm bg-white text-gray-700"
          >
            <option value={7}>Weekly</option>
            <option value={14}>Biweekly</option>
            <option value={1}>Daily</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={status === 'loading'}
          className="w-full bg-gray-900 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {status === 'loading' ? 'Sending...' : 'Subscribe'}
        </button>
        {status === 'error' && (
          <p className="text-sm text-red-600 text-center">
            Something went wrong. Please try again.
          </p>
        )}
      </form>

      <p className="text-xs text-gray-400 mt-3 text-center">
        Powered by <a href="https://replay.pub" target="_blank" rel="noopener noreferrer" className="underline hover:text-gray-600">Replay</a>
      </p>
    </div>
  )
}
