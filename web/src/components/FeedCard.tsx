import Link from 'next/link'
import type { Feed } from '@/lib/types'

// Authors awaiting permission - feeds are visible but not subscribable
export const AWAITING_PERMISSION_AUTHORS = [
  'Paul Graham',
  'Patrick McKenzie',
  'Venkatesh Rao',
  'Dan Wang',
]

export default function FeedCard({
  feed,
  postCount,
  showAuthor = true,
}: {
  feed: Feed
  postCount?: number
  showAuthor?: boolean
}) {
  const blog = feed.blogs
  const count = postCount ?? feed.blogs?.post_count ?? 0
  const awaitingPermission = blog?.author && AWAITING_PERMISSION_AUTHORS.includes(blog.author)

  if (awaitingPermission) {
    return (
      <div className="block border border-gray-200 rounded-lg p-5 bg-gray-50 opacity-60">
        <h3 className="font-semibold text-gray-500 mb-1">{feed.name}</h3>
        {showAuthor && blog?.author && (
          <p className="text-sm text-gray-400 mb-2">by {blog.author}</p>
        )}
        {feed.description && (
          <p className="text-sm text-gray-400 mb-3 line-clamp-2">{feed.description}</p>
        )}
        <p className="text-xs text-amber-600 font-medium">Awaiting author permission</p>
      </div>
    )
  }

  return (
    <Link
      href={`/feeds/${feed.slug}`}
      className="block border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition-all bg-white"
    >
      <h3 className="font-semibold text-gray-900 mb-1">{feed.name}</h3>
      {showAuthor && blog?.author && (
        <p className="text-sm text-gray-500 mb-2">by {blog.author}</p>
      )}
      {feed.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{feed.description}</p>
      )}
      <p className="text-xs text-gray-400">{count} posts</p>
    </Link>
  )
}
