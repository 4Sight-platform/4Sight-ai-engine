from Database.database import get_db
from sqlalchemy import text

db = next(get_db())
result = db.execute(text("SELECT goal_type, current_value, target_value, goal_category FROM strategy_goals WHERE user_id = 'user_daeaff31acaf' ORDER BY goal_category, goal_type"))

print("Goals for user_daeaff31acaf:")
print("="*60)
for row in result.fetchall():
    print(f"{row[3].upper()}: {row[0]}")
    print(f"  Current: {row[1]}")
    print(f"  Target: {row[2]}")
    print()
db.close()
