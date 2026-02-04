export interface Blog {
  id: string
  slug: string
  name: string
  author: string | null
  author_email: string | null
  description: string | null
  url: string
  post_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Feed {
  id: string
  blog_id: string
  name: string
  slug: string
  description: string | null
  tag_filter: string | null
  is_active: boolean
  created_at: string
  // Joined
  blogs?: Blog
}

export interface Post {
  id: string
  blog_id: string
  title: string
  slug: string
  content_html: string
  content_text: string | null
  excerpt: string | null
  original_url: string
  published_at: string | null
  post_index: number
  word_count: number | null
  reading_time_minutes: number | null
  tags: string[]
  created_at: string
}

export interface Subscription {
  id: string
  subscriber_id: string
  blog_id: string
  feed_id: string | null
  current_post_index: number
  frequency_days: number
  next_send_at: string | null
  last_sent_at: string | null
  is_active: boolean
  is_completed: boolean
  paused_at: string | null
  created_at: string
  updated_at: string
  // Joined fields
  blogs?: Blog
  feeds?: Feed
}

export interface BlogRequest {
  id: string
  url: string
  requester_email: string | null
  requester_id: string | null
  note: string | null
  vote_count: number
  status: 'pending' | 'approved' | 'rejected' | 'scraped'
  created_at: string
  updated_at: string
}
