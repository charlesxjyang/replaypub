'use client'

import { useSearchParams } from 'next/navigation'
import { useEffect, useState, Suspense } from 'react'

function UnsubscribeContent() {
  const searchParams = useSearchParams()
  const sid = searchParams.get('sid')
  const [status, setStatus] = useState<'loading' | 'done' | 'error'>('loading')

  useEffect(() => {
    if (!sid) {
      setStatus('error')
      return
    }

    fetch('/api/unsubscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription_id: sid }),
    })
      .then((res) => setStatus(res.ok ? 'done' : 'error'))
      .catch(() => setStatus('error'))
  }, [sid])

  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      {status === 'loading' && <p className="text-gray-500">Unsubscribing...</p>}

      {status === 'done' && (
        <div>
          <h1 className="text-2xl font-bold mb-2">Unsubscribed</h1>
          <p className="text-gray-600 mb-6">
            You will no longer receive emails for this subscription.
          </p>
          <a
            href="/dashboard"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Go to dashboard
          </a>
        </div>
      )}

      {status === 'error' && (
        <div>
          <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
          <p className="text-gray-600 mb-6">
            We couldn&apos;t process your unsubscribe request.
          </p>
          <a
            href="/dashboard"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Go to dashboard
          </a>
        </div>
      )}
    </div>
  )
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={<div className="max-w-md mx-auto px-4 py-16 text-center"><p className="text-gray-500">Loading...</p></div>}>
      <UnsubscribeContent />
    </Suspense>
  )
}
