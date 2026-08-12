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

-- 3. Backward-compatible columns for existing deployments
ALTER TABLE posted_articles ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE posted_articles ADD COLUMN IF NOT EXISTS link TEXT;

-- 4. Indexes for duplicate checks, dashboard queries and category filtering
CREATE INDEX IF NOT EXISTS idx_posted_at ON posted_articles(posted_at);
CREATE INDEX IF NOT EXISTS idx_fingerprint ON posted_articles(fingerprint);
CREATE INDEX IF NOT EXISTS idx_category ON posted_articles(category);
CREATE INDEX IF NOT EXISTS idx_posted_category_date ON posted_articles(category, posted_at DESC);

-- 5. Keep tables inaccessible to anonymous/public Supabase clients.
-- The server uses the service-role key, which bypasses RLS.
ALTER TABLE posted_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE retry_queue ENABLE ROW LEVEL SECURITY;
