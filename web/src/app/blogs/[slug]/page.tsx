import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Blog, Post } from '@/lib/types'
import SubscribeButton from './subscribe-button'
import PostList from './post-list'

export const dynamic = 'force-dynamic'

export default async function BlogDetail({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const supabase = await createClient()

  const { data: blog } = await supabase
    .from('blogs')
    .select('*')
    .eq('slug', slug)
    .single()

  if (!blog) notFound()

  const { data: posts } = await supabase
    .from('posts')
    .select('id, title, excerpt, post_index, reading_time_minutes, tags')
    .eq('blog_id', blog.id)
    .order('post_index')

  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Collect unique tags across all posts
  const allTags = Array.from(
    new Set((posts as Post[] ?? []).flatMap((p) => p.tags ?? []))
  ).sort()

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold mb-2">{(blog as Blog).name}</h1>
      {(blog as Blog).author && (
        <p className="text-gray-500 mb-2">by {(blog as Blog).author}</p>
      )}
      {(blog as Blog).description && (
        <p className="text-gray-600 mb-4">{(blog as Blog).description}</p>
      )}
      <p className="text-sm text-gray-400 mb-8">
        {(blog as Blog).post_count} posts
      </p>

      {/* Subscribe */}
      <div className="mb-10">
        <SubscribeButton blogId={blog.id} blogSlug={slug} isLoggedIn={!!user} />
      </div>

      {/* All posts with tag filter */}
      {posts && posts.length > 0 && (
        <PostList posts={posts as Post[]} tags={allTags} />
      )}
    </div>
  )
}
