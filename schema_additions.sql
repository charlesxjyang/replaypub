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

-- ============================================
-- SUBSCRIPTION SCHEDULING PREFERENCES
-- ============================================

ALTER TABLE subscriptions
  ADD COLUMN IF NOT EXISTS preferred_day SMALLINT CHECK (preferred_day BETWEEN 0 AND 6),
  ADD COLUMN IF NOT EXISTS preferred_hour SMALLINT DEFAULT 9 CHECK (preferred_hour BETWEEN 0 AND 23),
  ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'America/New_York';

-- Update mark_subscription_sent to respect scheduling preferences
CREATE OR REPLACE FUNCTION mark_subscription_sent(
    p_subscription_id UUID,
    p_post_id UUID,
    p_resend_message_id TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_frequency_days INTEGER;
    v_current_index INTEGER;
    v_total_posts INTEGER;
    v_preferred_day SMALLINT;
    v_preferred_hour SMALLINT;
    v_tz TEXT;
    v_next_send TIMESTAMPTZ;
    v_next_local TIMESTAMP;
BEGIN
    -- Get subscription details
    SELECT s.frequency_days, s.current_post_index, b.post_count,
           s.preferred_day, COALESCE(s.preferred_hour, 9), COALESCE(s.timezone, 'America/New_York')
    INTO v_frequency_days, v_current_index, v_total_posts,
         v_preferred_day, v_preferred_hour, v_tz
    FROM subscriptions s
    JOIN blogs b ON s.blog_id = b.id
    WHERE s.id = p_subscription_id;

    -- Log the email
    INSERT INTO email_log (subscription_id, post_id, resend_message_id)
    VALUES (p_subscription_id, p_post_id, p_resend_message_id);

    -- Calculate next send time in user's local timezone
    v_next_local := (NOW() AT TIME ZONE v_tz) + (v_frequency_days || ' days')::INTERVAL;
    -- Snap to preferred hour
    v_next_local := date_trunc('day', v_next_local) + (v_preferred_hour || ' hours')::INTERVAL;

    -- If preferred_day is set and frequency >= 7, snap to next occurrence of that weekday
    IF v_preferred_day IS NOT NULL AND v_frequency_days >= 7 THEN
        -- Advance to the next occurrence of preferred_day
        WHILE EXTRACT(DOW FROM v_next_local) != v_preferred_day LOOP
            v_next_local := v_next_local + INTERVAL '1 day';
        END LOOP;
    END IF;

    -- Convert back to UTC for storage
    v_next_send := v_next_local AT TIME ZONE v_tz;

    -- Update subscription
    UPDATE subscriptions
    SET
        current_post_index = v_current_index + 1,
        last_sent_at = NOW(),
        next_send_at = v_next_send,
        is_completed = (v_current_index + 1 >= v_total_posts),
        updated_at = NOW()
    WHERE id = p_subscription_id;
END;
$$ LANGUAGE plpgsql;
