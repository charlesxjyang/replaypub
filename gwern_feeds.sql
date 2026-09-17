-- Create feeds for gwern.net, one per theme from the index page.
-- Run after: python backstack.py upload gwern_clean.json -s gwern -n "Gwern" -u https://gwern.net -a "Gwern Branwen"

INSERT INTO feeds (blog_id, name, slug, description, tag_filter, source_url, is_active)
SELECT b.id, v.name, v.slug, v.description, v.tag_filter, 'https://gwern.net/index', true
FROM blogs b
CROSS JOIN (VALUES
  ('Gwern — Popular',               'gwern-popular',               'The most-read essays from gwern.net.',                                        'Popular'),
  ('Gwern — Notable',               'gwern-notable',               'Curated notable essays from gwern.net.',                                      'Notable'),
  ('Gwern — Statistics',            'gwern-statistics',            'Data analysis, forecasting, and statistical methods.',                         'Statistics'),
  ('Gwern — Meta-Science',          'gwern-meta-science',          'Research methodology, replication, and scientific critique.',                  'Meta-Science'),
  ('Gwern — Decision Theory',       'gwern-decision-theory',       'Choice, optimization, prediction markets, and A/B testing.',                  'Decision Theory'),
  ('Gwern — Order Statistics',      'gwern-order-statistics',      'Selection, ranking, and finding the best.',                                   'Order Statistics'),
  ('Gwern — Crypto/Bitcoin',        'gwern-crypto-bitcoin',        'Cryptocurrency, darknet markets, and cryptography.',                          'Crypto/Bitcoin'),
  ('Gwern — AI Safety',             'gwern-ai-safety',             'Artificial intelligence safety and alignment.',                               'AI Safety'),
  ('Gwern — Generative AI: Image',  'gwern-generative-ai-image',   'Neural network image generation, GANs, and visual AI.',                      'Generative AI: Image'),
  ('Gwern — Generative AI: Fiction','gwern-generative-ai-fiction',  'LLM creative writing and AI-generated fiction.',                             'Generative AI: Fiction'),
  ('Gwern — Generative AI: Poetry', 'gwern-generative-ai-poetry',  'AI-generated poetry and verse.',                                             'Generative AI: Poetry'),
  ('Gwern — Deep Learning',         'gwern-deep-learning',         'Neural network research, scaling, and architectures.',                        'Deep Learning'),
  ('Gwern — Computer Science',      'gwern-computer-science',      'Turing completeness, archiving, sorting, and computing.',                    'Computer Science'),
  ('Gwern — Haskell',               'gwern-haskell',               'Functional programming with Haskell.',                                       'Haskell'),
  ('Gwern — Cognition',             'gwern-cognition',             'Spaced repetition, dual n-back, IQ, and learning.',                          'Cognition'),
  ('Gwern — Psychology',            'gwern-psychology',            'Behavioral science, mental health, and cognitive biases.',                    'Psychology'),
  ('Gwern — Behavior Genetics',     'gwern-behavior-genetics',     'Embryo selection, heritability, and evolutionary genetics.',                  'Behavior Genetics'),
  ('Gwern — Economics',             'gwern-economics',             'Economic analysis, copyright, and incentives.',                               'Economics'),
  ('Gwern — Economics: Tech',       'gwern-economics-tech',        'Technology sector economics, complements, and Moore''s law.',                 'Economics: Tech'),
  ('Gwern — Domestic Cats',         'gwern-domestic-cats',         'Catnip research, cat behavior, and feline science.',                         'Domestic Cats'),
  ('Gwern — Practical',             'gwern-practical',             'Practical advice: internet search, longevity, and daily life.',               'Practical'),
  ('Gwern — Design',                'gwern-design',                'Web design, typography, and visual style.',                                   'Design'),
  ('Gwern — QS: Sleep',             'gwern-qs-sleep',              'Sleep experiments: melatonin, modafinil, and Zeo data.',                     'QS: Sleep'),
  ('Gwern — QS',                    'gwern-qs',                    'Quantified self experiments: nootropics, supplements, and self-tracking.',   'QS'),
  ('Gwern — Politics',              'gwern-politics',              'Political analysis, terrorism, and social dynamics.',                         'Politics'),
  ('Gwern — Epistemology',          'gwern-epistemology',          'Knowledge, belief, reasoning errors, and community design.',                  'Epistemology'),
  ('Gwern — Philosophy',            'gwern-philosophy',            'Ethics, aesthetics, and philosophical inquiry.',                              'Philosophy'),
  ('Gwern — Literary Criticism',    'gwern-literary-criticism',    'Analysis of fiction, film, and narrative.',                                   'Literary Criticism'),
  ('Gwern — Anime',                 'gwern-anime',                 'Anime criticism, Death Note analysis, and otaku culture.',                   'Anime'),
  ('Gwern — Fiction: Prose',        'gwern-fiction-prose',         'Original short fiction and prose.',                                           'Fiction: Prose'),
  ('Gwern — Fiction: Verse',        'gwern-fiction-verse',         'Original poetry and verse.',                                                  'Fiction: Verse'),
  ('Gwern — Docs',                  'gwern-docs',                  'Archived documents and curated collections.',                                'Docs'),
  ('Gwern — Docs: Science',         'gwern-docs-science',          'Archived scientific papers and essays.',                                     'Docs: Science'),
  ('Gwern — Docs: Crypto',          'gwern-docs-crypto',           'Archived cryptography and cryptocurrency documents.',                        'Docs: Crypto'),
  ('Gwern — Docs: Anime',           'gwern-docs-anime',            'Archived anime essays and interviews.',                                      'Docs: Anime'),
  ('Gwern — Docs: NGE',             'gwern-docs-nge',              'Neon Genesis Evangelion production documents and interviews.',                'Docs: NGE'),
  ('Gwern — Wikipedia',             'gwern-wikipedia',             'Essays on Wikipedia editing, culture, and policy.',                           'Wikipedia')
) AS v(name, slug, description, tag_filter)
WHERE b.slug = 'gwern';
