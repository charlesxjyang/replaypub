#!/usr/bin/env python3
"""
Replay CLI - manage your drip email service.

Usage:
    python backstack.py scrape https://samzdat.com -o posts.json
    python backstack.py clean posts.json -b https://samzdat.com
    python backstack.py upload posts_cleaned.json -s samzdat -n "sam[ ]zdat"
    python backstack.py check
    python backstack.py send --dry-run
"""

import os
import sys
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Replay - Great blogs, delivered over time."""
    pass


@cli.command()
@click.argument('url')
@click.option('--output', '-o', default='posts.json', help='Output file')
@click.option('--verbose', '-v', is_flag=True)
def scrape(url, output, verbose):
    """Extract posts from a blog URL."""
    from scraper.extract import BlogExtractor
    import json
    
    click.echo(f"Extracting posts from {url}...")
    
    extractor = BlogExtractor(url, verbose=verbose)
    posts = extractor.extract()
    
    if not posts:
        click.echo("No posts found!")
        sys.exit(1)
    
    # Save with post_index
    data = [p.to_dict() | {'post_index': i} for i, p in enumerate(posts, 1)]
    
    with open(output, 'w') as f:
        json.dump(data, f, indent=2)
    
    click.echo(f"Saved {len(posts)} posts to {output}")


@cli.command('scrape-illich')
@click.argument('book_url')
@click.option('--output', '-o', default='illich_posts.json', help='Output file')
@click.option('--verbose', '-v', is_flag=True)
def scrape_illich(book_url, output, verbose):
    """Extract chapters from an Illich book on henryzoo.com.

    Example:
        python backstack.py scrape-illich https://henryzoo.com/illich/celebration-of-awareness/
    """
    from scraper.extract import IllichExtractor
    import json

    click.echo(f"Extracting chapters from {book_url}...")

    extractor = IllichExtractor(book_url, verbose=verbose)
    posts = extractor.extract()

    if not posts:
        click.echo("No chapters found!")
        sys.exit(1)

    # Save with post_index
    data = [p.to_dict() | {'post_index': i} for i, p in enumerate(posts, 1)]

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)

    click.echo(f"Saved {len(posts)} chapters to {output}")


@cli.command('scrape-gwern')
@click.option('--output', '-o', default='gwern_raw.json', help='Output file')
@click.option('--verbose', '-v', is_flag=True)
def scrape_gwern(output, verbose):
    """Extract essays from gwern.net, tagged by index theme.

    Example:
        python backstack.py scrape-gwern -o gwern_raw.json -v
        python backstack.py clean gwern_raw.json -b https://gwern.net -o gwern_clean.json
        python backstack.py upload gwern_clean.json -s gwern -n "Gwern" -u https://gwern.net -a "Gwern Branwen"
    """
    from scraper.extract import GwernExtractor
    import json

    click.echo("Extracting essays from gwern.net...")

    extractor = GwernExtractor(verbose=verbose)
    posts = extractor.extract()

    if not posts:
        click.echo("No essays found!")
        sys.exit(1)

    data = [p.to_dict() | {'post_index': i} for i, p in enumerate(posts, 1)]

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)

    click.echo(f"Saved {len(posts)} essays to {output}")


@cli.command('scrape-rickover')
@click.option('--output', '-o', default='rickover_raw.json', help='Output file')
@click.option('--verbose', '-v', is_flag=True)
def scrape_rickover(output, verbose):
    """Extract speeches from rickovercorpus.org, tagged by theme.

    Example:
        python backstack.py scrape-rickover -o rickover_raw.json -v
        python backstack.py clean rickover_raw.json -b https://rickovercorpus.org -o rickover_clean.json
    """
    from scraper.extract import RickoverExtractor
    import json

    click.echo("Extracting speeches from rickovercorpus.org...")

    extractor = RickoverExtractor(verbose=verbose)
    posts = extractor.extract()

    if not posts:
        click.echo("No speeches found!")
        sys.exit(1)

    data = [p.to_dict() | {'post_index': i} for i, p in enumerate(posts, 1)]

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)

    click.echo(f"Saved {len(posts)} speeches to {output}")


@cli.command('scrape-curated')
@click.argument('links_file')
@click.option('--output', '-o', default='curated_raw.json', help='Output file')
@click.option('--verbose', '-v', is_flag=True)
def scrape_curated(links_file, output, verbose):
    """Extract articles from a curated list of URLs.

    LINKS_FILE should be a JSON array of objects with 'title', 'url', and optional 'author'.

    Example:
        python backstack.py scrape-curated joanne_peng_links.json -o joanne_raw.json -v
        python backstack.py clean joanne_raw.json -b https://example.com -o joanne_clean.json
    """
    from scraper.extract import CuratedExtractor
    import json

    with open(links_file) as f:
        links = json.load(f)

    click.echo(f"Extracting {len(links)} articles from curated list...")

    extractor = CuratedExtractor(links, verbose=verbose)
    posts = extractor.extract()

    if not posts:
        click.echo("No articles extracted!")
        sys.exit(1)

    data = [p.to_dict() | {'post_index': i} for i, p in enumerate(posts, 1)]

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)

    click.echo(f"Saved {len(posts)} articles to {output}")


@cli.command()
@click.argument('input_file')
@click.option('--output', '-o', help='Output file (default: input_cleaned.json)')
@click.option('--base-url', '-b', required=True, help='Blog base URL')
@click.option('--cdn-url', '-c', help='CDN URL for images')
@click.option('--verbose', '-v', is_flag=True)
def clean(input_file, output, base_url, cdn_url, verbose):
    """Clean extracted posts for email delivery."""
    from scraper.clean import HTMLCleaner
    import json
    
    if not output:
        output = input_file.replace('.json', '_cleaned.json')
    
    with open(input_file) as f:
        posts = json.load(f)
    
    click.echo(f"Cleaning {len(posts)} posts...")
    
    cleaner = HTMLCleaner(base_url, cdn_url, verbose)
    cleaned = []
    all_images = []
    
    for post in posts:
        if not post.get('content_html'):
            continue
        
        result = cleaner.clean(post['content_html'], post.get('title'))
        
        cleaned.append({
            **post,
            'content_html': result['html'],
            'content_text': result['text'],
            'excerpt': result['excerpt'],
            'word_count': result['word_count'],
            'reading_time_minutes': result['reading_time_minutes'],
        })
        all_images.extend(result['images'])
    
    with open(output, 'w') as f:
        json.dump(cleaned, f, indent=2)
    
    click.echo(f"Saved {len(cleaned)} cleaned posts to {output}")
    
    if all_images:
        images_file = output.replace('.json', '_images.json')
        with open(images_file, 'w') as f:
            json.dump(all_images, f, indent=2)
        click.echo(f"Saved {len(all_images)} image URLs to {images_file}")


@cli.command()
@click.argument('posts_file')
@click.option('--slug', '-s', required=True, help='Blog slug')
@click.option('--name', '-n', required=True, help='Blog display name')
@click.option('--url', '-u', required=True, help='Original blog URL')
@click.option('--author', '-a', help='Author name')
@click.option('--author-email', help='Author email')
@click.option('--dry-run', is_flag=True)
def upload(posts_file, slug, name, url, author, author_email, dry_run):
    """Upload posts to Supabase."""
    from supabase import create_client
    from datetime import datetime
    import json
    
    with open(posts_file) as f:
        posts = json.load(f)
    
    click.echo(f"Uploading {len(posts)} posts for {name}...")
    
    if dry_run:
        click.echo("[DRY RUN] Would upload:")
        click.echo(f"  Blog: {slug} ({name})")
        click.echo(f"  Posts: {len(posts)}")
        return
    
    supabase = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_KEY']
    )
    
    # Upsert blog
    blog_data = {
        'slug': slug,
        'name': name,
        'url': url,
        'author': author,
        'author_email': author_email,
        'post_count': len(posts),
        'updated_at': datetime.utcnow().isoformat(),
    }
    
    result = supabase.table('blogs').upsert(blog_data, on_conflict='slug').execute()
    blog_id = result.data[0]['id']
    
    click.echo(f"Blog ID: {blog_id}")
    
    # Upload posts
    for post in posts:
        post_data = {
            'blog_id': blog_id,
            'title': post['title'],
            'slug': post.get('slug', ''),
            'content_html': post.get('content_html', ''),
            'content_text': post.get('content_text', ''),
            'excerpt': post.get('excerpt', ''),
            'original_url': post['url'],
            'published_at': post.get('published_at'),
            'post_index': post['post_index'],
            'word_count': post.get('word_count'),
            'reading_time_minutes': post.get('reading_time_minutes'),
            'tags': post.get('tags', []),
        }
        
        supabase.table('posts').upsert(post_data, on_conflict='blog_id,post_index').execute()
    
    click.echo(f"Uploaded {len(posts)} posts")


@cli.command()
@click.option('--verbose', '-v', is_flag=True)
def check(verbose):
    """Check for subscriptions due for email."""
    from supabase import create_client
    
    supabase = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_KEY']
    )
    
    result = supabase.rpc('get_due_subscriptions').execute()
    due = result.data
    
    click.echo(f"Found {len(due)} subscriptions due for email")
    
    if verbose and due:
        for item in due:
            click.echo(f"  • {item['subscriber_email']}: {item['blog_name']} ({item['post_index']}/{item['total_posts']})")


@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview without sending')
@click.option('--limit', '-l', type=int, help='Limit number of emails')
@click.option('--verbose', '-v', is_flag=True)
def send(dry_run, limit, verbose):
    """Send due drip emails."""
    import resend
    from supabase import create_client
    
    resend.api_key = os.environ.get('RESEND_API_KEY')
    
    supabase = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_KEY']
    )
    
    result = supabase.rpc('get_due_subscriptions').execute()
    due = result.data
    
    if limit:
        due = due[:limit]
    
    click.echo(f"{'[DRY RUN] ' if dry_run else ''}Processing {len(due)} emails...")
    
    if not due:
        return
    
    # Import send logic
    from drip.send import render_email, send_email, mark_sent
    
    app_url = os.environ.get('APP_URL', 'https://replay.pub')
    from_email = os.environ.get('FROM_EMAIL', 'posts@replay.pub')
    reply_to = os.environ.get('REPLY_TO_EMAIL', 'hello@replay.pub')
    
    sent = 0
    for item in due:
        subject = f"{item['post_title']} — {item['blog_name']}"
        
        if verbose:
            click.echo(f"  {item['subscriber_email']}: {subject[:50]}...")
        
        if dry_run:
            sent += 1
            continue
        
        html = render_email(item, app_url)
        msg_id = send_email(
            item['subscriber_email'],
            item.get('subscriber_name'),
            subject, html, from_email, reply_to
        )
        
        if msg_id:
            mark_sent(supabase, item['subscription_id'], item['post_id'], msg_id)
            sent += 1
    
    click.echo(f"{'Would send' if dry_run else 'Sent'}: {sent}")


@cli.command()
@click.option('--email', '-e', required=True, help='Subscriber email')
@click.option('--blog', '-b', required=True, help='Blog slug')
@click.option('--frequency', '-f', default=7, help='Days between emails')
def subscribe(email, blog, frequency):
    """Add a test subscription (for development)."""
    from supabase import create_client
    from datetime import datetime, timedelta
    import uuid
    
    supabase = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_KEY']
    )
    
    # Get blog
    blog_result = supabase.table('blogs').select('id').eq('slug', blog).single().execute()
    if not blog_result.data:
        click.echo(f"Blog '{blog}' not found")
        sys.exit(1)
    
    blog_id = blog_result.data['id']
    
    # Create or get subscriber (using a fake auth user for testing)
    subscriber_id = str(uuid.uuid4())
    
    supabase.table('subscribers').upsert({
        'id': subscriber_id,
        'email': email,
        'is_confirmed': True,
        'confirmed_at': datetime.utcnow().isoformat(),
    }, on_conflict='id').execute()
    
    # Create subscription
    supabase.table('subscriptions').upsert({
        'subscriber_id': subscriber_id,
        'blog_id': blog_id,
        'current_post_index': 0,
        'frequency_days': frequency,
        'next_send_at': datetime.utcnow().isoformat(),  # Send immediately
        'is_active': True,
    }, on_conflict='subscriber_id,blog_id').execute()
    
    click.echo(f"Subscribed {email} to {blog} (every {frequency} days)")


if __name__ == '__main__':
    cli()
