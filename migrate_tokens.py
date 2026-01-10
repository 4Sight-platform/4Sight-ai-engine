
import json
import os
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from Database.database import get_db, engine
from Database.models import OAuthToken, Base

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

def migrate_tokens():
    """Migrate tokens from local JSON file to Database"""
    logger.info("Starting OAuth token migration...")
    
    # 1. Locate JSON file
    json_path = Path(__file__).parent / "onboarding" / "storage" / "credentials" / "oauth_tokens.json"
    
    if not json_path.exists():
        logger.info(f"No local token file found at {json_path}. Skipping migration.")
        return

    try:
        with open(json_path, 'r') as f:
            tokens = json.load(f)
            
        logger.info(f"Found {len(tokens)} tokens in local storage.")
        
        # 2. Connect to DB
        db = next(get_db())
        
        migrated_count = 0
        
        for user_id, data in tokens.items():
            encrypted_token = data.get("encrypted_refresh_token")
            created_at_str = data.get("created_at")
            
            if not encrypted_token:
                continue
                
            # Parse timestamp if valid
            created_at = datetime.utcnow()
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except:
                    pass
            
            # Check if exists
            exists = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
            if exists:
                logger.info(f"Token for {user_id} already in DB. Updating...")
                exists.encrypted_refresh_token = encrypted_token
                exists.last_refreshed_at = datetime.utcnow()
            else:
                logger.info(f"Migrating token for {user_id}...")
                new_token = OAuthToken(
                    user_id=user_id,
                    encrypted_refresh_token=encrypted_token,
                    provider='google',
                    token_created_at=created_at,
                    last_refreshed_at=datetime.utcnow()
                )
                db.add(new_token)
                migrated_count += 1
        
        db.commit()
        logger.info(f"Successfully migrated {migrated_count} new tokens to database.")
        
        # 3. Rename JSON file to backup
        backup_path = json_path.with_suffix('.json.bak')
        os.rename(json_path, backup_path)
        logger.info(f"Renamed local storage to {backup_path}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    migrate_tokens()
