import logging
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date

from Database.models import (
    AsIsScore, 
    AsIsSummaryCache, 
    AsIsProgressTimeline,
    GSCDailyMetrics
)
from asis.asis_service import AsIsStateService
from Database.database import get_db


# ==================== SCORING CONSTANTS ====================
# Status to numeric score mapping
STATUS_SCORES = {
    'critical': 0,
    'needs-attention': 1,
    'needs_attention': 1,
    'optimal': 2
}

# Parameter structure matching As-Is State frontend
# Maps category -> parameter_group_id -> list of sub-parameters
PARAMETER_STRUCTURE = {
    'onpage': {
        'page_topic_keyword_targeting': [
            'target_keyword_presence',
            'primary_vs_secondary_keyword_mapping',
            'keyword_cannibalization_signals',
            'keyword_placement',
            'keyword_consistency'
        ],
        'serp_snippet_optimization': [
            'title_tag_presence_optimization',
            'meta_description_presence_quality',
            'title_meta_duplication',
            'pixel_length_issues',
            'ctr_readiness_signals'
        ],
        'content_structure_hierarchy': [
            'h1_presence_uniqueness',
            'h2_h6_hierarchy',
            'heading_order_issues',
            'first_100_words_relevance',
            'content_sectioning'
        ],
        'accessibility_optimization': [
            'image_alt_text',
            'image_file_naming',
            'image_relevance',
            'lazy_loading_issues',
            'accessibility_compliance'
        ],
        'url_page_signals': [
            'url_structure',
            'url_length',
            'keyword_in_url',
            'parameterized_urls',
            'duplicate_urls',
            'canonical_alignment'
        ]
    },
    'offpage': {
        'domain_authority_trust': [
            'referring_domains_count',
            'authority_score',
            'spam_score',
            'follow_vs_nofollow'
        ],
        'backlink_relevance': [
            'referring_domains',
            'contextual_links',
            'toxic_score',
            'irrelevant_link_detection'
        ],
        'anchor_text_balance': [
            'anchor_text_distribution',
            'exact_match_anchor_frequency'
        ],
        'brand_entity_authority': [
            'unlinked_brand_mentions',
            'brand_citations',
            'brand_name_consistency',
            'industry_mentions'
        ],
        'link_growth_stability': [
            'monthly_link_trend',
            'link_velocity_spikes',
            'historical_growth'
        ]
    },
    'technical': {
        'crawl_indexation': [
            'xml_sitemap_health',
            'robots_txt_configuration',
            'indexed_vs_non_indexed_pages',
            'crawl_budget_efficiency',
            'orphan_urls'
        ],
        'canonicalization_duplicate': [
            'canonical_tag_implementation',
            'duplicate_urls',
            'http_vs_https_duplicates',
            'trailing_slash_issues'
        ],
        'page_experience_performance': [
            'lcp_performance',
            'inp_performance',
            'cls_stability',
            'mobile_vs_desktop_cwv'
        ],
        'search_rendering_accessibility': [
            'javascript_rendering_issues',
            'delayed_lazy_content',
            'hidden_content',
            'client_side_rendering_risks',
            'critical_resource_blocking'
        ],
        'ai_llm_crawl': [
            'llm_txt_presence_rules',
            'ai_crawler_permissions',
            'content_usage_signals',
            'ai_indexing_exposure'
        ]
    }
}

# Human-readable category names
CATEGORY_DISPLAY_NAMES = {
    'page_topic_keyword_targeting': 'Page Topic & Keyword Targeting',
    'serp_snippet_optimization': 'SERP Snippet Optimization',
    'content_structure_hierarchy': 'Content Structure & Semantic Hierarchy',
    'accessibility_optimization': 'Accessibility Optimization',
    'url_page_signals': 'URL & Page Level Signals',
    'domain_authority_trust': 'Domain Authority & Trust Signals',
    'backlink_relevance': 'Backlink Relevance & Topic Alignment',
    'anchor_text_balance': 'Anchor Text Profile & Risk Balance',
    'brand_entity_authority': 'Brand Mentions & Entity Authority',
    'link_growth_stability': 'Link Growth Stability',
    'crawl_indexation': 'Crawl & Indexation',
    'canonicalization_duplicate': 'Canonicalization & Duplicate Control',
    'page_experience_performance': 'Page Experience Performance',
    'search_rendering_accessibility': 'Search Rendering Accessibility',
    'ai_llm_crawl': 'AI & LLM Crawl'
}


class GovernanceAsIsService(AsIsStateService):
    """
    Extended As-Is Service for Governance Dashboard.
    Adds capabilities for baseline tracking, delta calculation, 
    and progress timeline management.
    """
    
    def __init__(self, db_session: Session):
        # Initialize parent service
        # Note: Parent __init__ doesn't take session, but methods do
        # We'll store session here for governance specific methods
        super().__init__()
        self.db = db_session

    def get_performance_overview(self, user_id: str) -> Dict[str, Any]:
        """
        Get high-level performance metrics with baseline comparison.
        """
        # Get latest summary from cache
        summary = self.db.query(AsIsSummaryCache).filter(
            AsIsSummaryCache.user_id == user_id
        ).first()
        
        # if not summary:
        #    return {
        #        "overall_score": 0,
        #        "baseline_score": 0,
        #        "score_delta": 0,
        #        "metrics": {}
        #    }
            
        # Calculate overall weighted score
        current_score = summary.your_visibility_score if summary else 0
        baseline_score = summary.baseline_visibility_score if summary else 0
        
        # Fallback: If visibility score is 0 (e.g. SERP API failed), 
        # calculate average of available category scores
        if current_score == 0:
            # Fetch all current non-baseline scores
            all_scores = self.db.query(AsIsScore).filter(
                AsIsScore.user_id == user_id,
                AsIsScore.is_baseline == False
            ).all()
            
            if all_scores:
                total_current = sum([s.score for s in all_scores])
                max_total = sum([s.max_score for s in all_scores])
                if max_total > 0:
                    current_score = (total_current / max_total) * 100

            # Try to get baseline from scores if summary baseline is 0
            if baseline_score == 0:
                 baseline_scores = self.db.query(AsIsScore).filter(
                    AsIsScore.user_id == user_id,
                    AsIsScore.is_baseline == True
                ).all()
                 if baseline_scores:
                    total_base = sum([s.score for s in baseline_scores])
                    max_base = sum([s.max_score for s in baseline_scores])
                    if max_base > 0:
                        baseline_score = (total_base / max_base) * 100

        metrics_data = {}
        if summary:
             metrics_data = {
                "organic_traffic": {
                    "current": summary.total_clicks,
                    "baseline": summary.baseline_total_clicks,
                    "delta": self._calculate_delta(summary.total_clicks, summary.baseline_total_clicks)
                },
                "keyword_rankings": {
                    "current": summary.top10_keywords,
                    "baseline": summary.baseline_top10_keywords,
                    "delta": self._calculate_delta(summary.top10_keywords, summary.baseline_top10_keywords)
                },
                "avg_position": {
                    "current": summary.avg_position,
                    "baseline": summary.baseline_avg_position,
                    "delta": self._calculate_delta(summary.avg_position, summary.baseline_avg_position, inverse=True)
                }
            }
        
        # Ensure scores are not None before rounding
        if current_score is None:
            current_score = 0.0
        if baseline_score is None:
            baseline_score = 0.0
            
        return {
            "overall_score": round(current_score, 1),
            "baseline_score": round(baseline_score, 1),
            "score_delta": round(current_score - baseline_score, 1),
            "metrics": metrics_data
        }

    def get_category_performance(self, user_id: str, category: str = "onpage") -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific category with baselines.
        """
        # Map frontend category names to DB values
        tab_map = {
            "onpage": "onpage",
            "offpage": "offpage",
            "technical": "technical", 
            "cwv": "cwv"
        }
        
        db_tab = tab_map.get(category, "onpage")
        
        # Get current scores
        current_scores = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.parameter_tab == db_tab,
            AsIsScore.is_baseline == False
        ).all()
        
        # Calculate overall category score
        if not current_scores:
            return {"overall_score": 0, "delta": 0, "sub_metrics": []}
            
        total_current = sum([s.score for s in current_scores])
        max_total = sum([s.max_score for s in current_scores])
        category_score = (total_current / max_total * 100) if max_total > 0 else 0
        
        # Calculate baseline category score
        total_baseline = sum([s.baseline_score for s in current_scores if s.baseline_score is not None])
        if total_baseline == 0 and max_total > 0:
             # If no explicit baseline stored, maybe it's the first run?
             baseline_score = category_score
        else:
             baseline_score = (total_baseline / max_total * 100) if max_total > 0 else 0

        # Build sub-metrics list
        sub_metrics = []
        for item in current_scores:
            sub_metrics.append({
                "name": item.parameter_group,
                "current": item.score,
                "baseline": item.baseline_score,
                "max": item.max_score,
                "delta": self._calculate_delta(item.score, item.baseline_score),
                "status": item.status
            })
            
        return {
            "overall_score": round(category_score, 1),
            "baseline_score": round(baseline_score, 1),
            "delta": round(category_score - baseline_score, 1),
            "sub_metrics": sub_metrics
        }

    def get_progress_timeline(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent progress timeline events.
        """
        events = self.db.query(AsIsProgressTimeline).filter(
            AsIsProgressTimeline.user_id == user_id
        ).order_by(desc(AsIsProgressTimeline.event_timestamp)).limit(limit).all()
        
        return [{
            "id": e.id,
            "type": e.event_type,
            "title": e.event_title,
            "description": e.event_description,
            "timestamp": e.event_timestamp,
            "category": e.category,
            "delta": e.change_delta
        } for e in events]

    def capture_baseline(self, user_id: str) -> bool:
        """
        Capture current state as the baseline.
        Typically called after initial onboarding analysis is complete.
        """
        try:
            # Update AsIsScores
            scores = self.db.query(AsIsScore).filter(
                AsIsScore.user_id == user_id,
                AsIsScore.is_baseline == False
            ).all()
            
            for score in scores:
                score.baseline_score = score.score
                
            # Update Summary Cache
            summary = self.db.query(AsIsSummaryCache).filter(
                AsIsSummaryCache.user_id == user_id
            ).first()
            
            if summary:
                summary.baseline_total_clicks = summary.total_clicks
                summary.baseline_total_impressions = summary.total_impressions
                summary.baseline_avg_position = summary.avg_position
                summary.baseline_top10_keywords = summary.top10_keywords
                summary.baseline_features_count = summary.features_count
                summary.baseline_your_rank = summary.your_rank
                summary.baseline_visibility_score = summary.your_visibility_score
                summary.baseline_captured_at = datetime.now()
                
            # Log event
            self._log_event(
                user_id, 
                "baseline_captured", 
                "Baseline Performance Captured", 
                "Initial SEO health metrics have been established as the baseline for tracking progress."
            )
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            # Log error
            return False

    def _calculate_delta(self, current: float, baseline: float, inverse: bool = False) -> float:
        """
        Calculate delta between current and baseline.
        Inverse=True means lower is better (e.g. rank position, page load time).
        """
        if current is None or baseline is None:
            return 0.0
            
        delta = current - baseline
        if inverse:
            delta = -delta  # If rank goes from 10 to 5, delta is -5, but that's +5 improvement
            
        return round(delta, 1)

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
        Trigger full data refresh and update cache.
        """
        # 1. Run standard refresh (fetches data + saves AsIsScores)
        refresh_result = await super().refresh_data(
             user_id, access_token, site_url, priority_urls, tracked_keywords, competitors
        )
        
        summary_data = await self.get_summary(
             user_id, access_token, site_url, tracked_keywords, competitors,
             force_refresh=True
        )
        
        # 3. Save Summary to Cache Table
        try:
             # Check if exists
             cache_entry = self.db.query(AsIsSummaryCache).filter(
                 AsIsSummaryCache.user_id == user_id
             ).first()
             
             if not cache_entry:
                 cache_entry = AsIsSummaryCache(user_id=user_id)
                 self.db.add(cache_entry)
                 
             # Map fields from summary_data to model
             traffic = summary_data.get("organic_traffic", {})
             keywords = summary_data.get("keywords_performance", {})
             serp = summary_data.get("serp_features", {})
             comp = summary_data.get("competitor_rank", {})
             
             cache_entry.total_clicks = traffic.get("total_clicks", 0)
             cache_entry.total_impressions = traffic.get("total_impressions", 0)
             
             cache_entry.avg_position = keywords.get("avg_position", 0)
             cache_entry.top10_keywords = keywords.get("top10_keywords", 0)
             
             cache_entry.features_count = serp.get("features_count", 0)
             
             cache_entry.your_rank = comp.get("your_rank")
             cache_entry.your_visibility_score = comp.get("your_visibility_score", 0)
             
             cache_entry.last_updated = datetime.now()
             
             self.db.commit()
             refresh_result["summary_cache_updated"] = True
             
        except Exception as e:
            self.db.rollback()
            # Log but don't fail the whole request
            refresh_result["summary_cache_error"] = str(e)
            
        return refresh_result

    def _log_event(self, user_id: str, event_type: str, title: str, description: str = None, 
                   category: str = None, delta: float = None):
        """Helper to log timeline events"""
        event = AsIsProgressTimeline(
            user_id=user_id,
            event_type=event_type,
            event_title=title,
            event_description=description,
            category=category,
            change_delta=delta
        )
        self.db.add(event)

    # ==================== STATUS-BASED SCORING METHODS ====================
    
    def _status_to_score(self, status: str) -> int:
        """Convert status string to numeric score (Critical=0, Needs Attention=1, Optimal=2)"""
        if not status:
            return 1  # Default to needs-attention if no status
        normalized = status.lower().replace(' ', '_').replace('-', '_')
        # Handle 'needs_improvement' as 'needs_attention'
        if 'needs' in normalized and ('improvement' in normalized or 'attention' in normalized):
            return 1
        return STATUS_SCORES.get(normalized, 1)
    
    def _get_scores_from_db(self, user_id: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Fetch all AsIsScore entries for the user and build a map of 
        {parameter_tab: {parameter_group: details_dict}}
        
        We pull the 'details' JSON which contains the individual sub-parameter assessments.
        """
        scores = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.is_baseline == False
        ).all()
        
        result = {}
        for score in scores:
            tab = score.parameter_tab
            group = score.parameter_group
            
            if tab not in result:
                result[tab] = {}
            
            # Parse the details JSON to get sub-parameter data
            details = {}
            if score.details:
                try:
                    # It might be stored as string or already dict depending on ORM/driver
                    if isinstance(score.details, str):
                        data = json.loads(score.details)
                        is_str = True
                    else:
                        data = score.details
                        is_str = False
                    
                    # Handle nested details structure which is common (e.g. {group_id:..., details: {...}})
                    if isinstance(data, dict) and 'details' in data and isinstance(data['details'], dict):
                        details = data['details']
                    else:
                        details = data
                        
                except Exception as e:
                    pass
            
            result[tab][group] = details
            
        return result
    
    def _calculate_category_scores(
        self, 
        db_scores: Dict[str, Dict[str, Any]], 
        category_structure: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Calculate score for a category implicitly using the formula:
        Percentage = (Sum of individual sub-parameter scores) / (Total Max Score) * 100
        
        Where:
        - Critical = 0
        - Needs Attention = 1
        - Optimal = 2
        - Max Score per sub-parameter = 2
        """
        total_score = 0
        max_score = 0
        total_params = 0
        groups_breakdown = {}
        
        for group_id, params in category_structure.items():
            param_count = len(params)
            group_max = param_count * 2
            
            # Get the detailed sub-parameter data for this group
            group_details = db_scores.get(group_id, {})
            
            group_total_score = 0
            
            # Iterate through each EXPECTED sub-parameter for this group
            for sub_param in params:
                # Find the specific sub-parameter in the details
                # The keys in details match the sub-parameter names
                sub_data = group_details.get(sub_param, {})
                status = sub_data.get('status', 'needs_improvement')
                
                score = self._status_to_score(status)
                group_total_score += score
            
            # Aggregate for category totals
            total_score += group_total_score
            max_score += group_max
            total_params += param_count
            
            # Group percentage
            group_percentage = (group_total_score / group_max * 100) if group_max > 0 else 0
            
            # Determine overall group status based on percentage
            if group_percentage >= 80:
                group_status = 'optimal'
            elif group_percentage >= 50:
                group_status = 'needs_improvement'
            else:
                group_status = 'critical'
            
            groups_breakdown[group_id] = {
                'name': CATEGORY_DISPLAY_NAMES.get(group_id, group_id),
                'score': round(group_percentage, 1),
                'total_score': group_total_score,
                'max_score': group_max,
                'status': group_status,
                'param_count': param_count
            }
        
        category_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'score': round(category_percentage, 1),
            'total_score': total_score,
            'max_score': max_score,
            'param_count': total_params,
            'groups': groups_breakdown
        }
    
    def get_asis_performance_scores(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate As-Is Performance scores based on status values.
        
        Scoring:
        - Critical = 0
        - Needs Attention = 1
        - Optimal = 2
        
        Category % = (sum of scores / max possible) × 100
        Overall % = (sum of ALL scores / total max) × 100
        
        Returns:
            {
                'overall_score': percentage,
                'overall_total_score': sum,
                'overall_max_score': max,
                'onpage': {...category breakdown...},
                'offpage': {...category breakdown...},
                'technical': {...category breakdown...}  # Core Vitals
            }
        """
        # Fetch status data from DB
        db_scores = self._get_scores_from_db(user_id)
        
        # Calculate scores for each tab
        onpage_scores = self._calculate_category_scores(
            db_scores.get('onpage', {}),
            PARAMETER_STRUCTURE['onpage']
        )
        
        offpage_scores = self._calculate_category_scores(
            db_scores.get('offpage', {}),
            PARAMETER_STRUCTURE['offpage']
        )
        
        technical_scores = self._calculate_category_scores(
            db_scores.get('technical', {}),
            PARAMETER_STRUCTURE['technical']
        )
        
        # Calculate overall score (NOT averaged, but summed)
        overall_total = (
            onpage_scores['total_score'] + 
            offpage_scores['total_score'] + 
            technical_scores['total_score']
        )
        overall_max = (
            onpage_scores['max_score'] + 
            offpage_scores['max_score'] + 
            technical_scores['max_score']
        )
        overall_percentage = (overall_total / overall_max * 100) if overall_max > 0 else 0
        
        return {
            'overall_score': round(overall_percentage, 1),
            'overall_total_score': overall_total,
            'overall_max_score': overall_max,
            'total_param_count': (
                onpage_scores['param_count'] + 
                offpage_scores['param_count'] + 
                technical_scores['param_count']
            ),
            'onpage': {
                'name': 'On-Page SEO',
                'subtitle': 'Content & Structure',
                **onpage_scores
            },
            'offpage': {
                'name': 'Off-Page SEO',
                'subtitle': 'Backlinks & Authority',
                **offpage_scores
            },
            'technical': {
                'name': 'Core Web Vitals',
                'subtitle': 'Performance & UX',
                **technical_scores
            }
        }
