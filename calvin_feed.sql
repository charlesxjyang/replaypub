-- Create John Calvin "Institutes of the Christian Religion" feed
-- Run this in your Supabase SQL editor after uploading:
--   python backstack.py upload calvin_clean.json -s john-calvin -n "Institutes of the Christian Religion" -u "https://www.ccel.org/ccel/calvin/institutes.html" -a "John Calvin"

INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'john-calvin',
    'Institutes of the Christian Religion',
    'John Calvin',
    'https://www.ccel.org/ccel/calvin/institutes.html',
    'Calvin''s magnum opus, first published in 1536 and revised throughout his life. A systematic exposition of Protestant theology in four books: the knowledge of God the Creator, the knowledge of God the Redeemer, the mode of obtaining the grace of Christ, and the holy catholic church. 80 chapters in the Beveridge translation.',
    80,
    true
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    author = EXCLUDED.author,
    url = EXCLUDED.url,
    description = EXCLUDED.description,
    post_count = EXCLUDED.post_count,
    updated_at = NOW();

-- After uploading posts, create the feed entry:
INSERT INTO feeds (blog_id, name, slug, description, source_url)
SELECT
    id,
    'Institutes of the Christian Religion',
    'institutes-of-the-christian-religion',
    'Calvin''s magnum opus, first published in 1536 and revised throughout his life. A systematic exposition of Protestant theology in four books: the knowledge of God the Creator, the knowledge of God the Redeemer, the mode of obtaining the grace of Christ, and the holy catholic church. 80 chapters in the Beveridge translation.',
    'https://www.ccel.org/ccel/calvin/institutes.html'
FROM blogs
WHERE slug = 'john-calvin'
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url;
