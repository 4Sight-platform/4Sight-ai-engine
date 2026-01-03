-- Governance As-Is Performance Migration
-- Adds baseline tracking to existing As-Is tables for performance delta calculations

-- 1. Add baseline tracking columns to as_is_scores table
ALTER TABLE as_is_scores 
ADD COLUMN IF NOT EXISTS baseline_score FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_baseline BOOLEAN DEFAULT FALSE;

-- Create index for efficient baseline queries
CREATE INDEX IF NOT EXISTS idx_asis_baseline 
ON as_is_scores(user_id, is_baseline, snapshot_date);

-- 2. Add baseline tracking columns to as_is_summary_cache table
ALTER TABLE as_is_summary_cache
ADD COLUMN IF NOT EXISTS baseline_total_clicks INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_total_impressions INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_avg_position FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_top10_keywords INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_features_count INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_your_rank INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_visibility_score FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS baseline_captured_at TIMESTAMP DEFAULT NULL;

-- 3. Create progress timeline table for tracking changes
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

-- Verify tables were modified successfully
SELECT 'Governance As-Is Performance tables updated successfully!' AS status;
