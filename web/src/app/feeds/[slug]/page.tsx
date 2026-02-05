import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Feed, Post } from '@/lib/types'
import SignUpForm from './sign-up-form'
import { AWAITING_PERMISSION_AUTHORS } from '@/components/FeedCard'

export const dynamic = 'force-dynamic'

async function getFeed(slug: string) {
  const supabase = await createClient()
  const { data: feed } = await supabase
    .from('feeds')
    .select('*, blogs(id, name, author, url, post_count)')
    .eq('slug', slug)
    .single()
  return feed as Feed | null
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const feed = await getFeed(slug)
  if (!feed) return {}

  const blog = feed.blogs!
  const title = feed.name
  const description = feed.description || `Subscribe to ${feed.name} by ${blog.author ?? 'unknown'} and receive posts as a drip email series.`

  return {
    title,
    description,
    openGraph: { title, description },
    twitter: { title, description },
    alternates: { canonical: `/feeds/${slug}` },
  }
}

export default async function FeedDetail({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const feed = await getFeed(slug)

  if (!feed) notFound()

  const typedFeed = feed
  const blog = typedFeed.blogs!

  const supabase = await createClient()

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

  // Use feed's source_url if set, otherwise fall back to blog URL
  const sourceUrl = typedFeed.source_url || blog.url

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: typedFeed.name,
    description: typedFeed.description ?? undefined,
    url: `https://replay.pub/feeds/${slug}`,
    mainEntity: {
      '@type': 'ItemList',
      numberOfItems: (posts as Post[] ?? []).length,
      itemListElement: (posts as Post[] ?? []).slice(0, 50).map((post, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: post.title,
        url: post.original_url,
      })),
    },
  }

  return (
    <>
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold mb-2">
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-blue-600 transition-colors"
        >
          {typedFeed.name}
          <span className="text-gray-400 ml-2 text-lg">↗</span>
        </a>
      </h1>
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
        {blog.author && AWAITING_PERMISSION_AUTHORS.includes(blog.author) ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
            <p className="text-amber-800 font-medium mb-1">Awaiting author permission</p>
            <p className="text-amber-700 text-sm">
              We&apos;re working on getting permission from the author to distribute this content.
              Check back soon!
            </p>
          </div>
        ) : (
          <SignUpForm feedId={typedFeed.id} blogId={blog.id} feedName={typedFeed.name} />
        )}
      </div>

      {/* Post list */}
      {posts && posts.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-1">Delivery order</h2>
          <p className="text-sm text-gray-500 mb-4">
            Each email contains one post, starting with #1
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
    </>
  )
}
