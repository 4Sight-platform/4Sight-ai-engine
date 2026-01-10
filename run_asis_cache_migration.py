#!/usr/bin/env python3
"""
Script to run the As-Is Summary Cache migration
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

# Read migration SQL - Using the correct file that adds full_summary JSONB columns
migration_file = "Database/as_is_summary_cache_migration.sql"
print(f"Reading migration file: {migration_file}")

try:
    with open(migration_file, 'r') as f:
        sql_content = f.read()
except FileNotFoundError:
    print(f"Error: Could not find migration file at {migration_file}")
    # Try looking in absolute path if relative fails
    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), migration_file)
    print(f"Trying absolute path: {abs_path}")
    with open(abs_path, 'r') as f:
        sql_content = f.read()

# Split by semicolons to execute statements separately
statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

print(f"Found {len(statements)} SQL statements to execute")

# Execute migration
try:
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            if statement:
                # Skip comments that might be treated as statements
                if statement.startswith('--') and '\n' not in statement:
                    continue
                    
                print(f"Executing statement {i}/{len(statements)}...")
                try:
                    conn.execute(text(statement))
                except Exception as stmt_err:
                    print(f"Warning executing statement {i}: {str(stmt_err)}")
                    # Continue if it's "relation already exists" or similar
                    if "already exists" in str(stmt_err).lower() or "duplicate column" in str(stmt_err).lower():
                         print("  (Object already exists, continuing...)")
                    else:
                        raise stmt_err
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("Changes applied to as_is_summary_cache table:")
        print("  - Added JSONB columns (full_summary, ranked_keywords, etc.)")
        print("  - Added Baseline columns")
        
except Exception as e:
    print(f"\n❌ Migration failed with error:")
    print(f"   {str(e)}")
    exit(1)
