-- Goal Milestones and Snapshots Migration
-- Run this migration to add goal tracking tables

-- 1. Add status column to strategy_goals table
ALTER TABLE strategy_goals 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'on_track';

-- Add check constraint for status values
DO $$ BEGIN
    ALTER TABLE strategy_goals
    ADD CONSTRAINT chk_goal_status 
    CHECK (status IN ('on_track', 'paused', 'completed', 'at_risk'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Create goal_milestones table
CREATE TABLE IF NOT EXISTS goal_milestones (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES strategy_goals(id) ON DELETE CASCADE,
    month_number INTEGER NOT NULL CHECK (month_number IN (1, 2, 3)),
    target_value VARCHAR(100) NOT NULL,
    actual_value VARCHAR(100),
    achieved BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(goal_id, month_number)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_goal_milestones_goal_id ON goal_milestones(goal_id);

-- 3. Create goal_progress_snapshots table
CREATE TABLE IF NOT EXISTS goal_progress_snapshots (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES strategy_goals(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    current_value VARCHAR(100) NOT NULL,
    progress_percentage FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(goal_id, snapshot_date)
);

-- Create indexes for faster lookups and trend calculations
CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal_id ON goal_progress_snapshots(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_snapshots_date ON goal_progress_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal_date ON goal_progress_snapshots(goal_id, snapshot_date DESC);

-- 4. Update existing goals to have status 'on_track' (or 'paused' for serp-features)
UPDATE strategy_goals 
SET status = CASE 
    WHEN goal_type = 'serp-features' THEN 'paused'
    WHEN progress_percentage >= 100 THEN 'completed'
    WHEN progress_percentage >= 70 THEN 'on_track'
    WHEN progress_percentage >= 30 THEN 'on_track'
    ELSE 'at_risk'
END
WHERE status IS NULL OR status = 'on_track';

-- Special case: mark serp-features as paused
UPDATE strategy_goals 
SET status = 'paused'
WHERE goal_type = 'serp-features';

COMMENT ON TABLE goal_milestones IS 'Tracks monthly milestone targets and actuals for each 90-day goal cycle';
COMMENT ON TABLE goal_progress_snapshots IS 'Daily/weekly snapshots of goal values for trend calculation';
