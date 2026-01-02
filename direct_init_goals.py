"""
Direct SQL approach to initialize goals bypassing ORM
"""
from Database.database import engine
from sqlalchemy import text
import json
from datetime import date, timedelta

user_id = "user_daeaff31acaf"

print(f"Direct SQL Goal Initialization for {user_id}")
print("="*60)

# Step 1: Check what SEO goals the user has
with engine.connect() as conn:
    result = conn.execute(text(f"SELECT goals FROM seo_goals WHERE user_id = '{user_id}'"))
    row = result.fetchone()
    
    if not row:
        print(f"❌ No SEO goals found for {user_id}")
        exit(1)
    
    seo_goals = row[0]
    print(f"\nUser's SEO Goals: {seo_goals}")
    
    # Goal mapping
    goal_mapping = {
        "organic_traffic": ("organic-traffic", "priority", "+500", "visitors/month", "growth", None),
        "search_visibility": ("serp-features", "priority", "Paused", "SERP features", "paused", None),
        "local_visibility": ("serp-features", "priority", "Paused", "SERP features", "paused", None),
        "top_rankings": ("keyword-rankings", "priority", "Slab Distribution", "keywords", "slabs", 
                        json.dumps([
                            {"label": "Top 50", "percentage": 50, "color": "bg-green-200"},
                            {"label": "Top 20", "percentage": 30, "color": "bg-green-400"},
                            {"label": "Top 10", "percentage": 20, "color": "bg-green-600"}
                        ]))
    }
    
    # Check if goals already exist
    result = conn.execute(text(f"SELECT COUNT(*) FROM strategy_goals WHERE user_id = '{user_id}' AND is_locked = TRUE"))
    existing_count = result.scalar()
    
    if existing_count > 0:
        print(f"\n⚠️  User already has {existing_count} active goals")
        print("Deleting existing goals...")
        conn.execute(text(f"DELETE FROM strategy_goals WHERE user_id = '{user_id}'"))
        conn.commit()
    
    # Set cycle dates
    cycle_start = date.today()
    cycle_end = cycle_start + timedelta(days=90)
    
    print(f"\nCycle: {cycle_start} to {cycle_end}")
    print(f"\nCreating goals...")
    
    created = 0
    for goal_name in seo_goals:
        if goal_name in goal_mapping:
            goal_type, category, target, unit, target_type, slab_data = goal_mapping[goal_name]
            
            # Get current value from AS-IS data (default to 0 for now)
            current_value = "0"
            
            # Insert goal
            insert_sql = text("""
                INSERT INTO strategy_goals 
                (user_id, goal_type, goal_category, cycle_start_date, cycle_end_date, 
                 is_locked, baseline_value, current_value, target_value, unit, target_type, 
                 slab_data, progress_percentage, last_calculated_at)
                VALUES 
                (:user_id, :goal_type, :goal_category, :cycle_start, :cycle_end,
                 TRUE, :baseline, :current, :target, :unit, :target_type,
                 :slab_data::jsonb, 0.0, CURRENT_TIMESTAMP)
            """)
            
            conn.execute(insert_sql, {
                "user_id": user_id,
                "goal_type": goal_type,
                "goal_category": category,
                "cycle_start": cycle_start,
                "cycle_end": cycle_end,
                "baseline": current_value,
                "current": current_value,
                "target": target,
                "unit": unit,
                "target_type": target_type,
                "slab_data": slab_data
            })
            
            created += 1
            print(f"  ✓ Created {goal_type}")
    
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created} goals!")
    print(f"{'='*60}")
    
    # Verify
    result = conn.execute(text(f"SELECT goal_type, target_value FROM strategy_goals WHERE user_id = '{user_id}'"))
    print(f"\nVerification:")
    for row in result.fetchall():
        print(f"  - {row[0]}: {row[1]}")
