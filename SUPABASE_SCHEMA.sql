-- SQL for Supabase Table Structure

-- 1. Table for posted articles
CREATE TABLE IF NOT EXISTS posted_articles (
    id TEXT PRIMARY KEY, -- article_id (hash)
    title TEXT,
    fingerprint TEXT,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    facebook BOOLEAN DEFAULT FALSE,
    telegram BOOLEAN DEFAULT FALSE,
    source TEXT,
    category TEXT CHECK (category IN ('finance', 'technology', 'business')),
    link TEXT
);

-- 2. Table for retry queue
CREATE TABLE IF NOT EXISTS retry_queue (
    id BIGSERIAL PRIMARY KEY,
    article_id TEXT,
    article_data JSONB,
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT
);

-- 3. Index for performance
CREATE INDEX IF NOT EXISTS idx_posted_at ON posted_articles(posted_at);
CREATE INDEX IF NOT EXISTS idx_fingerprint ON posted_articles(fingerprint);
CREATE INDEX IF NOT EXISTS idx_category ON posted_articles(category);
