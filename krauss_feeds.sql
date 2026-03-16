-- Create feed for The Engine of Scientific Discovery by Alexander Krauss
-- Prerequisites: python backstack.py upload krauss_clean.json -s krauss-engine-of-discovery -n "Alexander Krauss" -u "https://personal.lse.ac.uk/kraussa/The%20Engine%20of%20Scientific%20Discovery.pdf" -a "Alexander Krauss"

INSERT INTO feeds (blog_id, name, slug, description, source_url, is_active)
SELECT b.id,
       'The Engine of Scientific Discovery',
       'krauss-engine-of-discovery',
       'How new methods and tools spark major breakthroughs. Alexander Krauss analyses science''s 750+ biggest discoveries and finds that powerful new tools — from microscopes and particle accelerators to statistical methods — are the key driver behind nearly every major breakthrough.',
       'https://personal.lse.ac.uk/kraussa/The%20Engine%20of%20Scientific%20Discovery.pdf',
       true
FROM blogs b
WHERE b.slug = 'krauss-engine-of-discovery'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
