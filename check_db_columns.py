import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    # Fallback if env not loaded correctly in this context
    db_url = "postgresql://postgres:admin123@localhost:5432/4Sight_platform"

try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    table_name = "as_is_summary_cache"
    if inspector.has_table(table_name):
        print(f"Table '{table_name}' exists.")
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        print(f"Columns in {table_name}:")
        for col in columns:
            print(f" - {col}")
            
        if "full_summary" in columns:
            print("\n✅ Verification SUCCESS: 'full_summary' column EXISTS.")
        else:
            print("\n❌ Verification FAILED: 'full_summary' column does NOT exist.")
    else:
        print(f"❌ Table '{table_name}' does NOT exist.")

except Exception as e:
    print(f"Error connecting to database: {e}")
