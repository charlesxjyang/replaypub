ALTER TABLE blogs
  ADD COLUMN IF NOT EXISTS has_live_original_urls BOOLEAN NOT NULL DEFAULT true;

UPDATE blogs SET has_live_original_urls = false WHERE slug = 'lm-sacasas';
