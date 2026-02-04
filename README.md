# Backstack

A "Substack for archives" — subscribe to retired blogs and receive posts drip-fed to your inbox as if you were reading them in real-time.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKSTACK MVP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Scraper   │───▶│  Supabase   │◀───│   Cron Job  │         │
│  │  (one-time) │    │  Database   │    │   (daily)   │         │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘         │
│                            │                   │                │
│                            ▼                   ▼                │
│                     ┌─────────────┐    ┌─────────────┐         │
│                     │  Landing    │    │   Resend    │         │
│                     │   Page      │    │   (email)   │         │
│                     └─────────────┘    └─────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Service | Cost |
|-----------|---------|------|
| Database + Auth | Supabase | $0 (free tier) |
| Email delivery | Resend | $0 (3k/month free) |
| Daily cron | GitHub Actions | $0 |
| Image hosting | Cloudflare R2 | $0 (10GB free) |
| Landing page | Vercel/Netlify | $0 |
| **Total** | | **~$12/year** (domain only) |

## Project Structure

```
backstack/
├── scraper/
│   ├── extract.py       # Pull posts from blogs (sitemap, WP API, or crawl)
│   ├── clean.py         # Sanitize HTML for email
│   └── upload.py        # Push to Supabase + R2
├── drip/
│   ├── check_due.py     # Find subscribers due for email
│   └── send.py          # Render and send via Resend
├── templates/
│   └── email.mjml       # Email template
├── sql/
│   └── schema.sql       # Supabase database schema
├── .github/
│   └── workflows/
│       └── daily_drip.yml
├── requirements.txt
└── .env.example
```

## Quick Start

1. Set up Supabase project and run `sql/schema.sql`
2. Set up Resend account and get API key
3. Configure `.env` with credentials
4. Run scraper on target blog: `python scraper/extract.py https://samzdat.com`
5. Sign up a test subscriber in Supabase
6. Test drip: `python drip/send.py --dry-run`

## Database Schema

Three core tables:
- `blogs` — metadata about each archive
- `posts` — the actual content, ordered by original publish date
- `subscriptions` — links subscribers to blogs, tracks current position

## Email Flow

1. Daily cron wakes up at 8am UTC
2. Queries subscriptions where `next_send_at <= now()`
3. For each due subscription:
   - Fetch the next post
   - Render into MJML template
   - Send via Resend
   - Increment `current_post_index`
   - Set `next_send_at` based on frequency

## Content Extraction Priority

For each blog, try in order:
1. `/sitemap.xml` — lists all URLs
2. WordPress REST API — `/wp-json/wp/v2/posts`
3. Archive/index page — scrape links
4. Wayback Machine CDX API — for dead blogs
5. Full crawl — last resort

## License

MIT
