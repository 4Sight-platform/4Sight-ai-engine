-- Action Plan Tables Migration
-- Run this to create the action plan tables in your database

-- 1. action_plan_tasks - SEO action plan tasks
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


-- 2. action_plan_task_pages - Junction table for task-page relationships
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


-- 3. action_plan_task_history - Audit trail for task status changes
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

-- Verify tables were created
SELECT 'Action Plan tables created successfully!' AS status;
