"""
Clear and reinitialize goals for a user
"""
from Database.database import get_db
from sqlalchemy import text

user_id = "user_daeaff31acaf"

print("="*60)
print(f"Clearing and reinitializing goals for {user_id}")
print("="*60)

db = next(get_db())

try:
    # Step 1: Check existing goals
    result = db.execute(text(f"SELECT goal_type, is_locked FROM strategy_goals WHERE user_id = '{user_id}'"))
    existing = result.fetchall()
    
    if existing:
        print(f"\nFound {len(existing)} existing goals:")
        for goal in existing:
            print(f"  - {goal[0]} (locked: {goal[1]})")
        
        # Delete them
        print(f"\nDeleting existing goals...")
        db.execute(text(f"DELETE FROM strategy_goals WHERE user_id = '{user_id}'"))
        db.commit()
        print("✓ Deleted successfully")
    else:
        print("\nNo existing goals found")
    
    # Step 2: Check user's SEO goals
    result = db.execute(text(f"SELECT goals FROM seo_goals WHERE user_id = '{user_id}'"))
    row = result.fetchone()
    
    if not row:
        print(f"\n❌ No SEO goals found in seo_goals table for {user_id}")
        db.close()
        exit(1)
    
    seo_goals = row[0]
    print(f"\nUser's SEO goals from onboarding: {seo_goals}")
    
    # Step 3: Now call the service to initialize
    from goal_setting_service import GoalSettingService
    service = GoalSettingService(db)
    
    print(f"\nInitializing goals via service...")
    result = service.initialize_goals(user_id)
    
    if result.get("success"):
        print(f"\n✅ Successfully created {result.get('goals_created')} goals!")
        print(f"   Goal types: {', '.join(result.get('goal_types', []))}")
        print(f"   Cycle: {result.get('cycle_start')} to {result.get('cycle_end')}")
        
        # Verify
        verify_result = db.execute(text(f"SELECT goal_type, current_value, target_value FROM strategy_goals WHERE user_id = '{user_id}'"))
        goals = verify_result.fetchall()
        print(f"\nCreated goals:")
        for goal in goals:
            print(f"  - {goal[0]}: Current={goal[1]}, Target={goal[2]}")
    else:
        print(f"\n❌ Failed: {result.get('message')}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "="*60)
print("Done! Refresh your dashboard to see the goals.")
print("="*60)
