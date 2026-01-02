"""
Direct database script to initialize goals for a specific user
"""
from Database.database import get_db
from goal_setting_service import GoalSettingService
import sys

user_id = sys.argv[1] if len(sys.argv) > 1 else "user_daeaff31acaf"

print(f"Initializing goals for user: {user_id}")
print("="*60)

db = next(get_db())
service = GoalSettingService(db)

try:
    result = service.initialize_goals(user_id)
    
    print(f"\nResult: {result}")
    
    if result.get("success"):
        print(f"\n✅ Successfully created {result.get('goals_created')} goals!")
        print(f"   Goal types: {', '.join(result.get('goal_types', []))}")
        print(f"   Cycle: {result.get('cycle_start')} to {result.get('cycle_end')}")
        
        # Verify goals were created
        from sqlalchemy import text
        count_result = db.execute(text(f"SELECT COUNT(*) FROM strategy_goals WHERE user_id = '{user_id}'"))
        count = count_result.scalar()
        print(f"\n   Verified {count} goals in database")
        
        # Show the goals
        goals_result = db.execute(text(f"SELECT goal_type, current_value, target_value FROM strategy_goals WHERE user_id = '{user_id}'"))
        goals = goals_result.fetchall()
        print(f"\n   Goals:")
        for goal in goals:
            print(f"     - {goal[0]}: Current={goal[1]}, Target={goal[2]}")
    else:
        print(f"\n❌ Failed: {result.get('message')}")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
