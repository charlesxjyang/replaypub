import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Replay',
    short_name: 'Replay',
    description: 'Subscribe to classic blog archives and receive posts as a drip email series.',
    start_url: '/',
    display: 'browser',
    background_color: '#ffffff',
    theme_color: '#ffffff',
  }
}
