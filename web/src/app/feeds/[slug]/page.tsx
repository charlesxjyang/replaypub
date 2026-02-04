import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Feed, Post } from '@/lib/types'
import SignUpForm from './sign-up-form'

export const dynamic = 'force-dynamic'

export default async function FeedDetail({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const supabase = await createClient()

  const { data: feed } = await supabase
    .from('feeds')
    .select('*, blogs(id, name, author, url, post_count)')
    .eq('slug', slug)
    .single()

  if (!feed) notFound()

  const typedFeed = feed as Feed
  const blog = typedFeed.blogs!

  // Fetch posts — filtered by tag if the feed has a tag_filter
  let query = supabase
    .from('posts')
    .select('id, title, excerpt, post_index, reading_time_minutes, tags, original_url, published_at')
    .eq('blog_id', blog.id)
    .order('post_index')

  if (typedFeed.tag_filter) {
    query = query.contains('tags', [typedFeed.tag_filter])
  }

  const { data: posts } = await query

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold mb-2">{typedFeed.name}</h1>
      {blog.author && (
        <p className="text-gray-500 mb-2">by {blog.author}</p>
      )}
      {typedFeed.description && (
        <p className="text-gray-600 mb-4">{typedFeed.description}</p>
      )}
      <p className="text-sm text-gray-400 mb-8">
        {(posts as Post[] ?? []).length} posts
      </p>

      {/* Sign up */}
      <div className="mb-12">
        <SignUpForm feedId={typedFeed.id} blogId={blog.id} feedName={typedFeed.name} />
      </div>

      {/* Post list */}
      {posts && posts.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-1">Delivery order</h2>
          <p className="text-sm text-gray-500 mb-4">
            Posts are delivered starting from #1. Each email contains one post.
          </p>
          <div className="space-y-3">
            {(posts as Post[]).map((post, index) => (
              <a
                key={post.id}
                href={`${post.original_url}${post.original_url.includes('?') ? '&' : '?'}utm_source=replay`}
                target="_blank"
                rel="noopener noreferrer"
                className="block border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 text-gray-500 text-sm font-medium flex items-center justify-center">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
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
                    <div className="flex items-center gap-2 mt-2">
                      {index === 0 && (
                        <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded font-medium">
                          First email
                        </span>
                      )}
                      {index === (posts as Post[]).length - 1 && (posts as Post[]).length > 1 && (
                        <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-medium">
                          Last email
                        </span>
                      )}
                      {post.tags && post.tags.length > 0 && post.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
