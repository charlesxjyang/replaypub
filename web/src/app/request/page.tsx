'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { BlogRequest } from '@/lib/types'

export default function RequestPage() {
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [requests, setRequests] = useState<BlogRequest[]>([])
  const supabase = createClient()

  useEffect(() => {
    supabase
      .from('blog_requests')
      .select('*')
      .order('vote_count', { ascending: false })
      .limit(20)
      .then(({ data }) => setRequests((data as BlogRequest[]) ?? []))
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')

    const {
      data: { user },
    } = await supabase.auth.getUser()

    const { error } = await supabase.rpc('vote_for_blog_request', {
      p_url: url,
      p_email: user?.email ?? null,
    })

    if (error) {
      setStatus('error')
      return
    }

    // Notify admin (fire-and-forget)
    fetch('/api/notify-admin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'request',
        details: { url, voterEmail: user?.email ?? 'anonymous' },
      }),
    }).catch(() => {})

    setStatus('done')
    setUrl('')

    // Refresh list
    const { data } = await supabase
      .from('blog_requests')
      .select('*')
      .order('vote_count', { ascending: false })
      .limit(20)

    setRequests((data as BlogRequest[]) ?? [])
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold mb-2">Request a blog</h1>
      <p className="text-gray-600 mb-8">
        Submit a blog URL and vote for blogs you want to see on Replay.
      </p>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-12">
        <input
          type="url"
          placeholder="https://example.com/blog"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={status === 'loading'}
          className="bg-gray-900 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-gray-800 disabled:opacity-50 whitespace-nowrap"
        >
          {status === 'loading' ? 'Submitting...' : 'Submit'}
        </button>
      </form>

      {status === 'done' && (
        <p className="text-green-700 bg-green-50 border border-green-200 rounded-lg p-3 text-sm mb-8">
          Request submitted! If others request the same blog, it gets more votes.
        </p>
      )}

      {status === 'error' && (
        <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg p-3 text-sm mb-8">
          Something went wrong. You may need to sign in first.
        </p>
      )}

      {/* Top requested */}
      {requests.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Top requested</h2>
          <div className="space-y-2">
            {requests.map((req) => (
              <div
                key={req.id}
                className="flex items-center justify-between border border-gray-200 rounded-lg px-4 py-3"
              >
                <span className="text-sm text-gray-700 truncate mr-4">{req.url}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                    {req.vote_count} {req.vote_count === 1 ? 'vote' : 'votes'}
                  </span>
                  <span className="text-xs text-gray-400">{req.status}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
