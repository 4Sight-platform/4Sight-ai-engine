
import sys
import os
import logging
from sqlalchemy import text

# Add parent directory to path to import Database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Database.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_asis_data():
    db = SessionLocal()
    try:
        logger.info("Clearing AS-IS State data...")
        
        # Clear AsIsSummaryCache
        db.execute(text("DELETE FROM as_is_summary_cache;"))
        logger.info("Cleared as_is_summary_cache")
        
        # Clear AsIsScores
        db.execute(text("DELETE FROM as_is_scores;"))
        logger.info("Cleared as_is_scores")
        
        db.commit()
        logger.info("✅ Successfully erased all AS-IS data.")
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_asis_data()
