import type { MetadataRoute } from 'next'
import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const supabase = await createClient()

  const staticPages: MetadataRoute.Sitemap = [
    { url: 'https://replaypub.vercel.app', changeFrequency: 'weekly', priority: 1 },
    { url: 'https://replaypub.vercel.app/request', changeFrequency: 'weekly', priority: 0.6 },
  ]

  const { data: feeds } = await supabase
    .from('feeds')
    .select('slug, created_at')
    .eq('is_active', true)

  const feedPages: MetadataRoute.Sitemap = (feeds ?? []).map((feed) => ({
    url: `https://replaypub.vercel.app/feeds/${feed.slug}`,
    lastModified: feed.created_at,
    changeFrequency: 'monthly',
    priority: 0.8,
  }))

  const { data: blogs } = await supabase
    .from('blogs')
    .select('slug, updated_at')
    .eq('is_active', true)

  const blogPages: MetadataRoute.Sitemap = (blogs ?? []).map((blog) => ({
    url: `https://replaypub.vercel.app/blogs/${blog.slug}`,
    lastModified: blog.updated_at,
    changeFrequency: 'monthly',
    priority: 0.7,
  }))

  return [...staticPages, ...feedPages, ...blogPages]
}
