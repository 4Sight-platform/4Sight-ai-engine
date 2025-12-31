-- 4Sight Platform - Complete PostgreSQL Schema
-- Version 2.0 - Email-based UUID + Separated Products/Services

-- ============================================
-- DATABASE SETUP
-- ============================================

CREATE DATABASE foursight_platform;
\c foursight_platform;

-- ============================================
-- CORE TABLES
-- ============================================

-- 1. users - User Accounts (Email-based UUID)
CREATE TABLE users (
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

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_google_id ON users(google_user_id);
CREATE INDEX idx_users_created_at ON users(created_at);


-- 2. oauth_tokens - OAuth Token Storage
CREATE TABLE oauth_tokens (
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

CREATE INDEX idx_oauth_tokens_user_id ON oauth_tokens(user_id);


-- 3. email_verification_tokens
CREATE TABLE email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_token_expiry CHECK (expires_at > created_at)
);

CREATE INDEX idx_email_verification_token ON email_verification_tokens(token);
CREATE INDEX idx_email_verification_user_id ON email_verification_tokens(user_id);


-- 4. password_reset_tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_token_expiry CHECK (expires_at > created_at)
);

CREATE INDEX idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_user_id ON password_reset_tokens(user_id);


-- ============================================
-- ONBOARDING TABLES
-- ============================================

-- 5. business_profiles - Page 1
CREATE TABLE business_profiles (
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

CREATE INDEX idx_business_profiles_user_id ON business_profiles(user_id);


-- 6. integrations - Page 2
CREATE TABLE integrations (
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

CREATE INDEX idx_integrations_user_id ON integrations(user_id);


-- 7. audience_profiles - Page 3
CREATE TABLE audience_profiles (
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

CREATE INDEX idx_audience_profiles_user_id ON audience_profiles(user_id);


-- 8. products - Page 4 (Individual Products)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Product Info
    product_name VARCHAR(255) NOT NULL,
    product_url VARCHAR(500) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_user_id ON products(user_id);


-- 9. services - Page 4 (Individual Services)
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Service Info
    service_name VARCHAR(255) NOT NULL,
    service_url VARCHAR(500) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_services_user_id ON services(user_id);


-- 10. differentiators - Page 4 (Business Differentiators)
CREATE TABLE differentiators (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Differentiator
    differentiator TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_differentiators_user_id ON differentiators(user_id);


-- 11. seo_goals - Page 5
CREATE TABLE seo_goals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    goals TEXT[] NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_seo_goals_user_id ON seo_goals(user_id);


-- 12. onboarding_keywords - Page 6
CREATE TABLE onboarding_keywords (
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

CREATE INDEX idx_onboarding_keywords_user_id ON onboarding_keywords(user_id);
CREATE INDEX idx_onboarding_keywords_selected ON onboarding_keywords(user_id, is_selected);


-- 13. onboarding_competitors - Page 6
CREATE TABLE onboarding_competitors (
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

CREATE INDEX idx_onboarding_competitors_user_id ON onboarding_competitors(user_id);
CREATE INDEX idx_onboarding_competitors_selected ON onboarding_competitors(user_id, is_selected);


-- 14. page_urls - Page 7
CREATE TABLE page_urls (
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

CREATE INDEX idx_page_urls_user_id ON page_urls(user_id);


-- 15. reporting_preferences - Page 8
CREATE TABLE reporting_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Reporting Config (Email removed as it's in users table)
    reporting_channels TEXT[] NOT NULL,
    report_frequency VARCHAR(50) NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reporting_preferences_user_id ON reporting_preferences(user_id);


-- ============================================
-- STRATEGY DASHBOARD TABLES
-- ============================================

-- 16. keyword_universes - Keyword Planner Lock Status
CREATE TABLE keyword_universes (
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

CREATE INDEX idx_keyword_universes_user_id ON keyword_universes(user_id);


-- 17. keyword_universe_items - Keyword Planner Keywords
CREATE TABLE keyword_universe_items (
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

CREATE INDEX idx_keyword_universe_items_user_id ON keyword_universe_items(user_id);
CREATE INDEX idx_keyword_universe_items_selected ON keyword_universe_items(user_id, is_selected);


-- ============================================
-- SUMMARY
-- ============================================

/*
TOTAL TABLES: 17

CORE AUTH & USERS (4 tables)
1. users (email-based UUID)
2. oauth_tokens
3. email_verification_tokens
4. password_reset_tokens

ONBOARDING DATA (11 tables)
5. business_profiles (Page 1)
6. integrations (Page 2)
7. audience_profiles (Page 3)
8. products (Page 4)
9. services (Page 4)
10. differentiators (Page 4)
11. seo_goals (Page 5)
12. onboarding_keywords (Page 6)
13. onboarding_competitors (Page 6)
14. page_urls (Page 7)
15. reporting_preferences (Page 8)

STRATEGY DASHBOARD (2 tables)
16. keyword_universes
17. keyword_universe_items

KEY DESIGN DECISIONS:
- user_id = VARCHAR(50) from email hash (e.g., user_abc123def456)
- username field ready for frontend
- full_name field ready for frontend
- Products & Services as separate rows (not arrays)
- Password NULL until onboarding complete
- credentials_sent flag for email tracking
*/
