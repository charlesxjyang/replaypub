import type { MetadataRoute } from 'next'
import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const supabase = await createClient()

  const staticPages: MetadataRoute.Sitemap = [
    { url: 'https://replay.pub', changeFrequency: 'weekly', priority: 1 },
    { url: 'https://replay.pub/request', changeFrequency: 'weekly', priority: 0.6 },
  ]

  const { data: feeds } = await supabase
    .from('feeds')
    .select('slug, created_at')
    .eq('is_active', true)

  const feedPages: MetadataRoute.Sitemap = (feeds ?? []).map((feed) => ({
    url: `https://replay.pub/feeds/${feed.slug}`,
    lastModified: feed.created_at,
    changeFrequency: 'monthly',
    priority: 0.8,
  }))

  const { data: blogs } = await supabase
    .from('blogs')
    .select('slug, updated_at')
    .eq('is_active', true)

  const blogPages: MetadataRoute.Sitemap = (blogs ?? []).map((blog) => ({
    url: `https://replay.pub/blogs/${blog.slug}`,
    lastModified: blog.updated_at,
    changeFrequency: 'monthly',
    priority: 0.7,
  }))

  return [...staticPages, ...feedPages, ...blogPages]
}
