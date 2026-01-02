"""
Alternative: Use SQLAlchemy Base.metadata.create_all()
This creates tables from the models directly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔗 Connecting to database...")

try:
    from Database.database import engine, Base
    from Database.models import ActionPlanTask, ActionPlanTaskPage, ActionPlanTaskHistory
    
    print("📊 Creating Action Plan tables...")
    
    # This will create ONLY the tables that don't exist yet
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    print("\n✅ SUCCESS! Action Plan tables created successfully!")
    print("\nTables created/verified:")
    print("  - action_plan_tasks")
    print("  - action_plan_task_pages")
    print("  - action_plan_task_history")
    print("\n🎉 You can now use the Action Plan feature!")
    print("\nRefresh your browser to see the action plan with real data!")

except Exception as e:
    print(f"\n❌ ERROR: Table creation failed!")
    print(f"Error details: {str(e)}")
    print("\nTroubleshooting:")
    print("  1. Make sure PostgreSQL is running")
    print("  2. Check DATABASE_URL in .env file")
    print("  3. Verify database 'foursight_platform' exists")
    print(f"\nFull error:\n{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
