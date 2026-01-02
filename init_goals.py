"""
Simple script to create strategy_goals table and initialize user goals
"""
from Database.database import get_db, engine
from sqlalchemy import text
from goal_setting_service import GoalSettingService

# SQL to create table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS strategy_goals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Goal Identification
    goal_type VARCHAR(50) NOT NULL,
    goal_category VARCHAR(20) NOT NULL,
    
    -- Cycle Management
    cycle_start_date DATE NOT NULL,
    cycle_end_date DATE NOT NULL,
    is_locked BOOLEAN DEFAULT TRUE,
    
    -- Metrics
    baseline_value VARCHAR(100) NULL,
    current_value VARCHAR(100) NULL,
    target_value VARCHAR(100) NOT NULL,
    
    -- Metadata
    unit VARCHAR(50) NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    
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
    CONSTRAINT chk_target_type CHECK (target_type IN ('growth', 'range', 'slabs', 'paused'))
);

CREATE INDEX IF NOT EXISTS idx_strategy_goals_user ON strategy_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_goals_cycle ON strategy_goals(user_id, cycle_start_date);
CREATE INDEX IF NOT EXISTS idx_strategy_goals_active ON strategy_goals(user_id, is_locked) WHERE is_locked = TRUE;
"""

def main():
    print("="*60)
    print("Creating strategy_goals table and initializing user goals")
    print("="*60)
    
    # Create table
    print("\n1. Creating strategy_goals table...")
    try:
        with engine.connect() as conn:
            conn.execute(text(CREATE_TABLE_SQL))
            conn.commit()
        print("✓ Table created successfully")
    except Exception as e:
        print(f"Note: {str(e)}")
        print("  (Table may already exist, continuing...)")
    
    # Get user_id from database
    print("\n2. Finding users who completed onboarding...")
    db = next(get_db())
    try:
        result = db.execute(text("""
            SELECT u.id, u.email, u.full_name 
            FROM users u
            JOIN seo_goals sg ON u.id = sg.user_id
            WHERE u.onboarding_completed = TRUE
            LIMIT 10
        """))
        users = result.fetchall()
        
        if not users:
            print("❌ No users found who completed onboarding with SEO goals")
            print("\nPlease check:")
            print("- Users table has records with onboarding_completed = TRUE")
            print("- seo_goals table has corresponding records")
            return
        
        print(f"\nFound {len(users)} user(s) who completed onboarding:")
        for user in users:
            print(f"  - {user[0]} ({user[1]}) - {user[2] if user[2] else 'No name'}")
        
        # Initialize goals for each user
        print("\n3. Initializing goals...")
        service = GoalSettingService(db)
        
        for user in users:
            user_id = user[0]
            print(f"\n  Initializing goals for {user_id}...")
            
            try:
                result = service.initialize_goals(user_id)
                if result.get("success"):
                    print(f"  ✓ Created {result.get('goals_created')} goals")
                    print(f"    Goal types: {', '.join(result.get('goal_types', []))}")
                else:
                    print(f"  ⚠️  {result.get('message')}")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ Goal initialization complete!")
        print("="*60)
        print("\nRefresh your frontend to see the goals!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
