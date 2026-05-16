-- Create L.M. Sacasas "The Frailest Thing" feed
-- Steps:
--   1. Run this SQL in Supabase SQL editor
--   2. python backstack.py upload sacasas_clean.json -s lm-sacasas -n "The Frailest Thing" -u "https://thefrailestthing.com" -a "L.M. Sacasas"

-- 1. Blog row (stores posts)
INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'lm-sacasas',
    'The Frailest Thing',
    'L.M. Sacasas',
    'https://thefrailestthing.com',
    'L.M. Sacasas writes on technology, culture, and the moral life. A humanist technology critic drawing on history, philosophy, and close attention to everyday experience, Sacasas asks not just what technology does but what it does to us. 100 essays.',
    100,
    true
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    author = EXCLUDED.author,
    url = EXCLUDED.url,
    description = EXCLUDED.description,
    post_count = EXCLUDED.post_count,
    updated_at = NOW();

-- 2. Feed row (what the website displays and users subscribe to)
INSERT INTO feeds (blog_id, name, slug, description, source_url, is_active)
SELECT b.id,
       'The Frailest Thing',
       'lm-sacasas-frailest-thing',
       'L.M. Sacasas writes on technology, culture, and the moral life. A humanist technology critic drawing on history, philosophy, and close attention to everyday experience, Sacasas asks not just what technology does but what it does to us. 100 essays.',
       'https://thefrailestthing.com',
       true
FROM blogs b WHERE b.slug = 'lm-sacasas'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
