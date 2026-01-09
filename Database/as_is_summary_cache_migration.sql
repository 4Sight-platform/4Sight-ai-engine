-- ===========================================
-- AS-IS SUMMARY CACHE COMPLETE SCHEMA
-- Migration to add complete data storage
-- ===========================================

-- Add JSONB columns for storing complete As-Is summary data
-- This enables DB-first approach: read from DB if data exists, only sync if not found

-- Summary JSONB columns (stores complete card data)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS full_summary JSONB;

-- Keyword Rankings List (stores the ranked keywords with positions)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS ranked_keywords JSONB;

-- Top Performing Pages (stores the page list with clicks data)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS top_pages JSONB;

-- Competitor Rankings (stores competitor list with scores)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS competitor_rankings JSONB;

-- SERP Features Detail (stores which features are active/missing)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS serp_features_detail JSONB;

-- Baseline fields (for lock period - snapshot of data when locked)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_total_clicks INTEGER;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_total_impressions INTEGER;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_avg_position FLOAT;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_top10_keywords INTEGER;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_features_count INTEGER;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_your_rank INTEGER;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_visibility_score FLOAT;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_captured_at TIMESTAMP;

-- Domain Authority (for Goal Setting)
ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS domain_authority INTEGER DEFAULT 0;

ALTER TABLE as_is_summary_cache 
ADD COLUMN IF NOT EXISTS baseline_domain_authority INTEGER;

-- Add indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_as_is_summary_full_summary 
ON as_is_summary_cache USING GIN (full_summary);

-- Comment on table structure
COMMENT ON TABLE as_is_summary_cache IS 'Stores As-Is State summary data for the 4 top cards (Traffic, Keywords, SERP, Competitors). Uses JSONB for complete data storage to enable DB-first approach.';

COMMENT ON COLUMN as_is_summary_cache.full_summary IS 'Complete summary data as JSONB - primary source for reading cached data';
COMMENT ON COLUMN as_is_summary_cache.ranked_keywords IS 'List of keywords with positions and changes';
COMMENT ON COLUMN as_is_summary_cache.top_pages IS 'Top performing pages with traffic data';
COMMENT ON COLUMN as_is_summary_cache.competitor_rankings IS 'Competitor list with visibility scores';
COMMENT ON COLUMN as_is_summary_cache.serp_features_detail IS 'SERP features with active/missing status';
COMMENT ON COLUMN as_is_summary_cache.domain_authority IS 'Moz Domain Authority score';
COMMENT ON COLUMN as_is_summary_cache.baseline_domain_authority IS 'Baseline DA at lock time';
