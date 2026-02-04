-- Backstack Schema Additions
-- Run this in Supabase SQL editor AFTER schema.sql

-- ============================================
-- BLOG REQUESTS: User-submitted blog suggestions
-- ============================================

CREATE TYPE blog_request_status AS ENUM ('pending', 'approved', 'rejected', 'scraped');

CREATE TABLE blog_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    requester_email TEXT,
    requester_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    note TEXT,
    vote_count INTEGER DEFAULT 1,
    status blog_request_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique index on normalized URL for deduplication
CREATE UNIQUE INDEX idx_blog_requests_url ON blog_requests (lower(url));

-- Index for sorting by votes
CREATE INDEX idx_blog_requests_votes ON blog_requests (vote_count DESC, created_at);

-- RLS policies for blog_requests
ALTER TABLE blog_requests ENABLE ROW LEVEL SECURITY;

-- Anyone can read blog requests (for vote counts)
CREATE POLICY "Blog requests are publicly readable" ON blog_requests
    FOR SELECT USING (true);

-- Authenticated users can insert
CREATE POLICY "Authenticated users can create requests" ON blog_requests
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- VOTE / UPSERT RPC
-- ============================================

CREATE OR REPLACE FUNCTION vote_for_blog_request(
    p_url TEXT,
    p_email TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_request_id UUID;
    v_user_id UUID;
BEGIN
    v_user_id := auth.uid();

    -- Try to find existing request with this URL
    SELECT id INTO v_request_id
    FROM blog_requests
    WHERE lower(url) = lower(p_url);

    IF v_request_id IS NOT NULL THEN
        -- Increment vote count
        UPDATE blog_requests
        SET vote_count = vote_count + 1,
            updated_at = NOW()
        WHERE id = v_request_id;
    ELSE
        -- Create new request
        INSERT INTO blog_requests (url, requester_email, requester_id, note, vote_count)
        VALUES (p_url, p_email, v_user_id, NULL, 1)
        RETURNING id INTO v_request_id;
    END IF;

    RETURN v_request_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- AUTH TRIGGER: Auto-create subscriber on signup
-- ============================================

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO subscribers (id, email, is_confirmed, confirmed_at)
    VALUES (
        NEW.id,
        NEW.email,
        true,  -- Magic link already verifies email
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();
