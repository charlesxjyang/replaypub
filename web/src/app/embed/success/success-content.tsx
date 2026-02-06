'use client'

import { useSearchParams } from 'next/navigation'

export default function SuccessContent() {
  const searchParams = useSearchParams()
  const feedName = searchParams.get('feed')
  const already = searchParams.get('already')

  if (already) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-2">Already subscribed</h1>
        <p className="text-gray-600 mb-6">
          You already have an active subscription to this feed.
        </p>
        <a
          href="https://replaypub.vercel.app/dashboard"
          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
        >
          Go to dashboard
        </a>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <h1 className="text-2xl font-bold mb-2">You&apos;re subscribed!</h1>
      <p className="text-gray-600 mb-6">
        {feedName
          ? <>Your first post from <strong>{feedName}</strong> will arrive soon.</>
          : <>Your first post will arrive soon.</>
        }
      </p>
      <p className="text-gray-500 text-sm mb-6">
        You can manage your subscription anytime from the Replay dashboard.
      </p>
      <a
        href="https://replaypub.vercel.app/dashboard"
        className="inline-block bg-gray-900 text-white px-6 py-2.5 rounded-md text-sm font-medium hover:bg-gray-800"
      >
        Go to dashboard
      </a>
    </div>
  )
}
