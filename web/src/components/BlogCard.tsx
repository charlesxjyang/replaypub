import Link from 'next/link'
import type { Blog } from '@/lib/types'

export default function BlogCard({ blog }: { blog: Blog }) {
  return (
    <Link
      href={`/blogs/${blog.slug}`}
      className="block border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition-all"
    >
      <h3 className="font-semibold text-gray-900 mb-1">{blog.name}</h3>
      {blog.author && (
        <p className="text-sm text-gray-500 mb-2">by {blog.author}</p>
      )}
      {blog.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{blog.description}</p>
      )}
      <p className="text-xs text-gray-400">{blog.post_count} posts</p>
    </Link>
  )
}
