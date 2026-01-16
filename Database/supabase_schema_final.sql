-- 4Sight Platform - Complete Supabase PostgreSQL Schema
-- Consolidate Schema Version
-- Generated for Supabase Migration

-- ============================================
-- DATABASE SETUP
-- ============================================

-- Note: Supabase creates the database for you. 
-- We will proceed with creating tables in the public schema.

-- ============================================
-- CORE TABLES
-- ============================================

-- 1. users - User Accounts (Email-based UUID)
CREATE TABLE IF NOT EXISTS users (
    -- Primary Identity (from email hash)
    id VARCHAR(50) PRIMARY KEY,  -- user_abc123def456
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    
    -- Authentication
    password_hash VARCHAR(255) NULL,  -- NULL until onboarding complete
    google_user_id VARCHAR(255) UNIQUE NULL,
    
    -- Profile
    profile_picture_url TEXT NULL,
    
    -- Account Status
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    account_type VARCHAR(50) DEFAULT 'standard',  -- 'standard' or 'oauth'
    
    -- Onboarding Progress
    onboarding_completed BOOLEAN DEFAULT FALSE,
    current_onboarding_page INTEGER DEFAULT 1,
    credentials_sent BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    CONSTRAINT chk_account_type CHECK (account_type IN ('standard', 'oauth'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_user_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);


-- 2. oauth_tokens - OAuth Token Storage
CREATE TABLE IF NOT EXISTS oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Encrypted Tokens
    encrypted_refresh_token TEXT NOT NULL,
    
    -- Token Metadata
    provider VARCHAR(50) DEFAULT 'google',
    scopes TEXT[],
    
    -- Timestamps
    token_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_expires_at TIMESTAMP NULL,
    last_refreshed_at TIMESTAMP NULL,
    
    UNIQUE(user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);


-- 3. email_verification_tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_token_expiry CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_email_verification_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_user_id ON email_verification_tokens(user_id);


-- 4. password_reset_tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_token_expiry CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id);


-- ============================================
-- ONBOARDING TABLES
-- ============================================

-- 5. business_profiles - Page 1
CREATE TABLE IF NOT EXISTS business_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Business Info
    business_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(500) NOT NULL,
    business_description TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_business_profiles_user_id ON business_profiles(user_id);


-- 6. integrations - Page 2
CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Google Search Console
    gsc_connected BOOLEAN DEFAULT FALSE,
    gsc_verified_site VARCHAR(500) NULL,
    gsc_last_validated TIMESTAMP NULL,
    
    -- Google Analytics 4
    ga4_connected BOOLEAN DEFAULT FALSE,
    ga4_property_id VARCHAR(100) NULL,
    ga4_property_name VARCHAR(255) NULL,
    ga4_stream_url VARCHAR(500) NULL,
    ga4_last_validated TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integrations_user_id ON integrations(user_id);


-- 7. audience_profiles - Page 3
CREATE TABLE IF NOT EXISTS audience_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Location
    location_scope VARCHAR(100) NOT NULL,
    selected_locations TEXT[],
    
    -- Customer Info
    customer_description TEXT NOT NULL,
    
    -- Search Intent
    search_intent TEXT[] NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_search_intent_count CHECK (array_length(search_intent, 1) BETWEEN 1 AND 2)
);

CREATE INDEX IF NOT EXISTS idx_audience_profiles_user_id ON audience_profiles(user_id);


-- 8. products - Page 4 (Individual Products)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Product Info
    product_name VARCHAR(255) NOT NULL,
    product_url VARCHAR(500) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);


-- 9. services - Page 4 (Individual Services)
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Service Info
    service_name VARCHAR(255) NOT NULL,
    service_url VARCHAR(500) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_services_user_id ON services(user_id);


-- 10. differentiators - Page 4 (Business Differentiators)
CREATE TABLE IF NOT EXISTS differentiators (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Differentiator
    differentiator TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_differentiators_user_id ON differentiators(user_id);


-- 11. seo_goals - Page 5
CREATE TABLE IF NOT EXISTS seo_goals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    goals TEXT[] NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_seo_goals_user_id ON seo_goals(user_id);


-- 12. onboarding_keywords - Page 6
CREATE TABLE IF NOT EXISTS onboarding_keywords (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Keyword Data
    keyword VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'generated' or 'custom'
    is_selected BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    score DECIMAL(5,2) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, keyword),
    CONSTRAINT chk_keyword_source CHECK (source IN ('generated', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_onboarding_keywords_user_id ON onboarding_keywords(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_keywords_selected ON onboarding_keywords(user_id, is_selected);


-- 13. onboarding_competitors - Page 6
CREATE TABLE IF NOT EXISTS onboarding_competitors (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Competitor Info
    competitor_url VARCHAR(500) NOT NULL,
    competitor_name VARCHAR(255) NULL,
    source VARCHAR(50) NOT NULL,  -- 'suggested' or 'manual'
    is_selected BOOLEAN DEFAULT FALSE,
    
    -- Analysis Metadata
    priority VARCHAR(20) NULL,
    importance_score INTEGER NULL,
    keywords_matched TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, competitor_url),
    CONSTRAINT chk_competitor_source CHECK (source IN ('suggested', 'manual'))
);

CREATE INDEX IF NOT EXISTS idx_onboarding_competitors_user_id ON onboarding_competitors(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_competitors_selected ON onboarding_competitors(user_id, is_selected);


-- 14. page_urls - Page 7
CREATE TABLE IF NOT EXISTS page_urls (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Page URLs
    home_url VARCHAR(500) NOT NULL,
    product_url VARCHAR(500) NOT NULL,
    contact_url VARCHAR(500) NOT NULL,
    about_url VARCHAR(500) NOT NULL,
    blog_url VARCHAR(500) NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_page_urls_user_id ON page_urls(user_id);


-- 15. reporting_preferences - Page 8
CREATE TABLE IF NOT EXISTS reporting_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Reporting Config (Email removed as it's in users table)
    reporting_channels TEXT[] NOT NULL,
    report_frequency VARCHAR(50) NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reporting_preferences_user_id ON reporting_preferences(user_id);


-- ============================================
-- STRATEGY DASHBOARD TABLES
-- ============================================

-- 16. keyword_universes - Keyword Planner Lock Status
CREATE TABLE IF NOT EXISTS keyword_universes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Lock Status
    is_locked BOOLEAN DEFAULT FALSE,
    locked_until DATE NULL,
    selection_count INTEGER DEFAULT 0,
    
    -- GSC Exclusion Tracking
    gsc_excluded_keywords TEXT[],
    gsc_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_keyword_universes_user_id ON keyword_universes(user_id);


-- 17. keyword_universe_items - Keyword Planner Keywords
CREATE TABLE IF NOT EXISTS keyword_universe_items (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Keyword Data
    keyword VARCHAR(255) NOT NULL,
    search_volume INTEGER DEFAULT 0,
    difficulty VARCHAR(20) NOT NULL,
    intent VARCHAR(50) NOT NULL,
    keyword_type VARCHAR(50) NOT NULL,
    
    -- Source Tracking
    source VARCHAR(50) DEFAULT 'generated',  -- 'verified', 'generated', 'custom'
    score DECIMAL(5,2) NULL,
    
    -- Selection Status
    is_selected BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, keyword),
    CONSTRAINT chk_difficulty CHECK (difficulty IN ('Low', 'Medium', 'High')),
    CONSTRAINT chk_intent CHECK (intent IN ('Transactional', 'Informational')),
    CONSTRAINT chk_keyword_type CHECK (keyword_type IN ('Transactional', 'Informational', 'Branded', 'Long-tail')),
    CONSTRAINT chk_source CHECK (source IN ('verified', 'generated', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_keyword_universe_items_user_id ON keyword_universe_items(user_id);
CREATE INDEX IF NOT EXISTS idx_keyword_universe_items_selected ON keyword_universe_items(user_id, is_selected);


-- 18. strategy_goals - Goal Setting & Tracking
CREATE TABLE IF NOT EXISTS strategy_goals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Goal Identification
    goal_type VARCHAR(50) NOT NULL,  -- 'organic-traffic', 'keyword-rankings', 'serp-features', etc.
    goal_category VARCHAR(20) NOT NULL,  -- 'priority' or 'additional'
    
    -- Cycle Management
    cycle_start_date DATE NOT NULL,
    cycle_end_date DATE NOT NULL,  -- 90 days from start
    is_locked BOOLEAN DEFAULT TRUE,
    
    -- Status (for governance tracking)
    status VARCHAR(20) DEFAULT 'on_track',  -- 'on_track', 'paused', 'completed', 'at_risk'
    
    -- Metrics
    baseline_value VARCHAR(100) NULL,  -- Current value at cycle start
    current_value VARCHAR(100) NULL,   -- Updated monthly
    target_value VARCHAR(100) NOT NULL,  -- Target for this cycle
    
    -- Metadata
    unit VARCHAR(50) NOT NULL,  -- 'visitors/month', 'DA points', etc.
    target_type VARCHAR(20) NOT NULL,  -- 'growth', 'range', 'slabs', 'paused'
    
    -- For keyword-rankings goal (slab distribution)
    slab_data JSONB DEFAULT NULL,
    
    -- Progress Tracking
    progress_percentage FLOAT DEFAULT 0.0,
    last_calculated_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uix_user_goal_cycle UNIQUE (user_id, goal_type, cycle_start_date),
    CONSTRAINT chk_goal_type CHECK (goal_type IN (
        'organic-traffic', 'keyword-rankings', 'serp-features', 
        'avg-position', 'impressions', 'domain-authority'
    )),
    CONSTRAINT chk_goal_category CHECK (goal_category IN ('priority', 'additional')),
    CONSTRAINT chk_target_type CHECK (target_type IN ('growth', 'range', 'slabs', 'paused')),
    CONSTRAINT chk_goal_status CHECK (status IN ('on_track', 'paused', 'completed', 'at_risk'))
);

CREATE INDEX IF NOT EXISTS idx_strategy_goals_user ON strategy_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_goals_cycle ON strategy_goals(user_id, cycle_start_date);
CREATE INDEX IF NOT EXISTS idx_strategy_goals_active ON strategy_goals(user_id, is_locked) WHERE is_locked = TRUE;


-- 19. goal_milestones - Monthly milestones for goal tracking
CREATE TABLE IF NOT EXISTS goal_milestones (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES strategy_goals(id) ON DELETE CASCADE,
    month_number INTEGER NOT NULL CHECK (month_number IN (1, 2, 3)),
    target_value VARCHAR(100) NOT NULL,
    actual_value VARCHAR(100),
    achieved BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(goal_id, month_number)
);

CREATE INDEX IF NOT EXISTS idx_goal_milestones_goal_id ON goal_milestones(goal_id);


-- 20. goal_progress_snapshots - Daily/weekly snapshots for goal trends
CREATE TABLE IF NOT EXISTS goal_progress_snapshots (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES strategy_goals(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    current_value VARCHAR(100) NOT NULL,
    progress_percentage FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(goal_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal_id ON goal_progress_snapshots(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_snapshots_date ON goal_progress_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal_date ON goal_progress_snapshots(goal_id, snapshot_date DESC);


-- ============================================
-- AS-IS STATE TABLES
-- ============================================

-- 21. gsc_daily_metrics - GSC data snapshots
CREATE TABLE IF NOT EXISTS gsc_daily_metrics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    metric_type VARCHAR(20) NOT NULL,
    query_or_page TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr FLOAT DEFAULT 0.0,
    position FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_gsc_metrics UNIQUE (user_id, snapshot_date, period_type, metric_type, query_or_page)
);

CREATE INDEX IF NOT EXISTS idx_gsc_metrics_user_date ON gsc_daily_metrics(user_id, snapshot_date);





-- 23. keyword_position_snapshots - Position history
CREATE TABLE IF NOT EXISTS keyword_position_snapshots (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    snapshot_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    position FLOAT NULL,
    position_change FLOAT NULL,
    in_top10 BOOLEAN DEFAULT FALSE,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_keyword_snapshots_user ON keyword_position_snapshots(user_id, snapshot_date);


-- 24. serp_feature_presence - SERP features per keyword
CREATE TABLE IF NOT EXISTS serp_feature_presence (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    feature_type VARCHAR(50) NOT NULL,
    domain_present BOOLEAN DEFAULT FALSE,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_serp_features_user ON serp_feature_presence(user_id, snapshot_date);


-- 25. competitor_visibility_scores - Competitor rankings
CREATE TABLE IF NOT EXISTS competitor_visibility_scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competitor_domain VARCHAR(255) NOT NULL,
    visibility_score FLOAT DEFAULT 0.0,
    rank INTEGER NULL,
    score_factors TEXT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_competitor_scores_user ON competitor_visibility_scores(user_id, snapshot_date);


-- 26. crawl_pages - Crawled page metadata
CREATE TABLE IF NOT EXISTS crawl_pages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    page_url VARCHAR(500) NOT NULL,
    last_crawled TIMESTAMP NULL,
    crawl_status VARCHAR(50) DEFAULT 'pending',
    http_status INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_crawl_page UNIQUE (user_id, page_url)
);

CREATE INDEX IF NOT EXISTS idx_crawl_pages_user ON crawl_pages(user_id);


-- 27. onpage_signals - On-page SEO signals
CREATE TABLE IF NOT EXISTS onpage_signals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    page_url VARCHAR(500) NOT NULL,
    title_tag TEXT NULL,
    title_length INTEGER DEFAULT 0,
    meta_description TEXT NULL,
    meta_description_length INTEGER DEFAULT 0,
    h1_count INTEGER DEFAULT 0,
    h1_text TEXT NULL,
    h2_count INTEGER DEFAULT 0,
    h3_count INTEGER DEFAULT 0,
    h4_count INTEGER DEFAULT 0,
    h5_count INTEGER DEFAULT 0,
    h6_count INTEGER DEFAULT 0,
    canonical_url VARCHAR(500) NULL,
    canonical_self_referencing BOOLEAN DEFAULT FALSE,
    first_100_words TEXT NULL,
    word_count INTEGER DEFAULT 0,
    internal_link_count INTEGER DEFAULT 0,
    external_link_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    images_with_alt INTEGER DEFAULT 0,
    images_without_alt INTEGER DEFAULT 0,
    url_length INTEGER DEFAULT 0,
    url_has_parameters BOOLEAN DEFAULT FALSE,
    url_depth INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_onpage_signal UNIQUE (user_id, page_url)
);

CREATE INDEX IF NOT EXISTS idx_onpage_signals_user ON onpage_signals(user_id);


-- 28. backlink_signals - Backlink data
CREATE TABLE IF NOT EXISTS backlink_signals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referring_domains INTEGER DEFAULT 0,
    total_backlinks INTEGER DEFAULT 0,
    dofollow_ratio FLOAT DEFAULT 0.0,
    anchor_text_distribution TEXT NULL,
    top_linking_sites TEXT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 29. technical_signals - Technical SEO signals
CREATE TABLE IF NOT EXISTS technical_signals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    indexed_pages INTEGER DEFAULT 0,
    submitted_pages INTEGER DEFAULT 0,
    index_coverage_ratio FLOAT DEFAULT 0.0,
    robots_txt_exists BOOLEAN DEFAULT FALSE,
    robots_txt_valid BOOLEAN DEFAULT FALSE,
    sitemap_exists BOOLEAN DEFAULT FALSE,
    sitemap_valid BOOLEAN DEFAULT FALSE,
    canonical_issues_count INTEGER DEFAULT 0,
    duplicate_title_count INTEGER DEFAULT 0,
    duplicate_description_count INTEGER DEFAULT 0,
    https_enabled BOOLEAN DEFAULT FALSE,
    mixed_content_issues INTEGER DEFAULT 0,
    trailing_slash_consistent BOOLEAN DEFAULT TRUE,
    www_consistent BOOLEAN DEFAULT TRUE,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 30. cwv_signals - Core Web Vitals
CREATE TABLE IF NOT EXISTS cwv_signals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url_group VARCHAR(500) DEFAULT 'site-wide',
    device_type VARCHAR(20) DEFAULT 'mobile',
    lcp_score FLOAT NULL,
    lcp_status VARCHAR(20) NULL,
    inp_score FLOAT NULL,
    inp_status VARCHAR(20) NULL,
    cls_score FLOAT NULL,
    cls_status VARCHAR(20) NULL,
    overall_status VARCHAR(20) NULL,
    good_urls_count INTEGER DEFAULT 0,
    needs_improvement_urls_count INTEGER DEFAULT 0,
    poor_urls_count INTEGER DEFAULT 0,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cwv_signals_user ON cwv_signals(user_id);


-- 31. ai_crawl_governance - AI crawler rules
CREATE TABLE IF NOT EXISTS ai_crawl_governance (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    robots_ai_rules TEXT NULL,
    llm_txt_detected BOOLEAN DEFAULT FALSE,
    llm_txt_content TEXT NULL,
    ai_crawlers_blocked TEXT NULL,
    ai_crawlers_allowed TEXT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 32. as_is_scores - Parameter scores
CREATE TABLE IF NOT EXISTS as_is_scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parameter_tab VARCHAR(20) NOT NULL,
    parameter_group VARCHAR(100) NOT NULL,
    sub_parameter VARCHAR(100) NULL,
    score FLOAT DEFAULT 0.0,
    max_score FLOAT DEFAULT 100.0,
    baseline_score FLOAT DEFAULT NULL, -- Added from migration
    is_baseline BOOLEAN DEFAULT FALSE,   -- Added from migration
    status VARCHAR(20) NOT NULL,
    details TEXT NULL,
    recommendation TEXT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_asis_score UNIQUE (user_id, parameter_tab, parameter_group, sub_parameter, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_asis_scores_user ON as_is_scores(user_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_asis_baseline ON as_is_scores(user_id, is_baseline, snapshot_date);


-- 33. as_is_summary_cache - Summary card cache (complete data storage)
CREATE TABLE IF NOT EXISTS as_is_summary_cache (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Aggregate values (for quick queries)
    total_clicks INTEGER DEFAULT 0,
    clicks_change FLOAT DEFAULT 0.0,
    total_impressions INTEGER DEFAULT 0,
    impressions_change FLOAT DEFAULT 0.0,
    avg_position FLOAT DEFAULT 0.0,
    position_change FLOAT DEFAULT 0.0,
    top10_keywords INTEGER DEFAULT 0,
    top10_change INTEGER DEFAULT 0,
    features_present TEXT NULL,
    features_count INTEGER DEFAULT 0,
    your_rank INTEGER NULL,
    total_competitors INTEGER DEFAULT 0,
    your_visibility_score FLOAT DEFAULT 0.0,
    
    -- JSONB columns for complete data storage (DB-first approach)
    full_summary JSONB NULL,              -- Complete summary as JSONB
    ranked_keywords JSONB NULL,           -- Keyword list with positions
    top_pages JSONB NULL,                 -- Top performing pages
    competitor_rankings JSONB NULL,       -- Competitor list with scores
    serp_features_detail JSONB NULL,      -- SERP features with status
    
    -- Baseline fields (for lock period)
    baseline_total_clicks INTEGER,
    baseline_total_impressions INTEGER,
    baseline_avg_position FLOAT,
    baseline_top10_keywords INTEGER,
    baseline_features_count INTEGER,
    baseline_your_rank INTEGER,
    baseline_visibility_score FLOAT,
    baseline_captured_at TIMESTAMP,
    
    -- Domain Authority (for Goal Setting)
    domain_authority INTEGER DEFAULT 0,
    baseline_domain_authority INTEGER NULL,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_as_is_summary_full_summary ON as_is_summary_cache USING GIN (full_summary);


-- 34. asis_progress_timeline - Timeline of performance changes and improvements
CREATE TABLE IF NOT EXISTS asis_progress_timeline (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Event Information
    event_type VARCHAR(50) NOT NULL,  -- 'score_improvement', 'metric_change', 'milestone', etc.
    event_title VARCHAR(500) NOT NULL,
    event_description TEXT NULL,
    
    -- Categorization
    category VARCHAR(20) NULL,  -- 'onpage', 'offpage', 'technical', 'overall'
    parameter_group VARCHAR(100) NULL,
    
    -- Metrics
    metric_name VARCHAR(100) NULL,
    old_value FLOAT NULL,
    new_value FLOAT NULL,
    change_delta FLOAT NULL,
    
    -- Timestamp
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_event_type CHECK (event_type IN ('score_improvement', 'score_decline', 'metric_change', 'milestone', 'baseline_captured'))
);

CREATE INDEX IF NOT EXISTS idx_timeline_user ON asis_progress_timeline(user_id, event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_timeline_category ON asis_progress_timeline(user_id, category);


-- ============================================
-- ACTION PLAN TABLES
-- ============================================

-- 35. action_plan_tasks - SEO action plan tasks
CREATE TABLE IF NOT EXISTS action_plan_tasks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Task Information
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT NULL,
    category VARCHAR(20) NOT NULL,  -- 'onpage', 'offpage', 'technical'
    
    -- Priority & Effort
    priority VARCHAR(20) NOT NULL,  -- 'high', 'medium', 'low'
    impact_score FLOAT DEFAULT 0.0,
    effort_score FLOAT DEFAULT 0.0,
    
    -- Status Tracking
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed'
    
    -- Categorization
    parameter_group VARCHAR(100) NULL,  -- Links to AS-IS parameter groups
    sub_parameter VARCHAR(100) NULL,
    
    -- Goal Alignment
    related_goal VARCHAR(255) NULL,
    
    -- Metrics
    affected_pages_count INTEGER DEFAULT 0,
    
    -- Metadata
    impact_description TEXT NULL,
    effort_description VARCHAR(50) NULL,  -- 'Low', 'Medium', 'High'
    recommendation TEXT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    CONSTRAINT chk_category CHECK (category IN ('onpage', 'offpage', 'technical')),
    CONSTRAINT chk_priority CHECK (priority IN ('high', 'medium', 'low')),
    CONSTRAINT chk_status CHECK (status IN ('not_started', 'in_progress', 'completed')),
    CONSTRAINT chk_effort CHECK (effort_description IN ('Low', 'Medium', 'High'))
);

CREATE INDEX IF NOT EXISTS idx_action_plan_tasks_user ON action_plan_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_action_plan_tasks_category ON action_plan_tasks(user_id, category);
CREATE INDEX IF NOT EXISTS idx_action_plan_tasks_priority ON action_plan_tasks(user_id, priority);
CREATE INDEX IF NOT EXISTS idx_action_plan_tasks_status ON action_plan_tasks(user_id, status);


-- 36. action_plan_task_pages - Junction table for task-page relationships
CREATE TABLE IF NOT EXISTS action_plan_task_pages (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES action_plan_tasks(id) ON DELETE CASCADE,
    page_url VARCHAR(500) NOT NULL,
    
    -- Issue Details
    issue_description TEXT NULL,
    current_value TEXT NULL,
    recommended_value TEXT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_pages_task ON action_plan_task_pages(task_id);
CREATE INDEX IF NOT EXISTS idx_task_pages_url ON action_plan_task_pages(page_url);


-- 37. action_plan_task_history - Audit trail for task status changes
CREATE TABLE IF NOT EXISTS action_plan_task_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES action_plan_tasks(id) ON DELETE CASCADE,
    
    -- Status Change
    old_status VARCHAR(20) NULL,
    new_status VARCHAR(20) NOT NULL,
    
    -- Notes
    notes TEXT NULL,
    
    -- Timestamp
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_old_status CHECK (old_status IN ('not_started', 'in_progress', 'completed')),
    CONSTRAINT chk_new_status CHECK (new_status IN ('not_started', 'in_progress', 'completed'))
);

CREATE INDEX IF NOT EXISTS idx_task_history_task ON action_plan_task_history(task_id);


-- 38. action_plan_progress_snapshots - Historical tracking for governance
CREATE TABLE IF NOT EXISTS action_plan_progress_snapshots (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Snapshot Date
    snapshot_date DATE NOT NULL,
    cycle_start_date DATE NOT NULL,  -- Links to 90-day cycle
    
    -- Overall Metrics
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    in_progress_tasks INTEGER DEFAULT 0,
    completion_percentage FLOAT DEFAULT 0.0,
    
    -- Category Breakdown
    onpage_total INTEGER DEFAULT 0,
    onpage_completed INTEGER DEFAULT 0,
    onpage_percentage FLOAT DEFAULT 0.0,
    
    -- Category Breakdown
    offpage_total INTEGER DEFAULT 0,
    offpage_completed INTEGER DEFAULT 0,
    offpage_percentage FLOAT DEFAULT 0.0,
    
    -- Category Breakdown
    technical_total INTEGER DEFAULT 0,
    technical_completed INTEGER DEFAULT 0,
    technical_percentage FLOAT DEFAULT 0.0,
    
    -- Baseline Flag
    is_baseline BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uix_user_snapshot_date UNIQUE (user_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_action_plan_progress_user ON action_plan_progress_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_action_plan_progress_cycle ON action_plan_progress_snapshots(user_id, cycle_start_date);
CREATE INDEX IF NOT EXISTS idx_action_plan_progress_baseline ON action_plan_progress_snapshots(user_id, is_baseline) WHERE is_baseline = TRUE;

