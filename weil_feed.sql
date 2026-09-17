-- Create Simone Weil "Gravity and Grace" feed
-- Run this in your Supabase SQL editor, then use:
--   python backstack.py upload weil_clean.json -s simone-weil -n "Gravity and Grace" -u "https://ebooks-bnr.com/weil-simone-la-pesanteur-et-la-grace/" -a "Simone Weil"

INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'simone-weil',
    'Gravity and Grace',
    'Simone Weil',
    'https://ebooks-bnr.com/weil-simone-la-pesanteur-et-la-grace/',
    'Simone Weil''s masterwork of spiritual philosophy, drawn from her notebooks. 39 chapters of aphoristic meditations on gravity, grace, void, affliction, beauty, and the soul''s relationship to God. Translated from the French by AI.',
    39,
    true
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    author = EXCLUDED.author,
    url = EXCLUDED.url,
    description = EXCLUDED.description,
    post_count = EXCLUDED.post_count,
    updated_at = NOW();
