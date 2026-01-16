#asis service
"""
AS-IS State Service
Main orchestration service for the AS-IS State feature
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from Database.database import get_db
from Database.models import (
    AsIsScore, AsIsSummaryCache, OnPageSignal, BacklinkSignal, 
    TechnicalSignal, CWVSignal, AICrawlGovernance
)

from .gsc_data_service import GSCDataService
from .enhanced_gsc_service import EnhancedGSCService
from .serp_service import SERPService
from .serp_ranking_service import SERPRankingService
from .crawler_service import CrawlerService
from .signal_engine import SignalEngine
from .competitor_scoring import CompetitorScoringService
from .psi_service import PageSpeedService
from .backlink_analyzer import BacklinkAnalyzer
from .brand_mention_service import BrandMentionService

logger = logging.getLogger(__name__)


class AsIsStateService:
    """
    Main service for AS-IS State feature.
    
    Orchestrates:
    - GSC data fetching
    - SERP feature analysis
    - Page crawling
    - Signal computation
    - Score calculation
    """
    
    def __init__(
        self, 
        serp_api_key: str = None, 
        psi_api_key: str = None,
        google_cse_api_key: str = None,
        google_cse_cx: str = None,
        serper_api_key: str = None
    ):
        self.serp_api_key = serp_api_key or os.getenv("SERP_API_KEY")
        self.google_cse_api_key = google_cse_api_key or os.getenv("GOOGLE_CSE_API_KEY")
        self.google_cse_cx = google_cse_cx or os.getenv("GOOGLE_CSE_CX")
        self.serper_api_key = serper_api_key or os.getenv("SERPER_API_KEY")
        
        self.psi_api_key = psi_api_key or os.getenv("PSI_API_KEY")
        self.signal_engine = SignalEngine()
        self.competitor_service = CompetitorScoringService()
        self.crawler = CrawlerService()
        self.backlink_analyzer = BacklinkAnalyzer()
        self.psi_service = PageSpeedService(self.psi_api_key) if self.psi_api_key else None
    
    async def get_summary(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None,
        force_refresh: bool = False,
        skip_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Get AS-IS summary data for the four top cards.
        
        DB-FIRST APPROACH:
        1. Check database for cached data within 3 months
        2. If found, return cached data (no API calls)
        3. If not found or older than 3 months, fetch live data and save
        
        Args:
            force_refresh: If True, bypasses cache and fetches live data
            skip_cache: If True, completely skips DB cache (for debugging)
        
        Returns:
            Dict with card data for:
            - Organic Traffic
            - Keywords Performance
            - SERP Features
            - Competitor Rank
        """
        MAX_CACHE_AGE_DAYS = 90  # 3 months
        
        # === STEP 1: Check DB for recent cached data ===
        if skip_cache:
            logger.info(f"[AS-IS] ⚠️ skip_cache=True - bypassing DB, fetching live data")
        else:
            logger.info(f"[AS-IS] 🔍 Checking database for cached summary... (user: {user_id})")
        
        if not force_refresh and not skip_cache:
            try:
                db = next(get_db())
                cache = db.query(AsIsSummaryCache).filter(
                    AsIsSummaryCache.user_id == user_id
                ).first()
                
                if cache and cache.last_updated:
                    cache_age = (datetime.now() - cache.last_updated).days
                    
                    if cache_age <= MAX_CACHE_AGE_DAYS:
                        logger.info(f"[AS-IS] ✅ Found data in DB! Age: {cache_age} days. Returning cached summary.")
                        
                        # === Use full_summary JSONB if available (complete data) ===
                        if cache.full_summary:
                            cached_summary = dict(cache.full_summary)
                            cached_summary["from_cache"] = True
                            cached_summary["sync_source"] = "database"
                            last_synced_str = cache.last_updated.strftime("%b %d, %Y at %H:%M") if cache.last_updated else "Unknown"
                            cached_summary["sync_message"] = f"Data loaded from database (last synced: {last_synced_str})"
                            cached_summary["cache_age_days"] = cache_age
                            cached_summary["last_updated"] = cache.last_updated.isoformat() if cache.last_updated else None
                            db.close()
                            return cached_summary
                        
                        # === Fallback: Build from individual fields (legacy) ===
                        import json
                        features_present = []
                        if cache.features_present:
                            try:
                                features_present = json.loads(cache.features_present)
                            except:
                                features_present = []
                        
                        cached_summary = {
                            "organic_traffic": {
                                "total_clicks": cache.total_clicks or 0,
                                "clicks_change": cache.clicks_change or 0,
                                "clicks_change_direction": "up" if (cache.clicks_change or 0) > 0 else "down" if (cache.clicks_change or 0) < 0 else "neutral",
                                "total_impressions": cache.total_impressions or 0,
                                "impressions_change": cache.impressions_change or 0,
                                "impressions_change_direction": "up" if (cache.impressions_change or 0) > 0 else "down" if (cache.impressions_change or 0) < 0 else "neutral",
                                "top_pages": cache.top_pages or [],
                                "data_available": True
                            },
                            "keywords_performance": {
                                "avg_position": cache.avg_position or 0,
                                "position_change": cache.position_change or 0,
                                "position_change_direction": "up" if (cache.position_change or 0) > 0 else "down" if (cache.position_change or 0) < 0 else "neutral",
                                "top10_keywords": cache.top10_keywords or 0,
                                "top10_change": cache.top10_change or 0,
                                "ranked_keywords": cache.ranked_keywords or [],
                                "data_available": True
                            },
                            "serp_features": cache.serp_features_detail or {
                                "features_count": cache.features_count or 0,
                                "features_present": features_present,
                                "data_available": True
                            },
                            "competitor_rank": {
                                "your_rank": cache.your_rank,
                                "total_competitors": cache.total_competitors or 0,
                                "your_visibility_score": cache.your_visibility_score or 0,
                                "rankings": cache.competitor_rankings or [],
                                "data_available": cache.your_rank is not None
                            },
                            "last_updated": cache.last_updated.isoformat() if cache.last_updated else None,
                            "from_cache": True,
                            "sync_source": "database",
                            "sync_message": f"Data loaded from database (last synced: {cache.last_updated.strftime('%b %d, %Y at %H:%M') if cache.last_updated else 'Unknown'})",
                            "cache_age_days": cache_age
                        }
                        db.close()
                        return cached_summary
                    else:
                        logger.info(f"[AS-IS] ⚠️ No recent data in DB! Cache is {cache_age} days old (older than {MAX_CACHE_AGE_DAYS} days)")
                else:
                    logger.info(f"[AS-IS] ⚠️ No data found in database for user {user_id}")
                db.close()
            except Exception as e:
                logger.warning(f"[AS-IS] Error checking database: {e}")
        else:
            logger.info(f"[AS-IS] Force refresh requested - skipping DB check")
        
        
        # === STEP 2: Fetch live data from APIs ===
        logger.info(f"[AS-IS] 🔄 Syncing data from APIs... (no recent data in DB)")
        
        # Fetch selected competitors from database
        if not competitors:
            try:
                from Database.models import OnboardingCompetitor
                db = next(get_db())
                selected_comps = db.query(OnboardingCompetitor).filter(
                    OnboardingCompetitor.user_id == user_id,
                    OnboardingCompetitor.is_selected == True
                ).all()
                competitors = [comp.competitor_url for comp in selected_comps]
                logger.info(f"[AS-IS] Fetched {len(competitors)} selected competitors from database")
                db.close()
            except Exception as e:
                logger.error(f"[AS-IS] Error fetching competitors: {e}")
                competitors = []

        # Fetch tracked keywords from Keyword Universe (Primary Source)
        if not tracked_keywords:
            try:
                from Database.models import KeywordUniverseItem
                db = next(get_db())
                selected_kws = db.query(KeywordUniverseItem).filter(
                    KeywordUniverseItem.user_id == user_id,
                    KeywordUniverseItem.is_selected == True
                ).order_by(KeywordUniverseItem.score.desc()).limit(20).all()
                
                tracked_keywords = [kw.keyword for kw in selected_kws]
                logger.info(f"[AS-IS] Fetched {len(tracked_keywords)} target keywords from Keyword Universe")
                db.close()
            except Exception as e:
                logger.error(f"[AS-IS] Error fetching tracked keywords: {e}")
                tracked_keywords = []
        
        # Initialize services
        gsc_service = GSCDataService(access_token)
        
        # Initialize SERP Service with available providers
        has_serp_config = self.serp_api_key or (self.google_cse_api_key and self.google_cse_cx)
        serp_service = SERPService(
            api_key=self.serp_api_key,
            google_cse_key=self.google_cse_api_key,
            google_cse_cx=self.google_cse_cx
        ) if has_serp_config else None
        
        # Fetch GSC data
        try:
            gsc_data = await gsc_service.fetch_all_metrics(site_url)
        except Exception as e:
            logger.error(f"[AS-IS] Error fetching GSC data: {e}")
            gsc_data = None
            
        # Fetch SERP data (shared for SERP & Competitors)
        serp_analysis = None
        if serp_service and tracked_keywords:
            try:
                domain = urlparse(site_url).netloc.replace("www.", "")
                serp_analysis = await serp_service.batch_analyze(
                    keywords=tracked_keywords[:5],
                    target_domain=domain,
                    competitor_domains=competitors[:5] if competitors else None,
                    max_keywords=5
                )
            except Exception as e:
                logger.error(f"[AS-IS] Error fetching SERP data: {str(e)}")
        
        # Fetch Domain Authority from Moz API
        domain_authority = 0
        try:
            import os
            import httpx
            import base64
            
            moz_access_id = os.getenv("MOZ_ACCESS_ID")
            moz_secret_key = os.getenv("MOZ_SECRET_KEY")
            domain = urlparse(site_url).netloc.replace("www.", "") if site_url else ""
            
            if moz_access_id and moz_secret_key and domain:
                logger.info(f"[AS-IS] Fetching Domain Authority from Moz for {domain}")
                credentials = f"{moz_access_id}:{moz_secret_key}"
                encoded = base64.b64encode(credentials.encode()).decode()
                
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        "https://lsapi.seomoz.com/v2/url_metrics",
                        json={"targets": [domain]},
                        headers={"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            domain_authority = int(results[0].get("domain_authority", 0))
                            logger.info(f"[AS-IS] Moz returned DA={domain_authority}")
        except Exception as e:
            logger.error(f"[AS-IS] Error fetching Domain Authority: {str(e)}")
        
        # Build summary
        summary = {
            "organic_traffic": self._build_traffic_card(gsc_data),
            "keywords_performance": self._build_keywords_card(gsc_data, tracked_keywords),
            "serp_features": self._build_serp_card(serp_analysis),
            "competitor_rank": await self._build_competitor_card(
                site_url, tracked_keywords, competitors, gsc_data, serp_analysis
            ),
            "domain_authority": domain_authority,
            "last_updated": datetime.now().isoformat(),
            "from_cache": False,
            "sync_source": "api",
            "sync_message": "Data synced from live APIs (GSC, SERP, Moz)"
        }
        
        # === STEP 3: Save to DB cache ===
        logger.info(f"[AS-IS] 💾 Saving synced data to database...")
        try:
            self._save_summary_to_cache(user_id, summary)
            logger.info(f"[AS-IS] ✅ Data saved to database successfully!")
        except Exception as e:
            logger.error(f"[AS-IS] Error saving summary to cache: {e}")

        return summary
    
    def _save_summary_to_cache(self, user_id: str, summary: Dict[str, Any]):
        """Save summary data to AsIsSummaryCache table including full JSONB"""
        try:
            import json
            db = next(get_db())
            
            # Check for existing cache
            cache = db.query(AsIsSummaryCache).filter(
                AsIsSummaryCache.user_id == user_id
            ).first()
            
            if not cache:
                cache = AsIsSummaryCache(user_id=user_id)
                db.add(cache)
                logger.info(f"[AS-IS] Creating new cache entry for user {user_id}")
            else:
                logger.info(f"[AS-IS] Updating existing cache for user {user_id}")
            
            # Update values
            traffic = summary.get("organic_traffic", {})
            keywords = summary.get("keywords_performance", {})
            serp = summary.get("serp_features", {})
            comp = summary.get("competitor_rank", {})
            
            # === Store aggregate values (for quick queries) ===
            cache.total_clicks = traffic.get("total_clicks", 0)
            cache.clicks_change = traffic.get("clicks_change", 0)
            cache.total_impressions = traffic.get("total_impressions", 0)
            cache.impressions_change = traffic.get("impressions_change", 0)
            
            cache.avg_position = keywords.get("avg_position", 0)
            cache.position_change = keywords.get("position_change", 0)
            cache.top10_keywords = keywords.get("top10_keywords", 0)
            cache.top10_change = keywords.get("top10_change", 0)
            
            cache.features_count = serp.get("features_count", 0)
            cache.features_present = json.dumps(serp.get("features_present", []))
            
            cache.your_rank = comp.get("your_rank")
            cache.total_competitors = comp.get("total_competitors", 0)
            cache.your_visibility_score = comp.get("your_visibility_score", 0)
            
            # === Store complete data as JSONB (for full restore) ===
            # Remove 'from_cache' flag before storing
            summary_to_store = {k: v for k, v in summary.items() if k != 'from_cache'}
            cache.full_summary = summary_to_store
            
            # Store detailed lists separately for flexibility
            cache.ranked_keywords = keywords.get("ranked_keywords", [])
            cache.top_pages = traffic.get("top_pages", [])
            cache.competitor_rankings = comp.get("rankings", [])
            cache.serp_features_detail = serp
            
            # Domain Authority (for Goal Setting)
            cache.domain_authority = summary.get("domain_authority", 0)
            
            # Update timestamp
            cache.last_updated = datetime.now()
            
            db.commit()
            db.close()
            logger.info(f"[AS-IS] Successfully saved full summary cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"[AS-IS] DB Error in save_summary_to_cache: {e}", exc_info=True)
    
    def _build_traffic_card(self, gsc_data: Dict = None) -> Dict[str, Any]:
        """Build Organic Traffic card data with real top pages."""
        if not gsc_data:
            return {
                "total_clicks": 0,
                "clicks_change": 0,
                "clicks_change_direction": "neutral",
                "total_impressions": 0,
                "impressions_change": 0,
                "impressions_change_direction": "neutral",
                "top_pages": [],
                "data_available": False
            }
        
        current = gsc_data.get("current", {}).get("totals", {})
        changes = gsc_data.get("changes", {})
        
        clicks_change = changes.get("clicks_change", 0)
        impressions_change = changes.get("impressions_change", 0)
        
        # Process Top Pages (Real Data)
        current_pages = gsc_data.get("current", {}).get("pages", [])
        previous_pages = gsc_data.get("previous", {}).get("pages", [])
        
        # Map previous pages for change calculation: url -> clicks
        prev_map = {p["page"]: p["clicks"] for p in previous_pages}
        
        top_pages = []
        # Sort by clicks descending and take top 5
        sorted_pages = sorted(current_pages, key=lambda x: x["clicks"], reverse=True)[:5]
        
        for p in sorted_pages:
            url = p["page"]
            clicks = p["clicks"]
            prev_clicks = prev_map.get(url, 0)
            
            # Calculate change details
            if prev_clicks == 0:
                change_str = "+100%" if clicks > 0 else "0%"
            else:
                pct = ((clicks - prev_clicks) / prev_clicks) * 100
                sign = "+" if pct > 0 else ""
                change_str = f"{sign}{int(pct)}%"
            
            # Format path for display
            try:
                path = urlparse(url).path
                if not path: path = "/"
            except:
                path = url
            
            top_pages.append({
                "page": path,
                "visitors": clicks,  # Using Clicks as metric
                "change": change_str
            })
        
        return {
            "total_clicks": current.get("total_clicks", 0),
            "clicks_change": clicks_change,
            "clicks_change_direction": "up" if clicks_change > 0 else "down" if clicks_change < 0 else "neutral",
            "total_impressions": current.get("total_impressions", 0),
            "impressions_change": impressions_change,
            "impressions_change_direction": "up" if impressions_change > 0 else "down" if impressions_change < 0 else "neutral",
            "avg_ctr": current.get("avg_ctr", 0),
            "top_pages": top_pages,
            "data_available": True
        }
    
    def _build_keywords_card(
        self, 
        gsc_data: Dict = None, 
        tracked_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Build Keywords Performance card data."""
        if not gsc_data or not tracked_keywords:
            return {
                "avg_position": 0,
                "position_change": 0,
                "position_change_direction": "neutral",
                "top10_keywords": 0,
                "top10_change": 0,
                "total_keywords": 0,
                "tracked_keywords_count": 0,
                "data_available": False
            }
        
        current_queries = gsc_data.get("current", {}).get("queries", [])
        previous_queries = gsc_data.get("previous", {}).get("queries", [])
        
        # Convert GSC lists to dictionaries for fast lookup
        # Map: keyword -> {clicks, impressions, position}
        curr_map = {q["query"]: q for q in current_queries}
        prev_map = {q["query"]: q for q in previous_queries}
        
        # Helper to calculate stats and get top keywords
        def calc_targeted_stats(query_map, prev_query_map, target_list):
            if not target_list:
                return {"avg_position": 0, "top10_count": 0, "ranked_count": 0, "list": []}
            
            total_position = 0
            ranked_count = 0
            top10_count = 0
            details_list = []
            
            for kw in target_list:
                kw_norm = kw.lower().strip()
                
                # Current Data
                data = query_map.get(kw_norm)
                # Previous Data (for change calculation)
                prev_data = prev_query_map.get(kw_norm)
                
                if data:
                    pos = data.get("position", 101)
                    ranked_count += 1
                    total_position += pos
                    if pos <= 10:
                        top10_count += 1
                else:
                    pos = 101 # Penalty for not ranking
                    total_position += 100 # Add to total for average calc

                # Calculate Change
                prev_pos = prev_data.get("position", 101) if prev_data else 101
                
                # Change logic: Lower position is better. 
                # Prev 50 -> Curr 40 = +10 Improvement.
                change_val = prev_pos - pos
                
                change_str = f"+{int(change_val)}" if change_val > 0 else f"{int(change_val)}"
                
                details_list.append({
                    "keyword": kw,
                    "position": int(pos) if pos <= 100 else 101, # Keep as number for sorting
                    "position_display": str(int(pos)) if pos <= 100 else ">100",
                    "change": change_str,
                    "isTop": pos <= 10
                })

            # Sort by position (best rank first)
            details_list.sort(key=lambda x: x["position"])
            
            # Format for frontend (convert position back to display string if needed, mostly handled above)
            final_list = []
            for item in details_list[:5]: # Top 5 only
                 final_list.append({
                     "keyword": item["keyword"],
                     "position": item["position_display"] if item["position"] <= 100 else "-",
                     "change": item["change"],
                     "isTop": item["isTop"]
                 })

            avg_pos = total_position / len(target_list) if target_list else 0
            
            return {
                "avg_position": round(avg_pos, 1),
                "top10_count": top10_count,
                "ranked_count": ranked_count,
                "list": final_list
            }

        # Calculate metrics using both maps
        curr_stats = calc_targeted_stats(curr_map, prev_map, tracked_keywords)
        
        # Calculate distinct stats for Previous period just for the aggregated numbers comparison
        # (We already did per-keyword change in the main loop above, but need global avg change)
        def calc_prev_totals(query_map, target_list):
            if not target_list: return {"avg_position": 0, "top10_count": 0}
            total = 0
            top10 = 0
            for kw in target_list:
                data = query_map.get(kw.lower().strip())
                pos = data.get("position", 101) if data else 100
                total += pos if data else 100
                if data and pos <= 10: top10 += 1
            return {"avg_position": total / len(target_list), "top10_count": top10}

        prev_stats_totals = calc_prev_totals(prev_map, tracked_keywords)
        
        # Calculate changes
        position_change = round(prev_stats_totals["avg_position"] - curr_stats["avg_position"], 1)
        top10_change = curr_stats["top10_count"] - prev_stats_totals["top10_count"]
        
        return {
            "avg_position": curr_stats["avg_position"],
            "position_change": position_change,
            "position_change_direction": "up" if position_change > 0 else "down" if position_change < 0 else "neutral",
            "top10_keywords": curr_stats["top10_count"],
            "top10_change": top10_change,
            "total_keywords": curr_stats["ranked_count"], # How many we actually found data for
            "tracked_keywords_count": len(tracked_keywords), # How many we are trying to track
            "ranked_keywords": curr_stats["list"], # Top 5 list
            "data_available": True
        }
    
    def _build_serp_card(
        self,
        serp_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build SERP Features card data from pre-fetched analysis."""
        if not serp_analysis:
            return {
                "features_count": 0,
                "features_present": [],
                "domain_in_features": 0,
                "top10_rate": 0,
                "data_available": False,
                "message": "SERP data not available"
            }
        
        return {
            "features_count": len(serp_analysis.get("unique_features_found", [])),
            "features_present": serp_analysis.get("unique_features_found", []),
            "domain_in_features": len(serp_analysis.get("target_feature_presence", {})),
            "top10_rate": serp_analysis.get("top10_rate", 0),
            "data_available": True
        }
    
    
    async def _build_competitor_card(
        self,
        site_url: str,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None,
        gsc_data: Dict = None,
        serp_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build Competitor Rank card data with real SERP-based scoring.
        
        Fetches actual SERP positions for tracked keywords and calculates
        visibility scores for user and competitors.
        """
        if not competitors or not tracked_keywords:
            return {
                "your_rank": None,
                "total_competitors": 0,
                "your_visibility_score": 0,
                "empty_state": True,
                "message": "No competitors or keywords configured",
                "rankings": []
            }
        
        logger.info(f"[Competitor Card] Building rankings for {len(competitors)} competitors, {len(tracked_keywords)} keywords")
        
        domain = urlparse(site_url).netloc.replace("www.", "")
        total_kws = len(tracked_keywords)
        
        # Initialize SERP ranking service
        # Initialize SERP ranking service
        if not (self.google_cse_api_key and self.google_cse_cx) and not self.serper_api_key:
            logger.warning("[Competitor Card] No SERP provider credentials found, using fallback")
            return self._build_competitor_card_fallback(domain, competitors, gsc_data, tracked_keywords)
        
        serp_ranker = SERPRankingService(
            api_key=self.google_cse_api_key,
            cx=self.google_cse_cx,
            serper_api_key=self.serper_api_key
        )
        
        try:
            # Fetch SERP rankings for all keywords
            logger.info(f"[Competitor Card] Fetching SERP rankings...")
            serp_rankings = await serp_ranker.fetch_keyword_rankings(
                keywords=tracked_keywords,
                competitors=competitors,
                user_domain=domain
            )
            
            # Build user rankings from SERP data
            user_rankings = []
            for keyword, data in serp_rankings.items():
                if data.get('user_position'):
                    user_rankings.append({
                        'keyword': keyword,
                        'position': data['user_position']
                    })
            
            # Calculate user's visibility score
            user_score_data = self.competitor_service.compute_visibility_score(
                domain,
                user_rankings,
                total_keywords=total_kws
            )
            
            logger.info(f"[Competitor Card] User score: {user_score_data['visibility_score']}")
            
            # Build competitor rankings from SERP data
            competitor_scores = []
            comp_rankings_map = {comp: [] for comp in competitors}
            
            for keyword, data in serp_rankings.items():
                for comp_data in data.get('competitors', []):
                    comp_domain = comp_data['domain']
                    if comp_domain in comp_rankings_map:
                        comp_rankings_map[comp_domain].append({
                            'keyword': keyword,
                            'position': comp_data['position']
                        })
            
            # Calculate visibility scores for each competitor
            for comp_domain, rankings in comp_rankings_map.items():
                score_data = self.competitor_service.compute_visibility_score(
                    comp_domain,
                    rankings,
                    total_keywords=total_kws
                )
                competitor_scores.append(score_data)
                logger.info(f"[Competitor Card] {comp_domain}: {score_data['visibility_score']}")
            
            # Rank all domains
            ranking_data = self.competitor_service.rank_competitors(
                domain,
                user_score_data["visibility_score"],
                competitor_scores
            )
            
            return {
                "your_rank": ranking_data["user_rank"],
                "total_competitors": ranking_data["total_competitors"],
                "your_visibility_score": ranking_data["user_visibility_score"],
                "rankings": ranking_data["rankings"][:5],  # Top 5 for card
                "empty_state": False
            }
            
        except Exception as e:
            logger.error(f"[Competitor Card] Error fetching SERP rankings: {e}")
            return self._build_competitor_card_fallback(domain, competitors, gsc_data, tracked_keywords)
    
    def _build_competitor_card_fallback(
        self,
        domain: str,
        competitors: List[str],
        gsc_data: Dict,
        tracked_keywords: List[str]
    ) -> Dict[str, Any]:
        """Fallback competitor card using GSC data only."""
        logger.info("[Competitor Card] Using fallback (GSC data only)")
        
        total_kws = len(tracked_keywords) if tracked_keywords else 20
        
        # Calculate user's score based on GSC data
        user_rankings = []
        if gsc_data:
            queries = gsc_data.get("current", {}).get("queries", [])
            if tracked_keywords:
                target_queries = [q for q in queries if q["query"] in tracked_keywords]
            else:
                target_queries = queries[:20]
                
            for q in target_queries:
                user_rankings.append({
                    "keyword": q.get("query", ""),
                    "position": q.get("position", 100)
                })
        
        user_score_data = self.competitor_service.compute_visibility_score(
            domain,
            user_rankings,
            total_keywords=total_kws
        )
        
        # Mock competitor scores (fallback)
        competitor_scores = []
        for comp in competitors[:5]:
            competitor_scores.append({
                "domain": comp,
                "visibility_score": 50 + (hash(comp) % 40)
            })
        
        ranking_data = self.competitor_service.rank_competitors(
            domain,
            user_score_data["visibility_score"],
            competitor_scores
        )
        
        return {
            "your_rank": ranking_data["user_rank"],
            "total_competitors": ranking_data["total_competitors"],
            "your_visibility_score": ranking_data["user_visibility_score"],
            "rankings": ranking_data["rankings"][:5],
            "empty_state": False
        }
    
    
    async def get_parameters(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        priority_urls: List[str] = None,
        tab: str = "onpage",
        status_filter: str = None,
        tracked_keywords: List[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get AS-IS parameter scores for a specific tab.
        
        DB-FIRST APPROACH:
        1. Check database for cached scores within 3 months
        2. If found, return cached data (no API calls)
        3. If not found or older than 3 months, fetch live data and save
        
        Args:
            user_id: User ID
            access_token: OAuth access token
            site_url: User's website
            priority_urls: URLs to crawl (from onboarding)
            tab: 'onpage', 'offpage', or 'technical'
            status_filter: 'optimal' or 'needs_improvement' (None = all)
            force_refresh: If True, bypasses cache and fetches live data
            
        Returns:
            Dict with parameter scores and statuses
        """
        import json
        MAX_CACHE_AGE_DAYS = 90  # 3 months
        
        # === STEP 1: Check DB for recent cached scores ===
        logger.info(f"[AS-IS] 🔍 Checking database for {tab} scores... (user: {user_id})")
        
        if not force_refresh:
            try:
                db = next(get_db())
                
                # Get the most recent scores for this user/tab
                recent_scores = db.query(AsIsScore).filter(
                    AsIsScore.user_id == user_id,
                    AsIsScore.parameter_tab == tab
                ).order_by(AsIsScore.snapshot_date.desc()).first()
                
                if recent_scores and recent_scores.snapshot_date:
                    cache_age = (date.today() - recent_scores.snapshot_date).days
                    
                    if cache_age <= MAX_CACHE_AGE_DAYS:
                        logger.info(f"[AS-IS] ✅ Found {tab} data in DB! Age: {cache_age} days. Returning cached scores.")
                        
                        # Fetch all scores for this tab
                        all_scores = db.query(AsIsScore).filter(
                            AsIsScore.user_id == user_id,
                            AsIsScore.parameter_tab == tab
                        ).all()
                        
                        # Build parameters from cached scores
                        parameters = []
                        for score in all_scores:
                            param_data = {
                                "group_id": score.parameter_group,
                                "name": score.parameter_group,
                                "score": score.score or 0,
                                "status": score.status or "needs_improvement",
                                "tab": score.parameter_tab
                            }
                            # Add details if available
                            if score.details:
                                try:
                                    details = json.loads(score.details)
                                    param_data.update(details)
                                except:
                                    pass
                            parameters.append(param_data)
                        
                        db.close()
                        
                        # Apply status filter
                        if status_filter:
                            parameters = [p for p in parameters if p["status"] == status_filter]
                        
                        # Calculate summary stats
                        total = len(parameters)
                        optimal_count = len([p for p in parameters if p["status"] == "optimal"])
                        needs_improvement_count = len([p for p in parameters if p["status"] == "needs_improvement"])
                        
                        return {
                            "tab": tab,
                            "parameters": parameters,
                            "summary": {
                                "total": total,
                                "optimal": optimal_count,
                                "needs_improvement": needs_improvement_count
                            },
                            "filter_applied": status_filter,
                            "from_cache": True,
                            "sync_source": "database",
                            "sync_message": f"Data loaded from database (last synced: {recent_scores.updated_at.strftime('%b %d, %Y at %H:%M') if recent_scores.updated_at else 'Unknown'})",
                            "cache_age_days": cache_age
                        }
                    else:
                        logger.info(f"[AS-IS] ⚠️ No recent {tab} data in DB! Cache is {cache_age} days old (older than {MAX_CACHE_AGE_DAYS} days)")
                else:
                    logger.info(f"[AS-IS] ⚠️ No {tab} data found in database for user {user_id}")
                db.close()
            except Exception as e:
                logger.warning(f"[AS-IS] Error checking database: {e}")
        else:
            logger.info(f"[AS-IS] Force refresh requested - skipping DB check")
        
        # === STEP 2: Fetch live data from APIs/Crawling ===
        logger.info(f"[AS-IS] 🔄 Syncing {tab} data from APIs... (no recent data in DB)")
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        # Gather signals based on tab
        if tab == "onpage":
            signals = await self._gather_onpage_signals(priority_urls or [site_url])
            parameters = await self.signal_engine.compute_on_page_scores(signals, tracked_keywords)
        
        elif tab == "offpage":
            # Use both standard and enhanced GSC services
            gsc_service = GSCDataService(access_token)
            enhanced_gsc = EnhancedGSCService(access_token)
            brand_service = BrandMentionService()
            
            # Fetch basic links data
            links_data = await gsc_service.fetch_links(site_url)
            
            # Fetch enhanced links with anchors
            try:
                enhanced_links = await enhanced_gsc.fetch_links_with_anchors(site_url)
                # Merge data - enhanced has more details
                if enhanced_links.get("referring_domains", 0) > 0:
                    links_data = enhanced_links
            except Exception as e:
                logger.warning(f"[AS-IS] Enhanced GSC failed, using standard: {e}")
            
            # Use enhanced backlink analyzer with all sub-parameter analysis
            linking_domains = links_data.get("top_linking_sites", [])
            if linking_domains and len(linking_domains) > 0:
                backlink_analysis = await self.backlink_analyzer.analyze_backlinks(
                    domain, linking_domains, max_domains=15
                )
                
                # Calculate spam score
                spam_analysis = self.backlink_analyzer.calculate_spam_score(
                    backlink_analysis, linking_domains
                )
                
                # Analyze link context quality
                links_found = backlink_analysis.get("links_found", [])
                context_analysis = self.backlink_analyzer.analyze_link_context_quality(
                    links_found, domain
                )
                
                # Detect irrelevant links
                relevance_analysis = self.backlink_analyzer.detect_irrelevant_links(
                    linking_domains, domain, target_keywords=tracked_keywords
                )
                
                # Compute health scores (backward compatibility)
                health_scores = self.backlink_analyzer.compute_off_page_health(backlink_analysis)
            else:
                backlink_analysis = {}
                spam_analysis = {"spam_score": 0, "status": "optimal"}
                context_analysis = {"contextual_ratio": 0.5, "status": "needs_improvement"}
                relevance_analysis = {"irrelevant_ratio": 0.3, "status": "needs_improvement"}
                health_scores = {}
            
            # Fetch brand mention data
            brand_data = {}
            try:
                # Get brand name from domain
                brand_name = domain.split('.')[0].title()
                
                brand_mentions = await enhanced_gsc.fetch_brand_mentions(
                    site_url, brand_name, days_back=30
                )
                
                # Analyze brand consistency
                consistency = brand_service.analyze_brand_consistency(
                    brand_name,
                    brand_mentions.get("top_linked_mentions", []),
                    brand_mentions.get("top_unlinked_mentions", [])
                )
                
                # Classify linking domain sources
                source_classification = brand_service.classify_mention_sources(linking_domains)
                
                # Calculate opportunity score
                opportunity = brand_service.calculate_unlinked_opportunity_score(
                    brand_mentions.get('unlinked_mentions_count', 0),
                    brand_mentions.get('linked_mentions_count', 0)
                )
                
                # Entity recognition indicators
                entity_recognition = brand_service.estimate_entity_recognition(domain, brand_name)
                
                brand_data = {
                    **brand_mentions,
                    "consistency_analysis": consistency,
                    "source_classification": source_classification,
                    "opportunity_analysis": opportunity,
                    "entity_recognition": entity_recognition
                }
            except Exception as e:
                logger.warning(f"[AS-IS] Brand mention analysis failed: {e}")
            
            # Consolidate all backlink data for scoring
            backlink_data = {
                "referring_domains": links_data.get("referring_domains", 0),
                "dofollow_ratio": backlink_analysis.get("dofollow_ratio", 0.5),
                "avg_authority_score": backlink_analysis.get("avg_authority_score", 50),
                "anchor_distribution": backlink_analysis.get("anchor_distribution", {}),
                "authority_distribution": backlink_analysis.get("authority_distribution", {}),
                "spam_analysis": spam_analysis,
                "context_analysis": context_analysis,
                "relevance_analysis": relevance_analysis,
                "health_scores": health_scores,
                "brand_data": brand_data
            }
            
            # Compute off-page scores with all 24 sub-parameters
            parameters = self.signal_engine.compute_off_page_scores(
                backlink_data, gsc_data=links_data, brand_data=brand_data
            )
        
        elif tab == "technical":
            technical_data = await self._gather_technical_signals(domain)
            
            # UNBLOCK: Broken Links check (Spider)
            spider_data = None
            try:
                spider_data = await self.signal_engine.site_spider.crawl_and_analyze(site_url)
            except Exception as e:
                logger.error(f"Tech Spider failed: {e}")
            
            # Fetch CWV data from PageSpeed Insights
            cwv_data = {}
            if self.psi_service and priority_urls:
                try:
                    cwv_result = await self.psi_service.get_cwv_both_devices(priority_urls[0])
                    cwv_data = {
                        "overall_status": cwv_result.get("overall_status", "needs_improvement"),
                        "lcp_status": cwv_result.get("mobile", {}).get("lcp_status"),
                        "lcp_value": f"{cwv_result.get('mobile', {}).get('lcp_score', 0)/1000:.1f}s", # Convert ms to s
                        "inp_status": cwv_result.get("mobile", {}).get("inp_status"),
                        "inp_value": f"{cwv_result.get('mobile', {}).get('inp_score', 0)}ms",
                        "cls_status": cwv_result.get("mobile", {}).get("cls_status"),
                        "cls_value": f"{cwv_result.get('mobile', {}).get('cls_score', 0):.2f}",
                        "mobile_pass": cwv_result.get("mobile_pass", False),
                        "desktop_pass": cwv_result.get("desktop_pass", False)
                    }
                except Exception as e:
                    logger.error(f"[AS-IS] PSI error: {e}")
            
            # AI Governance is already inside technical_data from _gather_technical_signals
            ai_governance = {
                "ai_crawlers_blocked": technical_data.get("ai_crawlers_blocked"),
                "ai_crawlers_allowed": technical_data.get("ai_crawlers_allowed"),
                "ai_crawler_policy": technical_data.get("ai_crawler_policy"),
                "llm_txt_detected": technical_data.get("llm_txt_detected")
            }
            
            parameters = self.signal_engine.compute_technical_scores(
                technical_data, cwv_data, ai_governance, spider_data=spider_data
            )
        else:
            parameters = []
        
        if status_filter:
            parameters = [p for p in parameters if p["status"] == status_filter]
        
        # Save to DB (Persistence on Load)
        try:
            import json
            db = next(get_db())
            today = date.today()
            
            # Delete existing for this tab/user
            db.query(AsIsScore).filter(
                AsIsScore.user_id == user_id, 
                AsIsScore.parameter_tab == tab
            ).delete()
            
            for p in parameters:
                 s = AsIsScore(
                     user_id=user_id,
                     parameter_tab=tab,
                     parameter_group=p["group_id"],
                     score=p.get("score", 0),
                     status=p.get("status", "needs_improvement"),
                     details=json.dumps(p),
                     snapshot_date=today
                 )
                 db.add(s)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"[AS-IS] Error saving scores on load: {e}")
            # Don't fail the request if save fails
            
        # Calculate summary stats
        total = len(parameters)
        optimal_count = len([p for p in parameters if p["status"] == "optimal"])
        needs_improvement_count = len([p for p in parameters if p["status"] == "needs_improvement"])
        
        return {
            "tab": tab,
            "parameters": parameters,
            "summary": {
                "total": total,
                "optimal": optimal_count,
                "needs_improvement": needs_improvement_count
            },
            "filter_applied": status_filter,
            "from_cache": False,
            "sync_source": "api",
            "sync_message": f"Data synced from live APIs (crawling + {tab} analysis)"
        }
    
    async def _gather_onpage_signals(self, urls: List[str]) -> Dict[str, Any]:
        """Crawl URLs and aggregate on-page signals."""
        if not urls:
            return {}
        
        # Crawl first URL for MVP
        crawl_result = await self.crawler.crawl_page(urls[0])
        
        if crawl_result.get("crawl_status") == "success":
            return crawl_result.get("signals", {})
        
        return {}
    
    async def _gather_technical_signals(self, domain: str) -> Dict[str, Any]:
        """Gather technical signals for a domain."""
        # 1. Check robots.txt (includes AI rules)
        robots_data = await self.crawler.check_robots_txt(domain)
        
        # 2. Check llm.txt (AI governance)
        llm_data = await self.crawler.check_llm_txt(domain)
        
        # 3. Check Sitemap (basic discovery)
        # Check standard location
        sitemap_url = f"https://{domain}/sitemap.xml"
        sitemap_exists = False
        try:
             async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                 resp = await client.head(sitemap_url, follow_redirects=True)
                 if resp.status_code == 200:
                     sitemap_exists = True
        except:
             pass
             
        # 4. HTTPS Check
        https_enabled = False
        try:
             async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                 resp = await client.get(f"https://{domain}", follow_redirects=True)
                 if resp.url.scheme == "https":
                     https_enabled = True
        except:
             pass

        return {
            "robots_txt_exists": robots_data.get("robots_exists", False),
            "robots_txt_valid": robots_data.get("robots_valid", False),
            "ai_crawler_policy": "Defined" if (robots_data.get("ai_crawlers_blocked") or robots_data.get("ai_crawlers_allowed")) else "Not defined",
            "ai_crawlers_blocked": robots_data.get("ai_crawlers_blocked"),
            "ai_crawlers_allowed": robots_data.get("ai_crawlers_allowed"),
            "llm_txt_detected": llm_data.get("llm_txt_detected", False),
            "sitemap_exists": sitemap_exists,
            "sitemap_valid": sitemap_exists, # Assume valid if 200 OK for MVP
            "https_enabled": https_enabled,
            "index_coverage_ratio": 0.92, # Placeholder until GSC integration
            "crawl_errors": 0, # Placeholder
            "canonical_issues_count": 0, 
            "duplicate_title_count": 0,
            "duplicate_description_count": 0,
            "trailing_slash_consistent": True
        }
    
    async def get_parameter_details(
        self,
        user_id: str,
        tab: str,
        group_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific parameter group.
        
        Returns:
            Dict with sub-parameters, explanations, and recommendations
        """
        details = self.signal_engine.get_group_details(tab, group_id)
        
        # Add recommendations based on group
        recommendations = self._get_recommendations(tab, group_id)
        
        return {
            **details,
            "recommendations": recommendations
        }
    
    def _get_recommendations(self, tab: str, group_id: str) -> List[str]:
        """Get recommendations for a parameter group."""
        recommendations = {
            "page_topic_keyword_targeting": [
                "Ensure primary keyword appears in the title tag",
                "Include target keyword in the H1 heading",
                "Use keyword naturally within the first 100 words"
            ],
            "serp_snippet_optimization": [
                "Keep title tags between 50-60 characters",
                "Write unique meta descriptions of 150-160 characters",
                "Include a call-to-action in the meta description"
            ],
            "content_structure_hierarchy": [
                "Use only one H1 tag per page",
                "Structure content with H2 and H3 subheadings",
                "Aim for content length of 1000+ words for key pages"
            ],
            "media_accessibility": [
                "Add descriptive alt text to all images",
                "Use SEO-friendly image file names",
                "Implement lazy loading for images"
            ],
            "url_page_signals": [
                "Keep URLs under 75 characters",
                "Avoid URL parameters when possible",
                "Include target keywords in URLs"
            ],
            "crawl_indexation": [
                "Submit an XML sitemap to Search Console",
                "Ensure robots.txt doesn't block important pages",
                "Monitor and fix crawl errors regularly"
            ],
            "page_experience_cwv": [
                "Optimize images to improve LCP",
                "Minimize JavaScript execution for better INP",
                "Reserve space for dynamic content to reduce CLS"
            ],
            "ai_crawl_governance": [
                "Define explicit rules for AI crawlers in robots.txt",
                "Consider creating an llm.txt file",
                "Review which AI crawlers should access your content"
            ]
        }
        
        return recommendations.get(group_id, [
            "Review and optimize this parameter group",
            "Monitor changes over time",
            "Compare with competitor benchmarks"
        ])
    
    async def get_competitors(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Get competitor visibility scores and rankings.
        
        Returns:
            Dict with competitor data or empty state
        """
        if not competitors:
            return {
                "empty_state": True,
                "message": "No competitors configured. Add competitors in settings.",
                "rankings": []
            }
        
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        # Get user's score
        gsc_service = GSCDataService(access_token)
        try:
            gsc_data = await gsc_service.fetch_all_metrics(site_url)
            queries = gsc_data.get("current", {}).get("queries", [])
            user_rankings = [{"keyword": q["query"], "position": q["position"]} for q in queries[:20]]
        except:
            user_rankings = []
        
        user_score_data = self.competitor_service.compute_visibility_score(
            domain, user_rankings
        )
        
        # Calculate competitor scores (simplified for MVP)
        competitor_scores = []
        for comp in competitors:
            comp_domain = comp.replace("www.", "").replace("https://", "").replace("http://", "").rstrip("/")
            # Placeholder - would use SERP data in production
            competitor_scores.append({
                "domain": comp_domain,
                "visibility_score": 45 + (hash(comp_domain) % 45)
            })
        
        ranking_data = self.competitor_service.rank_competitors(
            domain, user_score_data["visibility_score"], competitor_scores
        )
        
        gap_analysis = self.competitor_service.compute_competitive_gap(
            user_score_data["visibility_score"], competitor_scores
        )
        
        return {
            "empty_state": False,
            "your_domain": domain,
            "your_rank": ranking_data["user_rank"],
            "your_score": ranking_data["user_visibility_score"],
            "total_competitors": len(competitors),
            "rankings": ranking_data["rankings"],
            "gap_analysis": gap_analysis
        }
    
    async def refresh_data(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        priority_urls: List[str] = None,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a full data refresh for AS-IS State.
        Calculates all scores and saves to local database.
        """
        import json
        refresh_start = datetime.now()
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        results = {
            "gsc_data": False,
            "crawl_data": False,
            "serp_data": False,
            "scores_computed": False,
            "db_save": False
        }
        
        try:
            # 1. Fetch Off-Page Data (GSC Links)
            gsc_service = GSCDataService(access_token)
            gsc_data = await gsc_service.fetch_all_metrics(site_url)
            results["gsc_data"] = True
            
            links_data = await gsc_service.fetch_links(site_url)
            # Enhance with backlink analyzer
            linking_domains = links_data.get("top_linking_sites", [])
            if linking_domains:
                backlink_analysis = await self.backlink_analyzer.analyze_backlinks(domain, linking_domains, max_domains=10)
                health_scores = self.backlink_analyzer.compute_off_page_health(backlink_analysis)
            else:
                backlink_analysis = {}
                health_scores = {}
            
            offpage_signals = {
                "referring_domains": links_data.get("referring_domains", 0),
                "dofollow_ratio": backlink_analysis.get("dofollow_ratio", 0.5),
                "avg_authority_score": backlink_analysis.get("avg_authority_score", 50),
                "anchor_text_distribution": backlink_analysis.get("anchor_distribution", {}),
                "health_scores": health_scores
            }
            
            # 2. Fetch On-Page Signals (Crawl)
            onpage_signals = {}
            if priority_urls:
                crawl_results = await self.crawler.crawl_multiple(priority_urls[:3])
                if crawl_results:
                    # Flatten/Aggregate for scoring (using first page for MVP)
                    first_res = crawl_results[0].get("signals", {})
                    onpage_signals = first_res
                    results["crawl_data"] = True
            
            # 3. Fetch Technical Signals
            technical_signals = await self._gather_technical_signals(domain)
            
            # 4. Fetch CWV
            cwv_data = {}
            if self.psi_service and priority_urls:
                try:
                    c = await self.psi_service.get_cwv_both_devices(priority_urls[0])
                    cwv_data = {
                        "overall_status": c.get("overall_status"),
                        "lcp_status": c.get("mobile", {}).get("lcp_status"),
                        "inp_status": c.get("mobile", {}).get("inp_status"),
                        "cls_status": c.get("mobile", {}).get("cls_status")
                    }
                except: pass
            
            # 5. Fetch AI Governance
            ai_gov = await self.crawler.check_robots_txt(domain)
            
            # 6. Compute All Scores
            all_scores = self.signal_engine.compute_all_scores(
                on_page_signals=onpage_signals,
                backlink_data=offpage_signals,
                technical_data=technical_signals,
                cwv_data=cwv_data,
                ai_governance=ai_gov,
                keywords=tracked_keywords
            )
            results["scores_computed"] = True
            
            # 7. Save to DB
            db = next(get_db())
            try:
                # Save Scores (Clear old first)
                db.query(AsIsScore).filter(AsIsScore.user_id == user_id).delete()
                
                today = date.today()
                
                for tab, items in all_scores.items():
                    for item in items:
                        s = AsIsScore(
                            user_id=user_id,
                            parameter_tab=tab,
                            parameter_group=item["group_id"],
                            score=item["score"],
                            status=item["status"],
                            details=json.dumps(item),
                            snapshot_date=today
                        )
                        db.add(s)
                
                # Save Signals (Simplified: OnPage)
                # Note: Signal tables usually unique by user_id in this schema based on previous view
                # but models.py shows UserID is unique in *some* tables (TechnicalSignal) but maybe not others?
                # We'll just upsert/replace.
                
                # OnPage
                db.query(OnPageSignal).filter(OnPageSignal.user_id == user_id).delete()
                ops = OnPageSignal(
                    user_id=user_id,
                    page_url=site_url, # Using site_url as the page_url
                    title_tag=onpage_signals.get("title_tag"),
                    meta_description=onpage_signals.get("meta_description"),
                    h1_text=onpage_signals.get("h1_tag"), # Map h1_tag to h1_text
                    word_count=onpage_signals.get("word_count", 0)
                )
                db.add(ops)
                
                db.commit()
                results["db_save"] = True
            except Exception as e:
                db.rollback()
                logger.error(f"DB Save Error: {e}")
                results["error_db"] = str(e)
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"[AS-IS] Refresh error: {e}")
            results["error"] = str(e)
        
        refresh_end = datetime.now()
        
        return {
            "status": "completed",
            "results": results,
            "duration_seconds": (refresh_end - refresh_start).total_seconds(),
            "refreshed_at": refresh_end.isoformat()
        }
        
        refresh_end = datetime.now()
        
        return {
            "status": "completed",
            "results": results,
            "duration_seconds": (refresh_end - refresh_start).total_seconds(),
            "refreshed_at": refresh_end.isoformat()
        }




