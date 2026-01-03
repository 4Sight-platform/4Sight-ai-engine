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
        
        # 2. Get latest summary data (computed from fresh fetches/db)
        summary_data = await self.get_summary(
             user_id, access_token, site_url, tracked_keywords, competitors
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
        
