import Link from 'next/link'
import type { Feed } from '@/lib/types'

export default function FeedCard({ feed, postCount }: { feed: Feed; postCount?: number }) {
  const blog = feed.blogs
  const count = postCount ?? feed.blogs?.post_count ?? 0
  return (
    <Link
      href={`/feeds/${feed.slug}`}
      className="block border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition-all"
    >
      <h3 className="font-semibold text-gray-900 mb-1">{feed.name}</h3>
      {blog?.author && (
        <p className="text-sm text-gray-500 mb-2">by {blog.author}</p>
      )}
      {feed.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{feed.description}</p>
      )}
      <p className="text-xs text-gray-400">{count} posts</p>
    </Link>
  )
}
