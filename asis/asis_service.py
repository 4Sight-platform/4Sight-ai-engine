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
from .serp_service import SERPService
from .crawler_service import CrawlerService
from .signal_engine import SignalEngine
from .competitor_scoring import CompetitorScoringService
from .psi_service import PageSpeedService
from .backlink_analyzer import BacklinkAnalyzer

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
    
    def __init__(self, serp_api_key: str = None, psi_api_key: str = None):
        self.serp_api_key = serp_api_key or os.getenv("SERP_API_KEY")
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
        serp_service = SERPService(self.serp_api_key) if self.serp_api_key else None
        
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
        
        # Build summary
        summary = {
            "organic_traffic": self._build_traffic_card(gsc_data),
            "keywords_performance": self._build_keywords_card(gsc_data, tracked_keywords),
            "serp_features": self._build_serp_card(serp_analysis),
            "competitor_rank": self._build_competitor_card(
                site_url, tracked_keywords, competitors, gsc_data, serp_analysis
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
    
    def _build_competitor_card(
        self,
        site_url: str,
        tracked_keywords: List[str] = None,
        competitors: List[str] = None,
        gsc_data: Dict = None,
        serp_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build Competitor Rank card data with real scoring if available."""
        if not competitors:
            return {
                "your_rank": None,
                "total_competitors": 0,
                "your_visibility_score": 0,
                "empty_state": True,
                "message": "No competitors configured"
            }
        
        domain = urlparse(site_url).netloc.replace("www.", "")
        total_kws = len(tracked_keywords) if tracked_keywords else 20
        
        # Calculate user's score based on GSC data
        user_rankings = []
        if gsc_data:
            queries = gsc_data.get("current", {}).get("queries", [])
            # Filter to tracked keywords if available
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
        
        # Calculate Competitor Scores using SERP Analysis
        competitor_scores = []
        
        if serp_analysis and serp_analysis.get("results"):
            # Real Data Logic
            # Group rankings by competitor
            comp_rankings = {c: [] for c in competitors}
            
            for res in serp_analysis["results"]:
                kw = res.get("keyword")
                for entry in res.get("competitors_in_top10", []):
                    c_domain = entry.get("domain")
                    
                    found_comp = next((c for c in competitors if c.lower() in c_domain.lower() or c_domain.lower() in c.lower()), None)
                    if found_comp:
                        comp_rankings[found_comp].append({
                            "keyword": kw,
                            "position": entry.get("position", 100)
                        })

            for comp in competitors[:5]:
                rankings = comp_rankings.get(comp, [])
                score_data = self.competitor_service.compute_visibility_score(
                    comp,
                    rankings,
                    total_keywords=total_kws
                )
                competitor_scores.append(score_data)
                
        else:
            # Fallback Logic (MVP / Mock)
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
        status_filter: str = None,
        tracked_keywords: List[str] = None
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
            parameters = self.signal_engine.compute_on_page_scores(signals, tracked_keywords)
        
        elif tab == "offpage":
            gsc_service = GSCDataService(access_token)
            links_data = await gsc_service.fetch_links(site_url)
            
            # Use enhanced backlink analyzer
            linking_domains = links_data.get("top_linking_sites", [])
            if linking_domains and len(linking_domains) > 0:
                backlink_analysis = await self.backlink_analyzer.analyze_backlinks(
                    domain, linking_domains, max_domains=10
                )
                health_scores = self.backlink_analyzer.compute_off_page_health(backlink_analysis)
            else:
                backlink_analysis = {}
                health_scores = {}
            
            backlink_data = {
                "referring_domains": links_data.get("referring_domains", 0),
                "dofollow_ratio": backlink_analysis.get("dofollow_ratio", 0.5),
                "avg_authority_score": backlink_analysis.get("avg_authority_score", 50),
                "anchor_text_distribution": backlink_analysis.get("anchor_distribution", {}),
                "health_scores": health_scores
            }
            parameters = self.signal_engine.compute_off_page_scores(backlink_data)
        
        elif tab == "technical":
            technical_data = await self._gather_technical_signals(domain)
            
            # Fetch CWV data from PageSpeed Insights
            cwv_data = {}
            if self.psi_service and priority_urls:
                try:
                    cwv_result = await self.psi_service.get_cwv_both_devices(priority_urls[0])
                    cwv_data = {
                        "overall_status": cwv_result.get("overall_status", "needs_improvement"),
                        "lcp_status": cwv_result.get("mobile", {}).get("lcp_status"),
                        "inp_status": cwv_result.get("mobile", {}).get("inp_status"),
                        "cls_status": cwv_result.get("mobile", {}).get("cls_status"),
                        "mobile_pass": cwv_result.get("mobile_pass", False),
                        "desktop_pass": cwv_result.get("desktop_pass", False)
                    }
                except Exception as e:
                    logger.error(f"[AS-IS] PSI error: {e}")
            
            ai_governance = await self.crawler.check_robots_txt(domain)
            llm_data = await self.crawler.check_llm_txt(domain)
            ai_governance.update(llm_data)
            
            parameters = self.signal_engine.compute_technical_scores(
                technical_data, cwv_data, ai_governance
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
                     status=p.get("status", "needs_attention"),
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
