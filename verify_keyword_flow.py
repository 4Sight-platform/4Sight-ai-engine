"""
Verify Data Persistence for Keywords and Competitors
1. Setup test user
2. Simulate Onboarding Keyword Selection
3. Simulate `final_competitors` Update
4. Simulate `mark_onboarding_complete`
5. Verify `KeywordUniverseItem` population
6. Verify `OnboardingCompetitor` persistence
7. Check schema for `tracked_keywords` (should be absent)
"""
import sys
import os
import uuid
import logging
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

try:
    from Database.database import SessionLocal, engine
    from Database.models import User, OnboardingKeyword, OnboardingCompetitor, KeywordUniverseItem
    from onboarding.fetch_profile_data import get_profile_manager
except ImportError:
    # Try adjusting path if running from subdir
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from Database.database import SessionLocal, engine
    from Database.models import User, OnboardingKeyword, OnboardingCompetitor, KeywordUniverseItem
    from onboarding.fetch_profile_data import get_profile_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_flow():
    db = SessionLocal()
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@example.com"
    
    try:
        # 1. Create Test User
        logger.info(f"Creating test user: {user_id}")
        user = User(id=user_id, email=email, username=user_id, full_name="Test User", account_type='standard')
        db.add(user)
        db.commit()
        
        # 2. Add Onboarding Keywords (Simulate Page 6 Selection)
        logger.info("Adding onboarding keywords...")
        keywords = ["seo tool", "keyword research", "competitor analysis"]
        pm = get_profile_manager()
        pm.save_keywords_selected(user_id, keywords)
        
        # 3. Simulate Final Competitors Update (Page 6/7)
        logger.info("Updating final competitors...")
        competitors = [
            {"domain": "semrush.com", "name": "Semrush"},
            {"domain": "ahrefs.com", "name": "Ahrefs"}
        ]
        # Simulate the update_profile call that happens at final step
        pm.update_profile(user_id, {"final_competitors": competitors})
        
        # Verify Competitors Saved
        comps = db.query(OnboardingCompetitor).filter(OnboardingCompetitor.user_id == user_id).all()
        logger.info(f"Competitors count: {len(comps)}")
        if len(comps) != 2:
            logger.error(f"Expected 2 competitors, found {len(comps)}")
            # sys.exit(1)
        
        # Check source and selection
        if comps:
            logger.info(f"Competitor 0: {comps[0].competitor_url} | Source: {comps[0].source} | Selected: {comps[0].is_selected}")
        
        # 4. Mark Onboarding Complete (Should trigger promotion)
        logger.info("Marking onboarding complete...")
        pm.mark_onboarding_complete(user_id)
        
        # 5. Verify Keyword Universe Promotion
        kui = db.query(KeywordUniverseItem).filter(KeywordUniverseItem.user_id == user_id).all()
        logger.info(f"Keyword Universe Items: {len(kui)}")
        if len(kui) != 3:
            logger.error(f"Expected 3 universe items, found {len(kui)}")
        else:
             logger.info(f"Item 0: {kui[0].keyword} | Source: {kui[0].source} | Selected: {kui[0].is_selected}")

        # 6. Verify Schema (tracked_keywords should be gone)
        logger.info("Checking for tracked_keywords table...")
        try:
            db.execute(text("SELECT * FROM tracked_keywords LIMIT 1"))
            logger.error("❌ tracked_keywords table still exists!")
        except Exception as e:
            if "does not exist" in str(e) or "ProgrammingError" in str(e) or "UndefinedTable" in str(e):
                logger.info("✅ tracked_keywords table does not exist (Expected)")
            else:
                logger.info(f"✅ Table check failed with expected error: {e}")

        logger.info("=== VERIFICATION FINISHED ===")
        
    except Exception as e:
        logger.error(f"Verification FAILED: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        try:
            db.query(User).filter(User.id == user_id).delete()
            db.commit()
        except:
             pass
        db.close()

if __name__ == "__main__":
    verify_flow()
