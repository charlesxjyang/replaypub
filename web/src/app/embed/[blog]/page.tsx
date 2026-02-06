import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Feed } from '@/lib/types'
import EmbedForm from './embed-form'

export const dynamic = 'force-dynamic'

export default async function EmbedPage({
  params,
}: {
  params: Promise<{ blog: string }>
}) {
  const { blog: blogSlug } = await params
  const supabase = await createClient()

  // Get the blog
  const { data: blog } = await supabase
    .from('blogs')
    .select('id, slug, name, author')
    .eq('slug', blogSlug)
    .single()

  if (!blog) notFound()

  // Get all active feeds for this blog
  const { data: feeds } = await supabase
    .from('feeds')
    .select('id, slug, name, tag_filter, blog_id')
    .eq('blog_id', blog.id)
    .eq('is_active', true)
    .order('name')

  if (!feeds || feeds.length === 0) notFound()

  // Get post counts per feed
  const feedsWithCounts = await Promise.all(
    feeds.map(async (feed) => {
      if (feed.tag_filter) {
        const { count } = await supabase
          .from('posts')
          .select('*', { count: 'exact', head: true })
          .eq('blog_id', blog.id)
          .contains('tags', [feed.tag_filter])
        return { ...feed, post_count: count ?? 0 }
      }
      const { count } = await supabase
        .from('posts')
        .select('*', { count: 'exact', head: true })
        .eq('blog_id', blog.id)
      return { ...feed, post_count: count ?? 0 }
    })
  )

  return (
    <div className="p-4 max-w-md mx-auto">
      <EmbedForm
        blogId={blog.id}
        blogName={blog.name}
        author={blog.author}
        feeds={feedsWithCounts}
      />
    </div>
  )
}
