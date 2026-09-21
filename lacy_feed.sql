-- Create Alex B. Lacy, Jr., "The Development of the White House Office, 1939-1967" feed
-- Steps:
--   1. python extract_lacy.py                      -> lacy_clean.json (28 posts)
--   2. python backstack.py upload lacy_clean.json -s lacy-white-house-office -n "The Development of the White House Office, 1939-1967" \
--        -u "https://www.nixonlibrary.gov/sites/default/files/virtuallibrary/documents/whsfreturned/WHSF_Box_39/WHSF39-04.pdf" -a "Alex B. Lacy, Jr."
--   3. Run this SQL (blog description + feeds row); `upload` never writes either.

INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'lacy-white-house-office',
    'The Development of the White House Office, 1939-1967',
    'Alex B. Lacy, Jr.',
    'https://www.nixonlibrary.gov/sites/default/files/virtuallibrary/documents/whsfreturned/WHSF_Box_39/WHSF39-04.pdf',
    'A 1967 American Political Science Association paper by Alex B. Lacy, Jr. of the University of Virginia, preserved in the Nixon Library''s White House Special Files. Drawing on interviews with the men who served, it traces the White House Office from the Brownlow Committee through Roosevelt, Truman, Eisenhower, Kennedy and Johnson: who the staff were, how each President organized them, and what the growth of the staff did to the Presidency. 28 short readings, with the paper''s five statistical tables.',
    28,
    true
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    author = EXCLUDED.author,
    url = EXCLUDED.url,
    description = EXCLUDED.description,
    post_count = EXCLUDED.post_count,
    updated_at = NOW();

INSERT INTO feeds (blog_id, name, slug, description, source_url, is_active)
SELECT b.id,
       'The Development of the White House Office',
       'lacy-white-house-office',
       'A 1967 American Political Science Association paper by Alex B. Lacy, Jr. of the University of Virginia, preserved in the Nixon Library''s White House Special Files. Drawing on interviews with the men who served, it traces the White House Office from the Brownlow Committee through Roosevelt, Truman, Eisenhower, Kennedy and Johnson: who the staff were, how each President organized them, and what the growth of the staff did to the Presidency. 28 short readings, with the paper''s five statistical tables.',
       'https://www.nixonlibrary.gov/sites/default/files/virtuallibrary/documents/whsfreturned/WHSF_Box_39/WHSF39-04.pdf',
       true
FROM blogs b WHERE b.slug = 'lacy-white-house-office'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
