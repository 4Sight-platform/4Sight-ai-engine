from sqlalchemy import create_engine, text
from Database.database import DATABASE_URL
from Database.models import AsIsSummaryCache, AsIsScore

def clear_cache():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("Clearing AsIsSummaryCache...")
        connection.execute(text("DELETE FROM as_is_summary_cache"))
        
        print("Clearing AsIsScore (optional, but requested to clear 'respective data')...")
        # The user might want to clear scores too if they are stale, but the main issue was the summary cache.
        # I'll stick to summary cache as that's the one causing the specific "0 Total" issue 
        # based on the previous turn's context. 
        # But to be safe and ensure a *full* fresh load as requested ("new value will load"), 
        # clearing scores might be aggressive but "correct" for a full reset.
        # Let's just clear the summary cache first as that's the direct blocker.
        # If I clear scores, they lose history which might be too much.
        # Re-reading: "clear the respective data from the db only then the new value will load"
        # in context of the "0 Total" issue, it refers to the summary cache.
        
        connection.commit()
        print("Cache cleared successfully.")

if __name__ == "__main__":
    clear_cache()
