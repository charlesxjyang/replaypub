-- Create Isaiah Berlin, "The Hedgehog and the Fox" feed
-- Steps:
--   1. python extract_berlin.py                     -> berlin_clean.json (41 posts)
--   2. python backstack.py upload berlin_clean.json -s berlin-hedgehog-fox \
--        -n "The Hedgehog and the Fox" \
--        -u "https://www.arvindguptatoys.com/arvindgupta/hedgehog-berlin.pdf" \
--        -a "Isaiah Berlin"
--   3. Run this SQL (blog description + feeds row); `upload` never writes either.

INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'berlin-hedgehog-fox',
    'The Hedgehog and the Fox',
    'Isaiah Berlin',
    'https://www.arvindguptatoys.com/arvindgupta/hedgehog-berlin.pdf',
    'Isaiah Berlin''s 1953 essay on Tolstoy''s view of history. It begins from a line of Archilochus — the fox knows many things, but the hedgehog knows one big thing — and turns it into a division that runs through all of literature and thought. Berlin''s thesis is that Tolstoy was by nature a fox who believed in being a hedgehog, and that this is what the philosophy of history in War and Peace is really about; the later sections trace Tolstoy''s unacknowledged debt to Joseph de Maistre, the Savoyard reactionary he resembled far more than he could have borne to know. 41 readings from the first edition; the footnotes are omitted.',
    41,
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
       'The Hedgehog and the Fox',
       'berlin-hedgehog-fox',
       'Isaiah Berlin''s 1953 essay on Tolstoy''s view of history. It begins from a line of Archilochus — the fox knows many things, but the hedgehog knows one big thing — and turns it into a division that runs through all of literature and thought. Berlin''s thesis is that Tolstoy was by nature a fox who believed in being a hedgehog, and that this is what the philosophy of history in War and Peace is really about; the later sections trace Tolstoy''s unacknowledged debt to Joseph de Maistre, the Savoyard reactionary he resembled far more than he could have borne to know. 41 readings from the first edition; the footnotes are omitted.',
       'https://www.arvindguptatoys.com/arvindgupta/hedgehog-berlin.pdf',
       true
FROM blogs b WHERE b.slug = 'berlin-hedgehog-fox'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
