#!/usr/bin/env python3
"""
Script to run the action plan migration
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("ERROR: DATABASE_URL not found in .env file")
    exit(1)

print(f"Connecting to database...")

# Create engine
engine = create_engine(database_url)

# Read migration SQL
migration_file = "Database/action_plan_migration.sql"
print(f"Reading migration file: {migration_file}")

with open(migration_file, 'r') as f:
    sql_content = f.read()

# Split by semicolons to execute statements separately
statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

print(f"Found {len(statements)} SQL statements to execute")

# Execute migration
try:
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                conn.execute(text(statement))
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("Action plan tables created:")
        print("  - action_plan_tasks")
        print("  - action_plan_task_pages")
        print("  - action_plan_task_history")
        
except Exception as e:
    print(f"\n❌ Migration failed with error:")
    print(f"   {str(e)}")
    exit(1)
