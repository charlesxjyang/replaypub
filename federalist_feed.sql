-- Create The Federalist Papers feed (85 essays, one email per paper)
-- Source: The Avalon Project, Yale Law School — https://avalon.law.yale.edu/subject_menus/fed.asp
-- Steps:
--   1. Run this SQL in the Supabase SQL editor
--   2. python backstack.py upload federalist_clean.json -s federalist-papers -n "The Federalist Papers" \
--        -u "https://avalon.law.yale.edu/subject_menus/fed.asp" -a "Alexander Hamilton, James Madison, and John Jay"

-- 1. Blog row (owns the posts)
INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'federalist-papers',
    'The Federalist Papers',
    'Alexander Hamilton, James Madison, and John Jay',
    'https://avalon.law.yale.edu/subject_menus/fed.asp',
    'The 85 essays written in 1787–1788 by Alexander Hamilton, James Madison, and John Jay under the shared pseudonym "Publius" to urge ratification of the United States Constitution. Still the foundational exposition of American constitutional thought — the dangers of faction (No. 10), the separation of powers (No. 51), energy in the executive (No. 70), and judicial review (No. 78). One paper per email, in order. Text from the Avalon Project at Yale Law School.',
    85,
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
INSERT INTO feeds (blog_id, name, slug, description, tag_filter, source_url, post_count, is_active)
SELECT b.id,
       'The Federalist Papers',
       'federalist-papers',
       'The 85 essays written in 1787–1788 by Alexander Hamilton, James Madison, and John Jay under the shared pseudonym "Publius" to urge ratification of the United States Constitution. Still the foundational exposition of American constitutional thought — the dangers of faction (No. 10), the separation of powers (No. 51), energy in the executive (No. 70), and judicial review (No. 78). One paper per email, in order. Text from the Avalon Project at Yale Law School.',
       NULL,
       'https://avalon.law.yale.edu/subject_menus/fed.asp',
       85,
       true
FROM blogs b WHERE b.slug = 'federalist-papers'
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    post_count = EXCLUDED.post_count,
    is_active = EXCLUDED.is_active;
