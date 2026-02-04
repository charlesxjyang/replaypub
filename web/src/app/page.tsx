import { createClient } from '@/lib/supabase/server'
import type { Feed } from '@/lib/types'
import FeedCard from '@/components/FeedCard'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const supabase = await createClient()
  const { data: feeds } = await supabase
    .from('feeds')
    .select('*, blogs(id, name, author, url, post_count)')
    .eq('is_active', true)
    .order('name')

  // Compute actual post counts for feeds with tag filters
  const feedsWithCounts = await Promise.all(
    (feeds ?? []).map(async (feed) => {
      if (feed.tag_filter && feed.blogs?.id) {
        // Count posts matching the tag filter
        const { count } = await supabase
          .from('posts')
          .select('*', { count: 'exact', head: true })
          .eq('blog_id', feed.blogs.id)
          .contains('tags', [feed.tag_filter])
        return { ...feed, _post_count: count ?? 0 }
      }
      // No filter - use blog's total count
      return { ...feed, _post_count: feed.blogs?.post_count ?? 0 }
    })
  )

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      {/* Hero */}
      <section className="text-center mb-16">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Great blogs, delivered over time
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Subscribe to classic blog archives and receive one post at a time,
          on your schedule. No algorithms, no feeds &mdash; just great writing in your inbox.
        </p>
      </section>

      {/* Feed catalog */}
      {feeds && feeds.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-6">Available feeds</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {feedsWithCounts.map((feed) => (
              <FeedCard key={feed.id} feed={feed as Feed} postCount={feed._post_count} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
