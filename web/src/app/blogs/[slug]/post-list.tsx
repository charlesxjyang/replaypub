'use client'

import { useState } from 'react'
import type { Post } from '@/lib/types'

export default function PostList({
  posts,
  tags,
}: {
  posts: Post[]
  tags: string[]
}) {
  const [activeTag, setActiveTag] = useState<string | null>(null)

  const filtered = activeTag
    ? posts.filter((p) => p.tags?.includes(activeTag))
    : posts

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          Posts{activeTag ? ` tagged "${activeTag}"` : ''}
          <span className="text-sm font-normal text-gray-400 ml-2">
            {filtered.length}
          </span>
        </h2>
      </div>

      {/* Tag filter */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setActiveTag(null)}
            className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
              activeTag === null
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            All
          </button>
          {tags.map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                activeTag === tag
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Post list */}
      <div className="space-y-3">
        {filtered.map((post) => (
          <div
            key={post.id}
            className="border border-gray-200 rounded-lg p-4"
          >
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="font-medium text-gray-900">{post.title}</h3>
              {post.reading_time_minutes && (
                <span className="text-xs text-gray-400 whitespace-nowrap">
                  {post.reading_time_minutes} min
                </span>
              )}
            </div>
            {post.excerpt && (
              <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                {post.excerpt}
              </p>
            )}
            {post.tags && post.tags.length > 0 && (
              <div className="flex gap-1.5 mt-2">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
