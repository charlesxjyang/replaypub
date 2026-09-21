-- Create Martin Buber "I and Thou" feed (Ronald Gregor Smith's 1937 translation)
-- Steps:
--   1. python extract_buber.py                      -> buber_clean.json (61 short posts)
--   2. python backstack.py upload buber_clean.json -s martin-buber -n "I and Thou" \
--        -u "https://www.burmalibrary.org/docs21/Buber-c1923-I_And_Thou-ocr-tu.pdf" -a "Martin Buber"
--   3. Run this SQL (blog description + feeds row); `upload` never writes either.

-- 1. Blog row (stores posts)
INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'martin-buber',
    'I and Thou',
    'Martin Buber',
    'https://www.burmalibrary.org/docs21/Buber-c1923-I_And_Thou-ocr-tu.pdf',
    'Martin Buber''s 1923 Ich und Du in Ronald Gregor Smith''s 1937 English translation, the first in English. The world is twofold for man: the I-Thou relation of meeting and the I-It world of experience and use. Three parts, delivered as 61 short readings that follow Buber''s own star-separated sections.',
    61,
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
       'I and Thou',
       'buber-i-and-thou',
       'Martin Buber''s 1923 Ich und Du in Ronald Gregor Smith''s 1937 English translation, the first in English. The world is twofold for man: the I-Thou relation of meeting and the I-It world of experience and use. Three parts, delivered as 61 short readings that follow Buber''s own star-separated sections.',
       'https://www.burmalibrary.org/docs21/Buber-c1923-I_And_Thou-ocr-tu.pdf',
       true
FROM blogs b WHERE b.slug = 'martin-buber'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
