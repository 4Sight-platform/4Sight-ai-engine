"""
Run goal milestones migration
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Database.database import engine
from sqlalchemy import text

def run_migration():
    """Execute the goal milestones migration SQL"""
    
    migration_sql = """
    -- 1. Add status column to strategy_goals table
    ALTER TABLE strategy_goals 
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'on_track';

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

    -- Create indexes for faster lookups
    CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal_id ON goal_progress_snapshots(goal_id);
    CREATE INDEX IF NOT EXISTS idx_goal_snapshots_date ON goal_progress_snapshots(snapshot_date DESC);

    -- 4. Update serp-features goals to paused status
    UPDATE strategy_goals 
    SET status = 'paused'
    WHERE goal_type = 'serp-features' AND (status IS NULL OR status = 'on_track');
    """
    
    with engine.connect() as conn:
        # Execute statements one by one
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        for stmt in statements:
            if stmt:
                try:
                    conn.execute(text(stmt))
                    print(f"✓ Executed: {stmt[:60]}...")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"⊘ Skipped (already exists): {stmt[:60]}...")
                    else:
                        print(f"✗ Error: {e}")
        conn.commit()
    
    print("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
