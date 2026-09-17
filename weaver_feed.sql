-- Create Warren Weaver "Scene of Change" feed
-- Steps:
--   1. Run this SQL in Supabase SQL editor
--   2. python backstack.py upload weaver_clean.json -s warren-weaver -n "Scene of Change" -u "https://gwern.net/doc/ai/1970-weaver-sceneofchangealifetimeinamericanscience.pdf" -a "Warren Weaver"

-- 1. Blog row (stores posts)
INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'warren-weaver',
    'Scene of Change',
    'Warren Weaver',
    'https://gwern.net/doc/ai/1970-weaver-sceneofchangealifetimeinamericanscience.pdf',
    'Warren Weaver''s 1970 autobiography spanning a lifetime in American science — from small-town Wisconsin through Caltech, the Rockefeller Foundation, wartime operations research, and reflections on the nature and limits of science. 11 chapters.',
    11,
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
       'Scene of Change',
       'warren-weaver-scene-of-change',
       'Warren Weaver''s 1970 autobiography spanning a lifetime in American science — from small-town Wisconsin through Caltech, the Rockefeller Foundation, wartime operations research, and reflections on the nature and limits of science. 11 chapters.',
       'https://gwern.net/doc/ai/1970-weaver-sceneofchangealifetimeinamericanscience.pdf',
       true
FROM blogs b WHERE b.slug = 'warren-weaver'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
