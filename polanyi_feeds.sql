-- Create Michael Polanyi blog and feeds for Duke + Wesleyan lectures
-- Steps:
--   1. python backstack.py upload polanyi_clean.json -s michael-polanyi -n "Michael Polanyi" -u "https://www.polanyisociety.org/essays.htm" -a "Michael Polanyi"
--   2. Run this SQL in Supabase SQL editor

-- Feeds (blog row created by upload command above)
INSERT INTO feeds (blog_id, name, slug, description, tag_filter, source_url, is_active)
SELECT b.id, v.name, v.slug, v.description, v.tag_filter, v.source_url, true
FROM blogs b
CROSS JOIN (VALUES
  ('Polanyi — Duke Lectures (1964)',
   'polanyi-duke-lectures',
   'Five lectures delivered at Duke University in February–March 1964 as the James B. Duke Distinguished Professor. Covers the metaphysical reach of science, tacit knowing, commitment, emergence, and thought in society.',
   'duke-lectures',
   'https://www.polanyisociety.org/Duke-intro.pdf'),
  ('Polanyi — Wesleyan Lectures (1965)',
   'polanyi-wesleyan-lectures',
   'Five lectures delivered at Wesleyan University in fall 1965 on "Man''s Place in the Universe." Covers science and reality, tacit knowing, creative imagination, science in society, and levels of reality.',
   'wesleyan-lectures',
   'https://www.polanyisociety.org/WesleyanLectures/WesleyanLecturesIntro.htm')
) AS v(name, slug, description, tag_filter, source_url)
WHERE b.slug = 'michael-polanyi'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    tag_filter = EXCLUDED.tag_filter,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
