# Replay

Great blogs, delivered over time. Subscribe to classic blog archives and receive posts as a drip email series.

**Live at [replay.pub](https://replay.pub)**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           REPLAY                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Scraper   │───▶│  Supabase   │◀───│   Cron Job  │         │
│  │  (one-time) │    │  Database   │    │   (daily)   │         │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘         │
│                            │                   │                │
│                            ▼                   ▼                │
│                     ┌─────────────┐    ┌─────────────┐         │
│                     │  Next.js    │    │   Resend    │         │
│                     │  Frontend   │    │   (email)   │         │
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
| Frontend | Vercel | $0 |
| **Total** | | **~$12/year** (domain only) |

## Project Structure

```
replay/
├── scraper/
│   ├── extract.py       # Pull posts from blogs (sitemap, WP API, or crawl)
│   └── clean.py         # Sanitize HTML for email
├── drip/
│   └── send.py          # Render and send via Resend
├── web/                  # Next.js frontend
├── templates/
│   └── email.mjml       # Email template
├── schema.sql           # Supabase database schema
├── .github/
│   └── workflows/
│       └── daily_drip.yml
├── backstack.py         # CLI tool
├── requirements.txt
└── .env.example
```

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## License

MIT
