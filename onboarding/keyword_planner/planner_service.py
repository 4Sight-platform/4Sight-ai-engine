"""
Keyword Planner Service
Orchestrates the modular keyword planning pipeline.

ARCHITECTURE :
1. Generate seeds from profile (seed_generator.py)
2. Validate seeds with LLM (seed_validator.py)
3. Query GKP for each seed category (gkp_client.py)
4. Validate GKP results (gkp_result_validator.py)
5. Fetch GSC low-hanging fruit (gsc_client.py)
6. Validate onboarding keywords against GKP
7. Process, proportion, score, and rank (keyword_processor.py)
8. Save to database

PROPORTIONALITY:
- 40% from GSC (low-hanging fruit, rank 11-50)
- 60% from intent-based GKP keywords

LLM MODEL: Gemini 2.5 Flash for all validations.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import date, timedelta

from Database.database import SessionLocal
from Database.models import (
    KeywordUniverse, KeywordUniverseItem,
    OnboardingKeyword
)
from onboarding.fetch_profile_data import get_profile_manager
from onboarding.oauth_manager import OAuthManager

# Import V2 modules
from onboarding.keyword_planner.seed_generator import generate_seeds
from onboarding.keyword_planner.seed_validator import validate_seeds
from onboarding.keyword_planner.gkp_client import get_gkp_client, GKPClient
from onboarding.keyword_planner.gkp_result_validator import validate_gkp_results
from onboarding.keyword_planner.gsc_client import GSCKeywordClient
from onboarding.keyword_planner.keyword_processor import process_keywords

logger = logging.getLogger(__name__)

# Constants
TARGET_KEYWORD_COUNT = 20
VOLUME_THRESHOLD = 500
MAX_GKP_RETRIES = 2


class KeywordPlannerService:
    """
    Keyword Planner Service using modular architecture.
    """
    
    def __init__(self, db: Session = None):
        """
        Initialize the service.
        
        Args:
            db: SQLAlchemy session. If None, creates own session.
        """
        self.db = db if db else SessionLocal()
        self.pm = get_profile_manager()
        self.owns_session = db is None
        
        self.oauth_manager = OAuthManager(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            encryption_key=os.getenv("ENCRYPTION_KEY")
        )
    
    def cleanup(self):
        """Clean up resources."""
        if self.owns_session:
            self.db.close()
    
    async def initialize_universe(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize or refresh keyword universe for a user.
        
        This is the main orchestration method that:
        1. Generates and validates seeds
        2. Queries GKP per category
        3. Validates GKP results
        4. Gets GSC low-hanging fruit
        5. Processes and ranks keywords
        6. Saves to database
        
        Args:
            user_id: The user ID to initialize universe for.
        
        Returns:
            Universe data dictionary.
        """
        logger.info(f"Initializing Keyword Universe for user: {user_id}")
        
        # Check if already locked
        existing = self.db.query(KeywordUniverse).filter(
            KeywordUniverse.user_id == user_id
        ).first()
        
        if existing and existing.is_locked:
            logger.info(f"Universe already locked for user {user_id}")
            return self.get_universe(user_id)
        
        # Load user profile
        profile = self.pm.get_profile(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user: {user_id}")
        
        website_url = profile.get('website_url', '')
        user_intents = profile.get('search_intent', [])
        location_scope = profile.get('location_scope', '')
        
        # === PHASE 1: SEED GENERATION ===
        logger.info("[Phase 1] Generating seeds...")
        raw_seeds = generate_seeds(profile)
        
        # === PHASE 2: SEED VALIDATION ===
        logger.info("[Phase 2] Validating seeds...")
        validated_seeds = validate_seeds(
            raw_seeds, 
            profile,
            seed_generator_callback=lambda p, f: generate_seeds(p, f)
        )
        
        if not validated_seeds:
            logger.warning("No valid seeds generated - falling back to onboarding keywords only")
        
        # === PHASE 3: GKP QUERIES ===
        logger.info("[Phase 3] Querying Google Keyword Planner...")
        gkp_keywords = await self._query_gkp_with_validation(
            validated_seeds, profile, location_scope
        )
        
        # === PHASE 4: GSC LOW-HANGING FRUIT ===
        logger.info("[Phase 4] Fetching GSC low-hanging fruit...")
        gsc_keywords = await self._get_gsc_keywords(user_id, website_url)
        
        # === PHASE 4.5: ENRICH GSC KEYWORDS WITH VOLUME ===
        if gsc_keywords:
            logger.info("[Phase 4.5] Enriching GSC keywords with GKP volume data...")
            gsc_keywords = await self._enrich_gsc_with_volume(gsc_keywords, location_scope)
        
        # === PHASE 5: VALIDATE ONBOARDING KEYWORDS ===
        logger.info("[Phase 5] Validating onboarding keywords...")
        onboarding_keywords = await self._validate_onboarding_keywords(
            user_id, location_scope
        )
        
        # === PHASE 6: PROCESS AND RANK ===
        logger.info("[Phase 6] Processing and ranking keywords...")
        final_keywords = process_keywords(
            onboarding_keywords=onboarding_keywords,
            gkp_keywords=gkp_keywords,
            gsc_keywords=gsc_keywords,
            user_intents=user_intents,
            target_count=TARGET_KEYWORD_COUNT
        )
        
        # === PHASE 7: SAVE TO DATABASE ===
        logger.info("[Phase 7] Saving to database...")
        self._save_universe(user_id, final_keywords, gsc_keywords)
        
        return self.get_universe(user_id)
    
    async def _query_gkp_with_validation(
        self,
        validated_seeds: Dict[str, List[str]],
        profile: Dict[str, Any],
        location_scope: str
    ) -> List[Dict[str, Any]]:
        """
        Query GKP for each seed category with validation and retry logic.
        """
        all_keywords = []
        
        try:
            gkp_client = get_gkp_client()
        except Exception as e:
            logger.error(f"Failed to initialize GKP client: {e}")
            return []
        
        for category, seeds in validated_seeds.items():
            if not seeds:
                continue
            
            logger.info(f"  Querying GKP for category: {category} ({len(seeds)} seeds)")
            
            retry_count = 0
            current_seeds = seeds
            
            while retry_count < MAX_GKP_RETRIES:
                # Query GKP
                try:
                    results = gkp_client.generate_keyword_ideas(
                        seeds=current_seeds[:5],  # Limit seeds per call
                        location_scope=location_scope
                    )
                except Exception as e:
                    logger.error(f"GKP query failed for {category}: {e}")
                    break
                
                if not results:
                    logger.warning(f"No results for category {category}")
                    break
                
                # Validate results
                validation = validate_gkp_results(
                    keywords=results,
                    profile=profile,
                    original_seed=current_seeds[0] if current_seeds else "",
                    retry_count=retry_count
                )
                
                # Add valid keywords
                all_keywords.extend(validation.valid_keywords)
                
                if not validation.needs_retry:
                    logger.info(
                        f"  Category {category}: {len(validation.valid_keywords)} valid keywords"
                    )
                    break
                
                # Retry with refined seed
                logger.info(f"  Retrying {category} with refined seed...")
                from onboarding.keyword_planner.gkp_result_validator import GKPResultValidator
                validator = GKPResultValidator()
                refined_seed = validator.generate_refined_seed(
                    current_seeds[0], validation.feedback, profile
                )
                
                if refined_seed:
                    current_seeds = [refined_seed]
                else:
                    break
                
                retry_count += 1
        
        logger.info(f"Total GKP keywords collected: {len(all_keywords)}")
        return all_keywords
    
    async def _get_gsc_keywords(
        self,
        user_id: str,
        website_url: str
    ) -> List[Dict[str, Any]]:
        """
        Get low-hanging fruit keywords from GSC.
        """
        if not website_url:
            logger.warning("No website URL in profile - skipping GSC")
            return []
        
        try:
            gsc_client = GSCKeywordClient(self.oauth_manager)
            keywords = await gsc_client.get_low_hanging_fruit(
                user_id=user_id,
                website_url=website_url,
                days=30,
                limit=50
            )
            return keywords
        except Exception as e:
            logger.error(f"GSC fetch failed: {e}")
            return []
    
    async def _enrich_gsc_with_volume(
        self,
        gsc_keywords: List[Dict[str, Any]],
        location_scope: str
    ) -> List[Dict[str, Any]]:
        """
        Enrich GSC keywords with search volume data from GKP.
        
        GSC doesn't provide search volume, so we query GKP
        to get the actual search volumes for these keywords.
        """
        if not gsc_keywords:
            return []
        
        try:
            gkp_client = get_gkp_client()
            
            # Extract keyword texts
            keyword_texts = [kw.get('keyword', '') for kw in gsc_keywords if kw.get('keyword')]
            
            if not keyword_texts:
                return gsc_keywords
            
            logger.info(f"Getting GKP metrics for {len(keyword_texts)} GSC keywords...")
            
            # Wait a bit to avoid rate limits (GKP API has limits too)
            import time
            time.sleep(5)  # Wait 5 seconds to avoid rate limit
            
            # Get metrics from GKP with retry
            metrics = []
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    metrics = gkp_client.get_keyword_metrics(
                        keywords=keyword_texts,
                        location_scope=location_scope
                    )
                    break
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        wait_time = 5 * (attempt + 1)
                        logger.warning(f"GKP rate limit hit, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            # Create a lookup map
            volume_map = {m.get('keyword', '').lower(): m for m in metrics}
            
            # Enrich GSC keywords with volume
            enriched = []
            for kw in gsc_keywords:
                keyword_text = kw.get('keyword', '').lower()
                if keyword_text in volume_map:
                    gkp_data = volume_map[keyword_text]
                    kw['volume'] = gkp_data.get('volume', 0)
                    kw['competition'] = gkp_data.get('competition', 'UNKNOWN')
                    kw['competition_index'] = gkp_data.get('competition_index', 50)
                else:
                    # No GKP data found - keep original (volume = 0)
                    kw['volume'] = kw.get('volume', 0)
                
                enriched.append(kw)
            
            # Count how many got enriched
            enriched_count = sum(1 for kw in enriched if kw.get('volume', 0) > 0)
            logger.info(f"Enriched {enriched_count}/{len(gsc_keywords)} GSC keywords with volume data")
            
            return enriched
            
        except Exception as e:
            logger.error(f"Failed to enrich GSC keywords with volume: {e}")
            # Return original keywords unchanged
            return gsc_keywords
    
    async def _validate_onboarding_keywords(
        self,
        user_id: str,
        location_scope: str
    ) -> List[Dict[str, Any]]:
        """
        Validate onboarding keywords by getting their metrics from GKP.
        """
        # Load onboarding keywords from DB
        onboarding_kws = self.db.query(OnboardingKeyword).filter(
            OnboardingKeyword.user_id == user_id,
            OnboardingKeyword.is_selected == True
        ).all()
        
        if not onboarding_kws:
            logger.info("No onboarding keywords found")
            return []
        
        keyword_texts = [kw.keyword for kw in onboarding_kws]
        logger.info(f"Validating {len(keyword_texts)} onboarding keywords")
        
        try:
            gkp_client = get_gkp_client()
            metrics = gkp_client.get_keyword_metrics(
                keywords=keyword_texts,
                location_scope=location_scope
            )
            
            # Filter by volume threshold
            validated = [
                m for m in metrics 
                if m.get('volume', 0) >= VOLUME_THRESHOLD
            ]
            
            logger.info(
                f"Onboarding keywords: {len(validated)}/{len(keyword_texts)} passed volume check"
            )
            
            return validated
            
        except Exception as e:
            logger.error(f"Onboarding keyword validation failed: {e}")
            return []
    
    def _save_universe(
        self,
        user_id: str,
        keywords: List[Dict[str, Any]],
        gsc_keywords: List[Dict[str, Any]]
    ):
        """
        Save keyword universe to database.
        """
        try:
            # Create or update universe record
            universe = self.db.query(KeywordUniverse).filter(
                KeywordUniverse.user_id == user_id
            ).first()
            
            if not universe:
                universe = KeywordUniverse(user_id=user_id)
                self.db.add(universe)
            
            # Store GSC info
            gsc_kw_list = [k.get('keyword', '') for k in gsc_keywords[:10]]
            universe.gsc_excluded_keywords = []  # Not excluding, just tracking
            universe.gsc_message = f"Found {len(gsc_keywords)} low-hanging fruit keywords"
            universe.is_locked = False
            
            # Delete existing items
            self.db.query(KeywordUniverseItem).filter(
                KeywordUniverseItem.user_id == user_id
            ).delete()
            
            # Insert new items
            for kw in keywords:
                item = KeywordUniverseItem(
                    user_id=user_id,
                    keyword=kw.get('keyword', ''),
                    search_volume=kw.get('volume', 0),
                    difficulty=kw.get('difficulty', 'Medium'),
                    intent=kw.get('intent', 'Informational'),
                    keyword_type=kw.get('keyword_type', 'Informational'),  # DB: Transactional, Informational, Branded, Long-tail
                    source=kw.get('source', 'generated'),  # DB: verified, generated, custom
                    score=kw.get('score', 0),
                    is_selected=False
                )
                self.db.add(item)
            
            self.db.commit()
            logger.info(f"Saved {len(keywords)} keywords to universe for {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save universe: {e}")
            raise
    
    def get_universe(self, user_id: str) -> Dict[str, Any]:
        """
        Get keyword universe for a user.
        """
        universe = self.db.query(KeywordUniverse).filter(
            KeywordUniverse.user_id == user_id
        ).first()
        
        items = self.db.query(KeywordUniverseItem).filter(
            KeywordUniverseItem.user_id == user_id
        ).order_by(KeywordUniverseItem.score.desc()).all()
        
        if not universe:
            return {"status": "not_initialized"}
        
        return {
            "status": "success",
            "total_keywords": len(items),
            "gsc_message": universe.gsc_message or "",
            "is_locked": universe.is_locked,
            "locked_until": universe.locked_until,
            "keywords": [
                {
                    "id": i.id,
                    "keyword": i.keyword,
                    "volume": i.search_volume,
                    "difficulty": i.difficulty,
                    "intent": i.intent,
                    "type": i.keyword_type,
                    "score": float(i.score) if i.score else 0,
                    "source": i.source,
                    "is_selected": i.is_selected
                }
                for i in items
            ]
        }
    
    def finalize_selection(
        self,
        user_id: str,
        selected_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Finalize keyword selection and lock universe.
        
        Rules:
        - Must select 10-15 keywords
        - Locks for 90 days
        """
        if not (10 <= len(selected_ids) <= 15):
            raise ValueError("Must select between 10 and 15 keywords")
        
        universe = self.db.query(KeywordUniverse).filter(
            KeywordUniverse.user_id == user_id
        ).first()
        
        if not universe:
            raise ValueError("Keyword universe not found")
        
        if universe.is_locked:
            raise ValueError("Universe is already locked")
        
        # Reset all selections
        self.db.query(KeywordUniverseItem).filter(
            KeywordUniverseItem.user_id == user_id
        ).update({"is_selected": False})
        
        # Set selected items
        self.db.query(KeywordUniverseItem).filter(
            KeywordUniverseItem.user_id == user_id,
            KeywordUniverseItem.id.in_(selected_ids)
        ).update({"is_selected": True}, synchronize_session=False)
        
        # Lock universe
        universe.is_locked = True
        universe.locked_until = date.today() + timedelta(days=90)
        universe.selection_count = len(selected_ids)
        
        self.db.commit()
        
        logger.info(
            f"Locked universe for {user_id} with {len(selected_ids)} keywords "
            f"until {universe.locked_until}"
        )
        
        return {
            "status": "success",
            "locked_until": universe.locked_until.isoformat() if universe.locked_until else None,
            "selection_count": len(selected_ids)
        }
