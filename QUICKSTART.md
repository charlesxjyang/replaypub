# Replay Quick Start

Get your MVP running in ~30 minutes.

## 1. Set Up Services (10 min)

### Supabase
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Go to **SQL Editor** and paste the contents of `sql/schema.sql`
3. Click **Run**
4. Go to **Settings → API** and copy:
   - Project URL → `SUPABASE_URL`
   - `anon` key → `SUPABASE_ANON_KEY`  
   - `service_role` key → `SUPABASE_SERVICE_KEY`

### Resend
1. Go to [resend.com](https://resend.com) and sign up
2. Go to **API Keys** and create a new key
3. Copy → `RESEND_API_KEY`
4. (Optional) Add a custom domain for better deliverability

## 2. Configure Environment (2 min)

```bash
cp .env.example .env
```

Edit `.env` with your values:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
RESEND_API_KEY=re_xxxxx
FROM_EMAIL=posts@yourdomain.com
APP_URL=https://replay.pub
```

## 3. Install Dependencies (2 min)

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

## 4. Scrape Your First Blog (5 min)

```bash
# Extract posts
python backstack.py scrape https://samzdat.com -o samzdat.json -v

# Clean for email
python backstack.py clean samzdat.json -b https://samzdat.com -o samzdat_clean.json

# Upload to Supabase
python backstack.py upload samzdat_clean.json \
  --slug samzdat \
  --name "sam[ ]zdat" \
  --url https://samzdat.com \
  --author "Anonymous"
```

## 5. Test Subscription (5 min)

```bash
# Add yourself as a test subscriber
python backstack.py subscribe -e your@email.com -b samzdat -f 1

# Check what's due
python backstack.py check -v

# Send (dry run first!)
python backstack.py send --dry-run -v

# Actually send
python backstack.py send -v
```

Check your inbox!

## 6. Set Up Automation (5 min)

### Option A: GitHub Actions (recommended)
1. Push to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add secrets:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `RESEND_API_KEY`
4. Add variables:
   - `FROM_EMAIL`
   - `REPLY_TO_EMAIL`
   - `APP_URL`
5. The workflow runs daily at 8am UTC automatically

### Option B: Local cron
```bash
# Add to crontab
0 8 * * * cd /path/to/backstack && ./venv/bin/python backstack.py send
```

---

## Common Issues

### "No posts found"
- Try different extraction methods: sitemap → WP API → archive page
- Some blogs need manual scraping (check `scraper/extract.py`)

### Emails going to spam
- Add SPF/DKIM records (Resend docs)
- Use a custom domain
- Start with low volume

### Rate limits
- Resend free tier: 3k emails/month
- Supabase free tier: 500MB database, 2GB bandwidth

---

## Next Steps

1. **Landing page**: Build a simple signup form with Supabase Auth
2. **More blogs**: Reach out to authors, get permission
3. **Payments**: Add Stripe for the Pro tier
4. **Analytics**: Track opens/clicks via Resend webhooks
