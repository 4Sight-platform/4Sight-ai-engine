"""
AS-IS State Service
Main orchestration service for the AS-IS State feature
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .gsc_data_service import GSCDataService
from .serp_service import SERPService
from .crawler_service import CrawlerService
from .signal_engine import SignalEngine
from .competitor_scoring import CompetitorScoringService

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
    
    def __init__(self, serp_api_key: str = None):
        self.serp_api_key = serp_api_key or os.getenv("SERP_API_KEY")
        self.signal_engine = SignalEngine()
        self.competitor_service = CompetitorScoringService()
        self.crawler = CrawlerService()
    
    async def get_summary(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get AS-IS summary data for the four top cards.
        
        Returns:
            Dict with card data for:
            - Organic Traffic
            - Keywords Performance
            - SERP Features
            - Competitor Rank
        """
        # Initialize services
        gsc_service = GSCDataService(access_token)
        
        # Fetch GSC data
        try:
            gsc_data = await gsc_service.fetch_all_metrics(site_url)
        except Exception as e:
            logger.error(f"[AS-IS] Error fetching GSC data: {e}")
            gsc_data = None
        
        # Build summary
        summary = {
            "organic_traffic": self._build_traffic_card(gsc_data),
            "keywords_performance": self._build_keywords_card(gsc_data, tracked_keywords),
            "serp_features": await self._build_serp_card(site_url, tracked_keywords),
            "competitor_rank": await self._build_competitor_card(
                site_url, tracked_keywords, competitors, gsc_data
            ),
            "last_updated": datetime.now().isoformat()
        }
        
        return summary
    
    def _build_traffic_card(self, gsc_data: Dict = None) -> Dict[str, Any]:
        """Build Organic Traffic card data."""
        if not gsc_data:
            return {
                "total_clicks": 0,
                "clicks_change": 0,
                "clicks_change_direction": "neutral",
                "total_impressions": 0,
                "impressions_change": 0,
                "impressions_change_direction": "neutral",
                "data_available": False
            }
        
        current = gsc_data.get("current", {}).get("totals", {})
        changes = gsc_data.get("changes", {})
        
        clicks_change = changes.get("clicks_change", 0)
        impressions_change = changes.get("impressions_change", 0)
        
        return {
            "total_clicks": current.get("total_clicks", 0),
            "clicks_change": clicks_change,
            "clicks_change_direction": "up" if clicks_change > 0 else "down" if clicks_change < 0 else "neutral",
            "total_impressions": current.get("total_impressions", 0),
            "impressions_change": impressions_change,
            "impressions_change_direction": "up" if impressions_change > 0 else "down" if impressions_change < 0 else "neutral",
            "avg_ctr": current.get("avg_ctr", 0),
            "data_available": True
        }
    
    def _build_keywords_card(
        self, 
        gsc_data: Dict = None, 
        tracked_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Build Keywords Performance card data."""
        if not gsc_data:
            return {
                "avg_position": 0,
                "position_change": 0,
                "position_change_direction": "neutral",
                "top10_keywords": 0,
                "top10_change": 0,
                "total_keywords": 0,
                "data_available": False
            }
        
        current = gsc_data.get("current", {}).get("totals", {})
        changes = gsc_data.get("changes", {})
        
        position_change = changes.get("position_change", 0)
        top10_change = changes.get("top10_change", 0)
        
        return {
            "avg_position": current.get("avg_position", 0),
            "position_change": position_change,
            "position_change_direction": "up" if position_change > 0 else "down" if position_change < 0 else "neutral",
            "top10_keywords": current.get("top10_count", 0),
            "top10_change": top10_change,
            "total_keywords": current.get("keyword_count", 0),
            "tracked_keywords_count": len(tracked_keywords) if tracked_keywords else 0,
            "data_available": True
        }
    
    async def _build_serp_card(
        self,
        site_url: str,
        tracked_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Build SERP Features card data."""
        if not self.serp_api_key or not tracked_keywords:
            return {
                "features_count": 0,
                "features_present": [],
                "domain_in_features": 0,
                "data_available": False,
                "message": "SERP data not available"
            }
        
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        try:
            serp_service = SERPService(self.serp_api_key)
            # Limit to first 5 keywords for MVP (API rate limiting)
            analysis = await serp_service.batch_analyze(
                tracked_keywords[:5],
                domain,
                max_keywords=5
            )
            
            return {
                "features_count": len(analysis.get("unique_features_found", [])),
                "features_present": analysis.get("unique_features_found", []),
                "domain_in_features": len(analysis.get("target_feature_presence", {})),
                "top10_rate": analysis.get("top10_rate", 0),
                "data_available": True
            }
        except Exception as e:
            logger.error(f"[AS-IS] SERP analysis error: {e}")
            return {
                "features_count": 0,
                "features_present": [],
                "domain_in_features": 0,
                "data_available": False,
                "message": str(e)
            }
    
    async def _build_competitor_card(
        self,
        site_url: str,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None,
        gsc_data: Dict = None
    ) -> Dict[str, Any]:
        """Build Competitor Rank card data."""
        if not competitors:
            return {
                "your_rank": None,
                "total_competitors": 0,
                "your_visibility_score": 0,
                "empty_state": True,
                "message": "No competitors configured"
            }
        
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        # Calculate user's score based on GSC data
        user_rankings = []
        if gsc_data:
            queries = gsc_data.get("current", {}).get("queries", [])
            for q in queries[:20]:  # Top 20 queries
                user_rankings.append({
                    "keyword": q.get("query", ""),
                    "position": q.get("position", 100)
                })
        
        user_score_data = self.competitor_service.compute_visibility_score(
            domain,
            user_rankings,
            total_keywords=len(tracked_keywords) if tracked_keywords else 20
        )
        
        # For MVP, we'll estimate competitor scores
        # In production, this would use actual SERP data for competitors
        competitor_scores = []
        for comp in competitors[:5]:
            # Placeholder scores - would be calculated from SERP data
            competitor_scores.append({
                "domain": comp,
                "visibility_score": 50 + (hash(comp) % 40)  # Pseudo-random for demo
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
            "rankings": ranking_data["rankings"][:5],  # Top 5 for card
            "empty_state": False
        }
    
    async def get_parameters(
        self,
        user_id: str,
        access_token: str,
        site_url: str,
        priority_urls: List[str] = None,
        tab: str = "onpage",
        status_filter: str = None
    ) -> Dict[str, Any]:
        """
        Get AS-IS parameter scores for a specific tab.
        
        Args:
            user_id: User ID
            access_token: OAuth access token
            site_url: User's website
            priority_urls: URLs to crawl (from onboarding)
            tab: 'onpage', 'offpage', or 'technical'
            status_filter: 'optimal' or 'needs_attention' (None = all)
            
        Returns:
            Dict with parameter scores and statuses
        """
        domain = urlparse(site_url).netloc.replace("www.", "")
        
        # Gather signals based on tab
        if tab == "onpage":
            signals = await self._gather_onpage_signals(priority_urls or [site_url])
            parameters = self.signal_engine.compute_on_page_scores(signals)
        
        elif tab == "offpage":
            gsc_service = GSCDataService(access_token)
            links_data = await gsc_service.fetch_links(site_url)
            backlink_data = {
                "referring_domains": links_data.get("referring_domains", 0),
                "anchor_text_distribution": {}
            }
            parameters = self.signal_engine.compute_off_page_scores(backlink_data)
        
        elif tab == "technical":
            technical_data = await self._gather_technical_signals(domain)
            cwv_data = {}  # Would come from GSC CWV data
            ai_governance = await self.crawler.check_robots_txt(domain)
            llm_data = await self.crawler.check_llm_txt(domain)
            ai_governance.update(llm_data)
            
            parameters = self.signal_engine.compute_technical_scores(
                technical_data, cwv_data, ai_governance
            )
        else:
            parameters = []
        
        # Apply status filter
        if status_filter:
            parameters = [p for p in parameters if p["status"] == status_filter]
        
        # Calculate summary stats
        total = len(parameters)
        optimal_count = len([p for p in parameters if p["status"] == "optimal"])
        needs_attention_count = len([p for p in parameters if p["status"] == "needs_attention"])
        
        return {
            "tab": tab,
            "parameters": parameters,
            "summary": {
                "total": total,
                "optimal": optimal_count,
                "needs_attention": needs_attention_count
            },
            "filter_applied": status_filter
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
        robots_data = await self.crawler.check_robots_txt(domain)
        
        return {
            "robots_txt_exists": robots_data.get("robots_exists", False),
            "robots_txt_valid": robots_data.get("robots_valid", False),
            "sitemap_exists": False,  # Would check /sitemap.xml
            "sitemap_valid": False,
            "https_enabled": True,  # Assume HTTPS for modern sites
            "index_coverage_ratio": 0.8,  # Placeholder
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
        
        Returns:
            Dict with refresh status
        """
        refresh_start = datetime.now()
        results = {
            "gsc_data": False,
            "crawl_data": False,
            "serp_data": False,
            "scores_computed": False
        }
        
        try:
            # Refresh GSC data
            gsc_service = GSCDataService(access_token)
            gsc_data = await gsc_service.fetch_all_metrics(site_url)
            results["gsc_data"] = True
            
            # Refresh crawl data for priority URLs
            if priority_urls:
                crawl_results = await self.crawler.crawl_multiple(priority_urls[:5])
                results["crawl_data"] = True
            
            # Refresh SERP data (limited for API)
            if self.serp_api_key and tracked_keywords:
                serp_service = SERPService(self.serp_api_key)
                domain = urlparse(site_url).netloc.replace("www.", "")
                await serp_service.batch_analyze(tracked_keywords[:3], domain, competitors, max_keywords=3)
                results["serp_data"] = True
            
            results["scores_computed"] = True
            
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
