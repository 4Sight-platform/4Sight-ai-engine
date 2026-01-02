"""
Database Migration Script for Strategy Goals Table
Creates the strategy_goals table for Goal Setting feature
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from Database.database import Base
from Database.models import StrategyGoal

# Database URL
DATABASE_URL = settings.database_url

def run_migration():
    """Run the migration to create strategy_goals table"""
    print("=" * 60)
    print("Strategy Goals Table Migration")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Check if table already exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'strategy_goals')"
            ))
            table_exists = result.scalar()
            
            if table_exists:
                print("⚠️  Table 'strategy_goals' already exists!")
                response = input("Do you want to drop and recreate it? (yes/no): ")
                if response.lower() != 'yes':
                    print("Migration cancelled.")
                    return
                
                print("Dropping existing table...")
                conn.execute(text("DROP TABLE IF EXISTS strategy_goals CASCADE"))
                conn.commit()
                print("✓ Table dropped successfully")
        
        # Create the table
        print("\nCreating strategy_goals table...")
        StrategyGoal.__table__.create(engine, checkfirst=True)
        print("✓ Table created successfully")
        
        # Verify table creation
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'strategy_goals' ORDER BY ordinal_position"
            ))
            columns = result.fetchall()
            
            print("\n" + "=" * 60)
            print("Table Structure:")
            print("=" * 60)
            for col_name, col_type in columns:
                print(f"  {col_name:<30} {col_type}")
            
            # Show indexes
            result = conn.execute(text(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'strategy_goals'"
            ))
            indexes = result.fetchall()
            
            print("\n" + "=" * 60)
            print("Indexes:")
            print("=" * 60)
            for idx_name, idx_def in indexes:
                print(f"  {idx_name}")
            
            # Show constraints
            result = conn.execute(text(
                """SELECT conname, pg_get_constraintdef(oid) 
                   FROM pg_constraint 
                   WHERE conrelid = 'strategy_goals'::regclass"""
            ))
            constraints = result.fetchall()
            
            print("\n" + "=" * 60)
            print("Constraints:")
            print("=" * 60)
            for const_name, const_def in constraints:
                print(f"  {const_name}: {const_def}")
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
