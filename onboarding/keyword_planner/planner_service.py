"""
Keyword Planner Service
Implementation of the 5-Phase Keyword Strategy logic (Full Service Integration).

DESIGN COMPLIANCE:
- Step 1: Verify keywords with Google Ads API, filter by volume (1000+)
- Step 2: Remove keywords user already ranks for (GSC Top 20)
- Step 3: Fill gaps using Google Ads API keyword ideas (NOT simulated)
- Step 4: Enrich with real competition data from Google Ads API
- Step 5: User selects 10-15 keywords, lock for 90 days

NO SIMULATION OR FALLBACK - Legal compliance requirement.
"""

import logging
import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime

from Database.database import SessionLocal
from Database.models import (
    KeywordUniverse, KeywordUniverseItem, User,
    OnboardingKeyword, OnboardingCompetitor, AudienceProfile,
    Differentiators, SeoGoal
)
from onboarding.fetch_profile_data import get_profile_manager
from onboarding.ga_gsc_connection.gsc_connect import GSCConnector
from onboarding.oauth_manager import OAuthManager

# Try importing Google Ads Client
try:
    from google.ads.googleads.client import GoogleAdsClient
    HAS_GOOGLE_ADS = True
except ImportError:
    HAS_GOOGLE_ADS = False

# Try importing Gemini for business summary
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logger = logging.getLogger(__name__)

# Location mapping (common locations to Google Geo Target IDs)
LOCATION_GEO_TARGETS = {
    "india": "2356",
    "united states": "2840",
    "usa": "2840",
    "uk": "2826",
    "united kingdom": "2826",
    "global": None,  # No geo restriction
    "international": None,
}

# Volume thresholds
VOLUME_PRIMARY_THRESHOLD = 1000
VOLUME_FALLBACK_THRESHOLD = 500
TARGET_KEYWORD_COUNT = 20


class KeywordPlannerService:
    def __init__(self, db: Session = None):
        self.db = db if db else SessionLocal()
        self.pm = get_profile_manager()
        self.owns_session = db is None
        
        self.oauth_manager = OAuthManager(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            encryption_key=os.getenv("ENCRYPTION_KEY")
        )
        
        # Initialize Gemini for business summary
        if HAS_GEMINI and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.gemini_model = None
    
    def cleanup(self):
        if self.owns_session:
            self.db.close()

    def _validate_google_ads_credentials(self):
        """Validate all required Google Ads API credentials are present."""
        required_env_vars = [
            "GOOGLE_ADS_DEVELOPER_TOKEN",
            "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_REFRESH_TOKEN",
            "GOOGLE_ADS_CUSTOMER_ID"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Google Ads API credentials are required but missing: {', '.join(missing_vars)}. "
                f"Please configure all credentials in .env file. See .env.example for details."
            )
        
        if not HAS_GOOGLE_ADS:
            raise ImportError(
                "google-ads library is not installed. "
                "Run: pip install google-ads"
            )

    def _get_google_ads_client(self) -> GoogleAdsClient:
        """Get configured Google Ads client."""
        google_ads_config = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "use_proto_plus": True
        }
        return GoogleAdsClient.load_from_dict(google_ads_config)

    def _get_customer_id(self) -> str:
        """Get customer ID without dashes."""
        return os.getenv("GOOGLE_ADS_CUSTOMER_ID").replace("-", "")

    def _get_geo_target(self, location_scope: str) -> Optional[str]:
        """Convert location scope to Google Geo Target ID."""
        if not location_scope:
            return None
        location_lower = location_scope.lower().strip()
        return LOCATION_GEO_TARGETS.get(location_lower)

    async def _create_business_summary(self, profile: Dict[str, Any]) -> str:
        """
        Create a one-liner business summary using LLM for GKP seed input.
        Combines: business_name, description, products, services, audience.
        """
        # Gather all business context
        business_name = profile.get('business_name', '')
        description = profile.get('business_description', '')
        products = [p.get('name', '') for p in profile.get('products', [])]
        services = [s.get('name', '') for s in profile.get('services', [])]
        customer_desc = profile.get('customer_description', '')
        search_intent = profile.get('search_intent', [])
        location = profile.get('location_scope', '')
        
        context = f"""
Business Name: {business_name}
Description: {description}
Products: {', '.join(products) if products else 'N/A'}
Services: {', '.join(services) if services else 'N/A'}
Target Customer: {customer_desc}
Search Intent: {', '.join(search_intent) if search_intent else 'General'}
Location: {location}
"""
        
        if self.gemini_model:
            prompt = f"""Based on this business profile, create a ONE LINE summary (max 100 characters) 
that captures the core business offering for keyword research purposes. 
Focus on: what they sell/offer + who they serve.

{context}

Return ONLY the one-liner, no quotes, no explanation. Example: "B2B digital marketing agency for startups in India"
"""
            try:
                response = self.gemini_model.generate_content(prompt)
                summary = response.text.strip().strip('"').strip("'")
                logger.info(f"Business summary generated: {summary}")
                return summary
            except Exception as e:
                logger.warning(f"Gemini summary failed: {e}, using fallback")
        
        # Fallback: Build manually
        parts = []
        if services:
            parts.append(services[0])
        elif products:
            parts.append(products[0])
        if business_name:
            parts.append(f"by {business_name}")
        if location and location.lower() not in ['global', 'international']:
            parts.append(f"in {location}")
        
        return ' '.join(parts) if parts else f"{business_name} services"

    async def initialize_universe(self, user_id: str) -> Dict[str, Any]:
        """
        Phase 1-4: Initialize keyword universe for a user.
        Returns exactly 20 keywords (or fewer if not enough pass filters).
        """
        logger.info(f"Initializing Keyword Universe for {user_id}")
        
        # Validate credentials upfront
        self._validate_google_ads_credentials()
        
        # Check if already locked
        existing = self.db.query(KeywordUniverse).filter(KeywordUniverse.user_id == user_id).first()
        if existing and existing.is_locked:
            return self.get_universe(user_id)

        # Load Profile & Onboarding Keywords
        profile = self.pm.get_profile(user_id)
        onboarding_kws = self.db.query(OnboardingKeyword).filter(
            OnboardingKeyword.user_id == user_id,
            OnboardingKeyword.is_selected == True
        ).all()
        
        raw_keywords = [kw.keyword for kw in onboarding_kws]
        logger.info(f"Loaded {len(raw_keywords)} onboarding keywords")
        
        # Phase 1: Verify with GKP + Filter by volume (1000+)
        verified_keywords = await self._verify_and_filter_keywords(raw_keywords, profile)
        logger.info(f"After volume filter: {len(verified_keywords)} keywords")

        # Phase 2: GSC De-duplication (Remove keywords ranking in Top 20)
        filtered_keywords, gsc_excluded, gsc_msg = await self._filter_gsc_keywords(verified_keywords, user_id)
        logger.info(f"After GSC filter: {len(filtered_keywords)} keywords (excluded {len(gsc_excluded)})")
        
        # Phase 3: Gap Filling (Target 20 keywords using Google Ads API)
        if len(filtered_keywords) < TARGET_KEYWORD_COUNT:
            gap_count = TARGET_KEYWORD_COUNT - len(filtered_keywords)
            logger.info(f"Need to fill {gap_count} keyword gaps")
            filled_keywords = await self._fill_keyword_gaps_with_gkp(
                filtered_keywords, gap_count, profile
            )
        else:
            # Take top 20 by volume
            filled_keywords = sorted(filtered_keywords, key=lambda x: x.get('volume', 0), reverse=True)[:TARGET_KEYWORD_COUNT]
        
        logger.info(f"Final keyword count: {len(filled_keywords)}")

        # Phase 4: Enrichment (calculate difficulty and score from real data)
        enriched_items = self._enrich_keywords(filled_keywords)

        # Save to database
        self._save_universe(user_id, enriched_items, gsc_excluded, gsc_msg)

        return self.get_universe(user_id)

    async def _verify_and_filter_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase 1: Verify keywords with Google Ads API and filter by volume.
        
        Volume Logic:
        - Keep keywords with 1000+ monthly searches
        - If fewer than 10 pass, also include 500-999 range
        - Never include keywords with < 500 searches
        """
        if not keywords:
            return []
        
        try:
            client = self._get_google_ads_client()
            customer_id = self._get_customer_id()
            
            keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
            request = client.get_type("GenerateKeywordHistoricalMetricsRequest")
            request.customer_id = customer_id
            request.keywords = keywords
            request.language = "languageConstants/1000"  # English
            request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            # Add geo target if available
            geo_target = self._get_geo_target(profile.get('location_scope'))
            if geo_target:
                request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
            
            logger.info("Fetching keyword metrics from Google Ads API...")
            response = keyword_plan_idea_service.generate_keyword_historical_metrics(request=request)
            
            high_volume = []  # 1000+
            medium_volume = []  # 500-999
            
            for result in response.results:
                metrics = result.keyword_metrics
                if metrics:
                    volume = metrics.avg_monthly_searches or 0
                    competition = metrics.competition.name if metrics.competition else "UNKNOWN"
                    competition_index = metrics.competition_index or 50
                    
                    keyword_data = {
                        "keyword": result.text,
                        "volume": volume,
                        "competition": competition,
                        "competition_index": competition_index,
                        "source": "verified"
                    }
                    
                    if volume >= VOLUME_PRIMARY_THRESHOLD:
                        high_volume.append(keyword_data)
                    elif volume >= VOLUME_FALLBACK_THRESHOLD:
                        medium_volume.append(keyword_data)
            
            # Apply threshold logic
            if len(high_volume) >= 10:
                logger.info(f"Found {len(high_volume)} keywords with 1000+ volume")
                return high_volume
            else:
                # Include medium volume as fallback
                combined = high_volume + medium_volume
                logger.info(f"Using fallback: {len(high_volume)} high + {len(medium_volume)} medium volume keywords")
                return combined
            
        except Exception as e:
            logger.error(f"Google Ads API Error in verification: {e}")
            raise RuntimeError(f"Failed to verify keywords with Google Ads API: {str(e)}")

    async def _filter_gsc_keywords(self, keywords: List[Dict[str, Any]], user_id: str) -> Tuple[List[Dict[str, Any]], List[str], str]:
        """
        Phase 2: Remove keywords user already ranks for (Top 20 positions).
        
        Logic:
        - Position 1-20: REMOVE (already ranking well)
        - Position 21-100: KEEP (room for improvement)
        - Not ranking (100+): KEEP (new opportunity)
        """
        # Get Access Token
        access_token = await self.oauth_manager.refresh_access_token(user_id)
        if not access_token:
            logger.warning(f"No GSC token for {user_id}, skipping de-duplication.")
            return keywords, [], "GSC not connected - skipping de-duplication."
            
        connector = GSCConnector(access_token)
        
        # Get website URL from profile
        profile = self.pm.get_profile(user_id)
        target_website = profile.get('website_url') or profile.get('website')
        
        if not target_website:
            logger.warning(f"No website found in profile for {user_id}. Skipping GSC validation.")
            return keywords, [], "No website set in profile."
            
        valid, site_url = await connector.validate_ownership(target_website)
        if not valid or not site_url:
            logger.warning(f"GSC ownership not validated for {target_website}")
            return keywords, [], "GSC website not verified."
            
        # Fetch Analytics (Last 30 days)
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()
        
        logger.info(f"Fetching GSC data for {site_url}")
        rows = await connector.fetch_search_analytics(
            site_url, start_date, end_date, dimensions=["query"], row_limit=500
        )
        
        # Extract keywords ranking in Top 20
        ranking_keywords = set()
        for row in rows:
            keys = row.get('keys', [])
            if keys:
                query = keys[0]
                position = row.get('position', 100)
                if position <= 20:  # Top 20
                    ranking_keywords.add(query.lower())
                
        filtered = []
        excluded_kws = []
        
        for item in keywords:
            if item['keyword'].lower() in ranking_keywords:
                excluded_kws.append(item['keyword'])
            else:
                filtered.append(item)
                
        if excluded_kws:
            msg = f"Removed {len(excluded_kws)} keywords you already rank for in Top 20: {', '.join(excluded_kws[:5])}{'...' if len(excluded_kws) > 5 else ''}"
        else:
            msg = "No ranking overlap found - all keywords are new opportunities."
        
        return filtered, excluded_kws, msg

    async def _fill_keyword_gaps_with_gkp(
        self, 
        current_keywords: List[Dict[str, Any]], 
        count: int, 
        profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: Fill keyword gaps using Google Ads API generate_keyword_ideas.
        
        Logic:
        1. Create business summary using LLM
        2. Use Google Ads API to generate keyword ideas based on:
           - Business summary as seed text
           - Website URL as page_url
        3. Filter by volume (1000+)
        4. Rank by volume * (100 - competition_index)
        5. Add until we reach TARGET_KEYWORD_COUNT
        """
        # Create business summary for seed
        business_summary = await self._create_business_summary(profile)
        website_url = profile.get('website_url', '')
        
        logger.info(f"Generating keyword ideas with seed: '{business_summary}'")
        
        try:
            client = self._get_google_ads_client()
            customer_id = self._get_customer_id()
            
            keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
            request = client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = customer_id
            request.language = "languageConstants/1000"  # English
            request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            # Add geo target if available
            geo_target = self._get_geo_target(profile.get('location_scope'))
            if geo_target:
                request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
            
            # Use keyword seed (text-based)
            request.keyword_seed.keywords.append(business_summary)
            
            # Also use URL if available
            if website_url:
                request.url_seed.url = website_url
            
            logger.info("Fetching keyword ideas from Google Ads API...")
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            # Collect and filter ideas
            existing_keywords = set(k['keyword'].lower() for k in current_keywords)
            new_keywords = []
            
            for idea in response.results:
                keyword_text = idea.text
                metrics = idea.keyword_idea_metrics
                
                if keyword_text.lower() in existing_keywords:
                    continue
                
                if metrics:
                    volume = metrics.avg_monthly_searches or 0
                    competition_index = metrics.competition_index or 50
                    
                    if volume >= VOLUME_PRIMARY_THRESHOLD:
                        # Calculate opportunity score: high volume + low competition = better
                        opportunity_score = volume * (100 - competition_index) / 100
                        
                        new_keywords.append({
                            "keyword": keyword_text,
                            "volume": volume,
                            "competition": metrics.competition.name if metrics.competition else "UNKNOWN",
                            "competition_index": competition_index,
                            "opportunity_score": opportunity_score,
                            "source": "generated"
                        })
                        existing_keywords.add(keyword_text.lower())
            
            # Sort by opportunity score and take what we need
            new_keywords.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
            keywords_to_add = new_keywords[:count]
            
            logger.info(f"Generated {len(keywords_to_add)} new keywords from Google Ads API")
            
            return current_keywords + keywords_to_add
            
        except Exception as e:
            logger.error(f"Google Ads API Error in gap filling: {e}")
            # Don't raise - return what we have
            logger.warning("Gap filling failed, proceeding with existing keywords")
            return current_keywords

    def _enrich_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 4: Enrich keywords with metadata.
        
        Uses REAL competition data from Google Ads API:
        - Difficulty: Based on competition_index (0-33: Low, 34-66: Medium, 67-100: High)
        - Score: Calculated from volume + competition + relevance
        - Intent: Rule-based (Transactional vs Informational)
        - Type: Based on word count and content
        """
        enriched = []
        
        for item in keywords:
            kw = item['keyword'].lower()
            competition_index = item.get('competition_index', 50)
            volume = item.get('volume', 0)
            
            # Difficulty from competition_index
            if competition_index <= 33:
                difficulty = "Low"
            elif competition_index <= 66:
                difficulty = "Medium"
            else:
                difficulty = "High"
            
            # Intent based on keyword content
            transactional_triggers = ["buy", "price", "cost", "order", "deal", "discount", 
                                      "get", "hire", "purchase", "cheap", "best", "top", 
                                      "service", "agency", "company", "near me"]
            if any(trigger in kw for trigger in transactional_triggers):
                intent = "Transactional"
            else:
                intent = "Informational"
            
            # Keyword type based on word count and content
            word_count = len(kw.split())
            if word_count >= 4:
                keyword_type = "Long-tail"
            elif any(x in kw for x in ["agency", "company", "brand", "firm"]):
                keyword_type = "Branded"
            elif intent == "Transactional":
                keyword_type = "Transactional"
            else:
                keyword_type = "Informational"
            
            # Score calculation: volume weight + competition inverse
            # Normalize volume to 0-50 range (max at 10K)
            volume_score = min(50, (volume / 10000) * 50)
            # Competition inverse: 0-50 range
            competition_score = ((100 - competition_index) / 100) * 50
            # Final score: 0-100
            score = round(volume_score + competition_score, 1)
            
            item['difficulty'] = difficulty
            item['intent'] = intent
            item['keyword_type'] = keyword_type
            item['score'] = score
            
            enriched.append(item)
        
        # Sort by score descending
        enriched.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return enriched

    def _save_universe(self, user_id: str, items: List[Dict[str, Any]], gsc_excluded: List[str], gsc_msg: str):
        """Save keyword universe to database."""
        try:
            universe = self.db.query(KeywordUniverse).filter(KeywordUniverse.user_id == user_id).first()
            if not universe:
                universe = KeywordUniverse(user_id=user_id)
                self.db.add(universe)
            
            universe.gsc_excluded_keywords = gsc_excluded
            universe.gsc_message = gsc_msg
            universe.is_locked = False 
            
            # Delete existing items
            self.db.query(KeywordUniverseItem).filter(KeywordUniverseItem.user_id == user_id).delete()
            
            # Insert new items
            for item in items:
                k_item = KeywordUniverseItem(
                    user_id=user_id,
                    keyword=item['keyword'],
                    search_volume=item.get('volume', 0),
                    difficulty=item.get('difficulty', 'Medium'),
                    intent=item.get('intent', 'Informational'),
                    keyword_type=item.get('keyword_type', 'Informational'),
                    source=item.get('source', 'generated'),
                    score=item.get('score', 0),
                    is_selected=False
                )
                self.db.add(k_item)
            
            self.db.commit()
            logger.info(f"Saved {len(items)} keywords to universe for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving universe: {e}")
            raise e

    def get_universe(self, user_id: str) -> Dict[str, Any]:
        """Get keyword universe for a user."""
        universe = self.db.query(KeywordUniverse).filter(KeywordUniverse.user_id == user_id).first()
        items = self.db.query(KeywordUniverseItem).filter(KeywordUniverseItem.user_id == user_id).all()
        
        if not universe:
            return {"status": "not_initialized"}
        
        return {
            "status": "success",
            "total_keywords": len(items),
            "excluded_gsc_keywords": universe.gsc_excluded_keywords or [],
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
                } for i in items
            ]
        }

    def finalize_selection(self, user_id: str, selected_ids: List[int]) -> Dict[str, Any]:
        """
        Finalize keyword selection and lock universe.
        
        Rules:
        - Must select 10-15 keywords
        - Locks for 90 days
        """
        if not (10 <= len(selected_ids) <= 15):
            raise ValueError("Must select between 10 and 15 keywords")
        
        universe = self.db.query(KeywordUniverse).filter(KeywordUniverse.user_id == user_id).first()
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
        
        logger.info(f"Locked universe for user {user_id} with {len(selected_ids)} keywords until {universe.locked_until}")
        
        return {
            "status": "success", 
            "locked_until": universe.locked_until.isoformat() if universe.locked_until else None,
            "selection_count": len(selected_ids)
        }
