-- Create Christian Millotat "Understanding the Prussian-German General Staff System" feed
-- Steps:
--   1. Run this SQL in the Supabase SQL editor
--   2. python backstack.py upload prussian_staff_clean.json -s prussian-german-general-staff \
--        -n "Understanding the Prussian-German General Staff System" \
--        -u "https://bootcampmilitaryfitnessinstitute.com/wp-content/uploads/2015/07/41-understanding-the-prussian-german-general-staff-system-millotat-1992.pdf" \
--        -a "Christian O.E. Millotat"

-- 1. Blog row (stores posts)
INSERT INTO blogs (slug, name, author, url, description, post_count, is_active)
VALUES (
    'prussian-german-general-staff',
    'Understanding the Prussian-German General Staff System',
    'Christian O.E. Millotat',
    'https://bootcampmilitaryfitnessinstitute.com/wp-content/uploads/2015/07/41-understanding-the-prussian-german-general-staff-system-millotat-1992.pdf',
    'Colonel Christian Millotat of the German Army wrote this 1992 study at the U.S. Army War College for the Strategic Studies Institute. It traces the Prussian-German General Staff from Scharnhorst and Gneisenau through Moltke, Schlieffen, Versailles and the Third Reich to the Bundeswehr of today — and explains what makes the German "commander''s adviser" unlike any other staff officer in NATO. 18 sections.',
    18,
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
       'The Prussian-German General Staff',
       'millotat-prussian-german-general-staff',
       'Colonel Christian Millotat of the German Army wrote this 1992 study at the U.S. Army War College for the Strategic Studies Institute. It traces the Prussian-German General Staff from Scharnhorst and Gneisenau through Moltke, Schlieffen, Versailles and the Third Reich to the Bundeswehr of today — and explains what makes the German "commander''s adviser" unlike any other staff officer in NATO. 18 sections.',
       'https://bootcampmilitaryfitnessinstitute.com/wp-content/uploads/2015/07/41-understanding-the-prussian-german-general-staff-system-millotat-1992.pdf',
       true
FROM blogs b WHERE b.slug = 'prussian-german-general-staff'
ON CONFLICT (slug) DO UPDATE SET
    description = EXCLUDED.description,
    source_url = EXCLUDED.source_url,
    is_active = EXCLUDED.is_active;
