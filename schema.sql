-- Backstack Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- BLOGS: The archives we're serving
-- ============================================
CREATE TABLE blogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,              -- e.g., 'samzdat', 'ribbonfarm'
    name TEXT NOT NULL,                     -- Display name
    author TEXT,                            -- Original author name
    author_email TEXT,                      -- For revenue share payments
    description TEXT,
    url TEXT NOT NULL,                      -- Original blog URL
    post_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,         -- Can users subscribe?
    revenue_share_percent INTEGER DEFAULT 50,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- POSTS: Individual blog posts
-- ============================================
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    
    -- Content
    title TEXT NOT NULL,
    slug TEXT NOT NULL,                     -- URL slug
    content_html TEXT NOT NULL,             -- Cleaned HTML for email
    content_text TEXT,                      -- Plain text fallback
    excerpt TEXT,                           -- First ~200 chars
    original_url TEXT NOT NULL,
    
    -- Ordering
    published_at TIMESTAMPTZ NOT NULL,      -- Original publish date
    post_index INTEGER NOT NULL,            -- 1, 2, 3... for drip ordering
    
    -- Metadata
    word_count INTEGER,
    reading_time_minutes INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(blog_id, post_index),
    UNIQUE(blog_id, slug)
);

CREATE INDEX idx_posts_blog_index ON posts(blog_id, post_index);

-- ============================================
-- SUBSCRIBERS: Users (handled by Supabase Auth)
-- ============================================
-- We use Supabase Auth for user management
-- This table extends auth.users with additional fields
CREATE TABLE subscribers (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    is_confirmed BOOLEAN DEFAULT false,     -- Double opt-in confirmed
    confirmation_token TEXT,
    confirmed_at TIMESTAMPTZ,
    is_pro BOOLEAN DEFAULT false,           -- Paid tier
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- SUBSCRIPTIONS: Links subscribers to blogs
-- ============================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id UUID NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    
    -- Drip state
    current_post_index INTEGER DEFAULT 0,   -- Last sent post (0 = not started)
    frequency_days INTEGER DEFAULT 7,       -- Days between emails
    next_send_at TIMESTAMPTZ,               -- When to send next
    last_sent_at TIMESTAMPTZ,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_completed BOOLEAN DEFAULT false,     -- Finished the archive
    paused_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(subscriber_id, blog_id)
);

CREATE INDEX idx_subscriptions_next_send ON subscriptions(next_send_at) 
    WHERE is_active = true AND is_completed = false;

-- ============================================
-- EMAIL_LOG: Track what we've sent
-- ============================================
CREATE TABLE email_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    resend_message_id TEXT,                 -- For tracking/debugging
    
    -- Engagement (populated via webhooks)
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ
);

CREATE INDEX idx_email_log_subscription ON email_log(subscription_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Get subscriptions due for sending
CREATE OR REPLACE FUNCTION get_due_subscriptions()
RETURNS TABLE (
    subscription_id UUID,
    subscriber_email TEXT,
    subscriber_name TEXT,
    blog_name TEXT,
    blog_slug TEXT,
    post_id UUID,
    post_title TEXT,
    post_content_html TEXT,
    post_index INTEGER,
    total_posts INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS subscription_id,
        sub.email AS subscriber_email,
        sub.name AS subscriber_name,
        b.name AS blog_name,
        b.slug AS blog_slug,
        p.id AS post_id,
        p.title AS post_title,
        p.content_html AS post_content_html,
        s.current_post_index + 1 AS post_index,
        b.post_count AS total_posts
    FROM subscriptions s
    JOIN subscribers sub ON s.subscriber_id = sub.id
    JOIN blogs b ON s.blog_id = b.id
    JOIN posts p ON p.blog_id = b.id 
        AND p.post_index = s.current_post_index + 1
    WHERE s.is_active = true
        AND s.is_completed = false
        AND sub.is_confirmed = true
        AND s.next_send_at <= NOW();
END;
$$ LANGUAGE plpgsql;

-- Mark a subscription as sent
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
BEGIN
    -- Get subscription details
    SELECT s.frequency_days, s.current_post_index, b.post_count
    INTO v_frequency_days, v_current_index, v_total_posts
    FROM subscriptions s
    JOIN blogs b ON s.blog_id = b.id
    WHERE s.id = p_subscription_id;
    
    -- Log the email
    INSERT INTO email_log (subscription_id, post_id, resend_message_id)
    VALUES (p_subscription_id, p_post_id, p_resend_message_id);
    
    -- Update subscription
    UPDATE subscriptions
    SET 
        current_post_index = v_current_index + 1,
        last_sent_at = NOW(),
        next_send_at = NOW() + (v_frequency_days || ' days')::INTERVAL,
        is_completed = (v_current_index + 1 >= v_total_posts),
        updated_at = NOW()
    WHERE id = p_subscription_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Subscribers can only see their own data
CREATE POLICY "Users can view own subscriber data" ON subscribers
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own subscriber data" ON subscribers
    FOR UPDATE USING (auth.uid() = id);

-- Subscriptions: users can manage their own
CREATE POLICY "Users can view own subscriptions" ON subscriptions
    FOR SELECT USING (auth.uid() = subscriber_id);

CREATE POLICY "Users can insert own subscriptions" ON subscriptions
    FOR INSERT WITH CHECK (auth.uid() = subscriber_id);

CREATE POLICY "Users can update own subscriptions" ON subscriptions
    FOR UPDATE USING (auth.uid() = subscriber_id);

CREATE POLICY "Users can delete own subscriptions" ON subscriptions
    FOR DELETE USING (auth.uid() = subscriber_id);

-- Blogs and posts are public read
CREATE POLICY "Blogs are publicly readable" ON blogs
    FOR SELECT USING (true);

CREATE POLICY "Posts are publicly readable" ON posts
    FOR SELECT USING (true);

-- ============================================
-- SEED DATA (example)
-- ============================================

-- INSERT INTO blogs (slug, name, author, url, description)
-- VALUES (
--     'samzdat',
--     'sam[ ]zdat',
--     'Anonymous',
--     'https://samzdat.com',
--     'Systems thinking, civilization critique, and the Uruk Machine'
-- );
