import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Blog, Post } from '@/lib/types'
import SubscribeButton from './subscribe-button'
import PostList from './post-list'

export const dynamic = 'force-dynamic'

async function getBlog(slug: string) {
  const supabase = await createClient()
  const { data: blog } = await supabase
    .from('blogs')
    .select('*')
    .eq('slug', slug)
    .single()
  return blog as Blog | null
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const blog = await getBlog(slug)
  if (!blog) return {}

  const title = blog.name
  const description = blog.description || `Read ${blog.post_count} posts from ${blog.name}${blog.author ? ` by ${blog.author}` : ''} on Replay.`

  return {
    title,
    description,
    openGraph: { title, description },
    twitter: { title, description },
    alternates: { canonical: `/blogs/${slug}` },
  }
}

export default async function BlogDetail({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const blog = await getBlog(slug)

  if (!blog) notFound()

  const supabase = await createClient()

  const { data: posts } = await supabase
    .from('posts')
    .select('id, title, excerpt, post_index, reading_time_minutes, tags')
    .eq('blog_id', blog.id)
    .order('post_index')

  const {
    data: { user },
  } = await supabase.auth.getUser()

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: blog.name,
    description: blog.description ?? undefined,
    url: `https://replay.pub/blogs/${slug}`,
    ...(blog.author ? { author: { '@type': 'Person', name: blog.author } } : {}),
  }

  // Collect unique tags across all posts
  const allTags = Array.from(
    new Set((posts as Post[] ?? []).flatMap((p) => p.tags ?? []))
  ).sort()

  return (
    <>
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold mb-2">{blog.name}</h1>
      {blog.author && (
        <p className="text-gray-500 mb-2">by {blog.author}</p>
      )}
      {blog.description && (
        <p className="text-gray-600 mb-4">{blog.description}</p>
      )}
      <p className="text-sm text-gray-400 mb-8">
        {blog.post_count} posts
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
    </>
  )
}
