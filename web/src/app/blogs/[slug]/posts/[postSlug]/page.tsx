import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { Blog, Post } from '@/lib/types'

export const dynamic = 'force-dynamic'

async function getBlogAndPost(blogSlug: string, postSlug: string) {
  const supabase = await createClient()
  const { data: blog } = await supabase
    .from('blogs')
    .select('*')
    .eq('slug', blogSlug)
    .single()
  if (!blog) return { blog: null, post: null }
  const { data: post } = await supabase
    .from('posts')
    .select('*')
    .eq('blog_id', blog.id)
    .eq('slug', postSlug)
    .single()
  return { blog: blog as Blog, post: post as Post | null }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string; postSlug: string }>
}): Promise<Metadata> {
  const { slug, postSlug } = await params
  const { blog, post } = await getBlogAndPost(slug, postSlug)
  if (!blog || !post) return {}

  const title = `${post.title} — ${blog.name}`
  const description = post.excerpt ?? `${post.title} by ${blog.author ?? blog.name}`

  return {
    title,
    description,
    openGraph: { title, description, type: 'article' },
    twitter: { title, description },
    alternates: { canonical: `/blogs/${slug}/posts/${postSlug}` },
  }
}

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string; postSlug: string }>
}) {
  const { slug, postSlug } = await params
  const { blog, post } = await getBlogAndPost(slug, postSlug)

  if (!blog || !post) notFound()

  const hasLiveOriginal = blog.has_live_original_urls && !!post.original_url
  const publishedDate = post.published_at
    ? new Date(post.published_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  return (
    <article className="max-w-2xl mx-auto px-4 py-12">
      <nav className="mb-8 text-sm">
        <Link
          href={`/blogs/${slug}`}
          className="text-gray-500 hover:text-gray-900 transition-colors"
        >
          ← {blog.name}
        </Link>
      </nav>

      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-3 leading-tight">
          {hasLiveOriginal ? (
            <a
              href={`${post.original_url}${post.original_url.includes('?') ? '&' : '?'}utm_source=replay`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 transition-colors"
            >
              {post.title}
              <span className="text-gray-400 ml-2 text-xl">↗</span>
            </a>
          ) : (
            post.title
          )}
        </h1>
        <div className="text-sm text-gray-500 flex flex-wrap items-center gap-x-3 gap-y-1">
          {blog.author && <span>by {blog.author}</span>}
          {publishedDate && <span>· {publishedDate}</span>}
          {post.reading_time_minutes && (
            <span>· {post.reading_time_minutes} min read</span>
          )}
        </div>
      </header>

      <div
        className="post-content text-gray-900 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: post.content_html }}
      />

      <footer className="mt-12 pt-6 border-t border-gray-200 text-sm text-gray-500">
        <p>
          {hasLiveOriginal ? (
            <>
              Originally published at{' '}
              <a
                href={`${post.original_url}${post.original_url.includes('?') ? '&' : '?'}utm_source=replay`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {new URL(post.original_url).hostname}
              </a>
              {blog.author ? ` by ${blog.author}.` : '.'}
            </>
          ) : (
            <>
              Republished from{' '}
              <a
                href={blog.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {blog.name}
              </a>
              {blog.author ? ` by ${blog.author}.` : '.'}
            </>
          )}
        </p>
      </footer>

      <style>{`
        .post-content h1, .post-content h2, .post-content h3, .post-content h4 {
          font-weight: 600;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          line-height: 1.3;
        }
        .post-content h1 { font-size: 1.5rem; }
        .post-content h2 { font-size: 1.3rem; }
        .post-content h3 { font-size: 1.15rem; }
        .post-content p {
          margin-bottom: 1em;
          line-height: 1.7;
        }
        .post-content a {
          color: #2563eb;
          text-decoration: underline;
        }
        .post-content a:hover {
          color: #1d4ed8;
        }
        .post-content ul, .post-content ol {
          margin-bottom: 1em;
          padding-left: 1.5em;
        }
        .post-content ul { list-style: disc; }
        .post-content ol { list-style: decimal; }
        .post-content li { margin-bottom: 0.25em; }
        .post-content blockquote {
          border-left: 3px solid #e5e7eb;
          padding-left: 1em;
          margin: 1em 0;
          color: #4b5563;
          font-style: italic;
        }
        .post-content img {
          max-width: 100%;
          height: auto;
          margin: 1em 0;
          border-radius: 0.375rem;
        }
        .post-content pre {
          background: #f3f4f6;
          padding: 1em;
          border-radius: 0.375rem;
          overflow-x: auto;
          margin: 1em 0;
          font-size: 0.9em;
        }
        .post-content code {
          background: #f3f4f6;
          padding: 0.1em 0.3em;
          border-radius: 0.25rem;
          font-size: 0.9em;
        }
        .post-content pre code {
          background: transparent;
          padding: 0;
        }
        .post-content hr {
          border: 0;
          border-top: 1px solid #e5e7eb;
          margin: 2em 0;
        }
      `}</style>
    </article>
  )
}
