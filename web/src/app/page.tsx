import { createClient } from '@/lib/supabase/server'
import type { Feed } from '@/lib/types'
import FeedCard from '@/components/FeedCard'

export const dynamic = 'force-dynamic'

// Pastel colors for author sections
const AUTHOR_COLORS = [
  'bg-rose-50 border-rose-100',
  'bg-sky-50 border-sky-100',
  'bg-amber-50 border-amber-100',
  'bg-emerald-50 border-emerald-100',
  'bg-violet-50 border-violet-100',
  'bg-orange-50 border-orange-100',
  'bg-teal-50 border-teal-100',
  'bg-pink-50 border-pink-100',
  'bg-indigo-50 border-indigo-100',
  'bg-lime-50 border-lime-100',
]

type FeedWithCount = Feed & { _post_count: number }

export default async function Home() {
  const supabase = await createClient()
  const { data: feeds } = await supabase
    .from('feeds')
    .select('*, blogs(id, name, author, url, post_count)')
    .eq('is_active', true)
    .order('name')

  // Compute actual post counts for feeds with tag filters
  const feedsWithCounts: FeedWithCount[] = await Promise.all(
    (feeds ?? []).map(async (feed) => {
      if (feed.tag_filter && feed.blogs?.id) {
        const { count } = await supabase
          .from('posts')
          .select('*', { count: 'exact', head: true })
          .eq('blog_id', feed.blogs.id)
          .contains('tags', [feed.tag_filter])
        return { ...feed, _post_count: count ?? 0 }
      }
      return { ...feed, _post_count: feed.blogs?.post_count ?? 0 }
    })
  )

  // Group feeds by author
  const feedsByAuthor: Record<string, FeedWithCount[]> = {}
  for (const feed of feedsWithCounts) {
    const author = feed.blogs?.author || 'Unknown'
    if (!feedsByAuthor[author]) {
      feedsByAuthor[author] = []
    }
    feedsByAuthor[author].push(feed)
  }

  // Sort authors alphabetically
  const sortedAuthors = Object.keys(feedsByAuthor).sort()

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

      {/* Feed catalog grouped by author */}
      {sortedAuthors.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-6">Available feeds</h2>
          <div className="space-y-4">
            {sortedAuthors.map((author, index) => {
              const authorFeeds = feedsByAuthor[author]
              const colorClass = AUTHOR_COLORS[index % AUTHOR_COLORS.length]
              return (
                <div
                  key={author}
                  className={`rounded-xl p-4 border ${colorClass}`}
                >
                  <h3 className="font-medium text-gray-800 mb-3">{author}</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {authorFeeds.map((feed) => (
                      <FeedCard
                        key={feed.id}
                        feed={feed as Feed}
                        postCount={feed._post_count}
                        showAuthor={false}
                      />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}
    </div>
  )
}
