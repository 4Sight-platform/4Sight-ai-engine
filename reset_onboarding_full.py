
import sys
import os
from sqlalchemy import create_engine, text
from Database.database import DATABASE_URL

# Extend path to import from current directory
sys.path.append(os.getcwd())

try:
    from clear_all_data import clear_all_tables
except ImportError:
    print("Could not import clear_all_data. Please ensure it is in the current directory.")
    sys.exit(1)

def reset_users():
    """Reset onboarding flags for all users"""
    print("=" * 70)
    print("🔄 RESETTING USER ONBOARDING STATE")
    print("=" * 70)
    
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        try:
            # unique user ids are strings in this schema
            result = connection.execute(text("UPDATE users SET onboarding_completed = FALSE, current_onboarding_page = 1"))
            connection.commit()
            print(f"   ✓ Reset onboarding status for {result.rowcount} users")
        except Exception as e:
            print(f"   ❌ Error resetting users: {e}")
            
    print("\n✅ User state reset complete.")

if __name__ == "__main__":
    print("Starting full reset for re-onboarding test...")
    
    # 1. Clear all data tables
    clear_all_tables()
    
    # 2. Reset user flags
    reset_users()
    
    print("\n🚀 READY FOR ONBOARDING TEST")
