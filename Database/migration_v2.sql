-- Migration to add AS-IS STATE tables (Tables 18-30 from schema v2.0)

-- 18. gsc_daily_metrics - GSC data snapshots
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


-- 19. tracked_keywords - User's tracked keywords
CREATE TABLE IF NOT EXISTS tracked_keywords (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    is_tracked BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_tracked_keyword UNIQUE (user_id, keyword)
);

CREATE INDEX IF NOT EXISTS idx_tracked_keywords_user ON tracked_keywords(user_id);


-- 20. keyword_position_snapshots - Position history
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


-- 21. serp_feature_presence - SERP features per keyword
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


-- 22. competitor_visibility_scores - Competitor rankings
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


-- 23. crawl_pages - Crawled page metadata
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


-- 24. onpage_signals - On-page SEO signals
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


-- 25. backlink_signals - Backlink data
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


-- 26. technical_signals - Technical SEO signals
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


-- 27. cwv_signals - Core Web Vitals
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


-- 28. ai_crawl_governance - AI crawler rules
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


-- 29. as_is_scores - Parameter scores
CREATE TABLE IF NOT EXISTS as_is_scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parameter_tab VARCHAR(20) NOT NULL,
    parameter_group VARCHAR(100) NOT NULL,
    sub_parameter VARCHAR(100) NULL,
    score FLOAT DEFAULT 0.0,
    max_score FLOAT DEFAULT 100.0,
    status VARCHAR(20) NOT NULL,
    details TEXT NULL,
    recommendation TEXT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_asis_score UNIQUE (user_id, parameter_tab, parameter_group, sub_parameter, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_asis_scores_user ON as_is_scores(user_id, snapshot_date);


-- 30. as_is_summary_cache - Summary card cache
CREATE TABLE IF NOT EXISTS as_is_summary_cache (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
