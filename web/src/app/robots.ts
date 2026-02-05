import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/dashboard', '/subscribe/', '/unsubscribe', '/api/', '/auth/'],
    },
    sitemap: 'https://replay.pub/sitemap.xml',
  }
}
