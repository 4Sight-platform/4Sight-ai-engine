"""
Goal Setting Service
Generates and manages strategy goals with 90-day cycles
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from Database.models import (
    StrategyGoal, SeoGoal, GSCDailyMetrics, KeywordPositionSnapshot,
    SERPFeaturePresence, AsIsSummaryCache
)

logger = logging.getLogger(__name__)


# Hardcoded targets for first 90 days
HARDCODED_TARGETS = {
    "organic-traffic": {
        "value": "+500",
        "unit": "visitors/month",
        "type": "growth",
        "category": "priority"
    },
    "keyword-rankings": {
        "value": "Slab Distribution",
        "unit": "keywords",
        "type": "slabs",
        "category": "priority",
        "slabs": [
            {"label": "Top 50", "percentage": 50, "color": "bg-green-200"},
            {"label": "Top 20", "percentage": 30, "color": "bg-green-400"},
            {"label": "Top 10", "percentage": 20, "color": "bg-green-600"}
        ]
    },
    "serp-features": {
        "value": "Paused",
        "unit": "SERP features",
        "type": "paused",
        "category": "priority"
    },
    "avg-position": {
        "value": "−3 to −5",
        "unit": "position improvement",
        "type": "range",
        "category": "additional"
    },
    "impressions": {
        "value": "+2,000",
        "unit": "impressions/month",
        "type": "growth",
        "category": "additional"
    },
    "domain-authority": {
        "value": "+4",
        "unit": "DA points",
        "type": "growth",
        "category": "additional"
    }
}


# Mapping from onboarding goal names to goal types
GOAL_NAME_MAPPING = {
    # Title case names (from BRD)
    "Increase Organic Traffic": "organic-traffic",
    "Improve Keyword Rankings": "keyword-rankings",
    "Capture Visibility Features": "serp-features",
    "Reduce Average Position": "avg-position",
    "Increase Impressions": "impressions",
    "Improve Domain Authority": "domain-authority",
    
    # Snake case names (from onboarding database)
    "organic_traffic": "organic-traffic",
    "search_visibility": "serp-features",
    "local_visibility": "serp-features",
    "top_rankings": "keyword-rankings",
    
    # Additional variations
    "Organic Traffic": "organic-traffic",
    "Search Visibility": "serp-features",
    "Local Visibility": "serp-features",
    "Top Rankings": "keyword-rankings"
}


class GoalSettingService:
    """Service for managing strategy goals with 90-day cycles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_goals(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize goals after onboarding completion
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with created goals count and details
        """
        try:
            # Get user's selected SEO goals from onboarding
            seo_goals_record = self.db.query(SeoGoal).filter(
                SeoGoal.user_id == user_id
            ).first()
            
            if not seo_goals_record or not seo_goals_record.goals:
                logger.warning(f"No SEO goals found for user {user_id}")
                return {
                    "success": False,
                    "message": "No SEO goals found for user"
                }
            
            # Check if goals already exist for current cycle
            existing_goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).first()
            
            if existing_goals:
                logger.warning(f"Goals already initialized for user {user_id}")
                return {
                    "success": False,
                    "message": "Goals already initialized for current cycle"
                }
            
            # Set cycle dates (90 days)
            cycle_start = date.today()
            cycle_end = cycle_start + timedelta(days=90)
            
            logger.info(f"Initializing goals for user {user_id}, cycle: {cycle_start} to {cycle_end}")
            
            # Get current metrics from AS-IS data
            current_metrics = self._get_current_metrics(user_id)
            
            # Create goals based on selected onboarding goals
            # Deduplicate: multiple onboarding goal names may map to same goal type
            created_goals = []
            processed_goal_types = set()
            
            for goal_name in seo_goals_record.goals:
                goal_type = GOAL_NAME_MAPPING.get(goal_name)
                
                if not goal_type or goal_type not in HARDCODED_TARGETS:
                    logger.warning(f"Unknown goal name: {goal_name}")
                    continue
                
                # Skip if already processed (e.g., search_visibility and local_visibility both map to serp-features)
                if goal_type in processed_goal_types:
                    logger.info(f"Skipping duplicate goal type: {goal_type} (from {goal_name})")
                    continue
                
                processed_goal_types.add(goal_type)
                
                target_config = HARDCODED_TARGETS[goal_type]
                
                # Get baseline value from current metrics
                baseline_value = current_metrics.get(goal_type, "0")
                
                # Create goal record
                goal = StrategyGoal(
                    user_id=user_id,
                    goal_type=goal_type,
                    goal_category=target_config["category"],
                    cycle_start_date=cycle_start,
                    cycle_end_date=cycle_end,
                    is_locked=True,
                    baseline_value=baseline_value,
                    current_value=baseline_value,
                    target_value=target_config["value"],
                    unit=target_config["unit"],
                    target_type=target_config["type"],
                    slab_data=target_config.get("slabs"),
                    progress_percentage=0.0,
                    last_calculated_at=datetime.utcnow()
                )
                
                self.db.add(goal)
                created_goals.append(goal_type)
            
            # 2. ALWAYS Create "Additional" goals (Impressions, Domain Authority, Avg Position)
            # These are standard supporting metrics that should appear for all users
            for goal_type, config in HARDCODED_TARGETS.items():
                # Skip if already created (e.g. if it was a priority goal)
                if goal_type in processed_goal_types:
                    continue
                
                # Only add if category is 'additional'
                if config["category"] != "additional":
                    continue
                    
                # Get baseline value
                baseline_value = current_metrics.get(goal_type, "0")
                
                goal = StrategyGoal(
                    user_id=user_id,
                    goal_type=goal_type,
                    goal_category=config["category"],
                    cycle_start_date=cycle_start,
                    cycle_end_date=cycle_end,
                    is_locked=True,
                    baseline_value=baseline_value,
                    current_value=baseline_value,
                    target_value=config["value"],
                    unit=config["unit"],
                    target_type=config["type"],
                    slab_data=config.get("slabs"),
                    progress_percentage=0.0,
                    last_calculated_at=datetime.utcnow()
                )
                
                self.db.add(goal)
                created_goals.append(goal_type)
                processed_goal_types.add(goal_type)
            
            self.db.commit()
            
            logger.info(f"Created {len(created_goals)} goals for user {user_id}: {created_goals}")
            
            return {
                "success": True,
                "goals_created": len(created_goals),
                "goal_types": created_goals,
                "cycle_start": cycle_start.isoformat(),
                "cycle_end": cycle_end.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error initializing goals for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _get_current_metrics(self, user_id: str, asis_summary: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Get current metric values from AS-IS data.
        
        Priority order:
        1. Live AS-IS summary data (passed from API endpoint)
        2. Defaults to "0"/empty if live data is not available (NO CACHING as per user request)
        
        Args:
            user_id: User ID
            asis_summary: Live AS-IS summary data (from AsIsStateService.get_summary())
            
        Returns:
            Dict mapping goal_type to current value
        """
        metrics = {}
        
        try:
            if asis_summary:
                # Priority 1: Parse live AS-IS summary data (real-time!)
                logger.info(f"[Goal Setting] Using LIVE AS-IS data for user {user_id}")
                
                traffic = asis_summary.get("organic_traffic", {})
                keywords = asis_summary.get("keywords_performance", {})
                serp = asis_summary.get("serp_features", {})
                
                # Organic Traffic (from clicks) - EXACT value from As-Is State
                metrics["organic-traffic"] = str(traffic.get("total_clicks", 0))
                
                # Average Position - EXACT value from As-Is State
                avg_pos = keywords.get("avg_position", 0)
                metrics["avg-position"] = f"#{avg_pos:.1f}" if avg_pos else "#0"
                
                # Impressions - EXACT value from As-Is State
                metrics["impressions"] = str(traffic.get("total_impressions", 0))
                
                # Keyword Rankings (top 10 keywords count) - EXACT value from As-Is State
                metrics["keyword-rankings"] = str(keywords.get("top10_keywords", 0))
                
                # SERP Features - EXACT value from As-Is State
                metrics["serp-features"] = str(serp.get("features_count", 0))
                
                # Domain Authority - placeholder for now
                metrics["domain-authority"] = "0"
                
                logger.info(f"[Goal Setting] LIVE metrics for user {user_id}: {metrics}")
                
            else:
                # NO CACHING FALLBACK (User Request)
                logger.warning(f"[Goal Setting] No live AS-IS data provided for user {user_id}. Returning empty metrics.")
                metrics["organic-traffic"] = "0"
                metrics["impressions"] = "0"
                metrics["avg-position"] = "#0"
                metrics["keyword-rankings"] = "0"
                metrics["serp-features"] = "0"
                metrics["domain-authority"] = "0"
            
            logger.info(f"Current metrics for user {user_id}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting current metrics for user {user_id}: {str(e)}")
            # Return default values
            return {
                "organic-traffic": "0",
                "keyword-rankings": "0",
                "serp-features": "0",
                "avg-position": "#0",
                "impressions": "0",
                "domain-authority": "0"
            }
    
    def get_user_goals(self, user_id: str, asis_summary: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get all active goals for a user with LIVE current values from AS-IS state.
        
        Args:
            user_id: User ID
            asis_summary: Live AS-IS summary data (from AsIsStateService.get_summary())
            
        Returns:
            List of goal dictionaries with live current_value from AS-IS state
        """
        try:
            goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).order_by(
                StrategyGoal.goal_category.asc(),  # priority first
                StrategyGoal.created_at.asc()
            ).all()
            
            if not goals:
                return []
            
            # Fetch current metrics from LIVE AS-IS data (not cache!)
            current_metrics = self._get_current_metrics(user_id, asis_summary)
            logger.info(f"Fetched live AS-IS metrics for user {user_id}: {current_metrics}")
            
            # Update current values in goals and convert to dict
            goal_dicts = []
            for goal in goals:
                # Get live value from AS-IS State
                live_value = current_metrics.get(goal.goal_type, goal.current_value)
                
                # Update the goal object in DB with latest value
                if live_value != goal.current_value:
                    goal.current_value = live_value
                    goal.last_calculated_at = datetime.utcnow()
                    logger.info(f"Updated {goal.goal_type} current_value: {goal.current_value} -> {live_value}")
                
                # Convert to dict with live current_value
                goal_dict = self._goal_to_dict(goal)
                goal_dict["current_value"] = live_value
                goal_dicts.append(goal_dict)
            
            # Commit the updates to current_value
            self.db.commit()
            
            return goal_dicts
            
        except Exception as e:
            logger.error(f"Error getting goals for user {user_id}: {str(e)}")
            self.db.rollback()
            return []
    
    def can_refresh_goals(self, user_id: str) -> bool:
        """
        Check if user can manually refresh goals (90-day cycle ended)
        
        Args:
            user_id: User ID
            
        Returns:
            True if refresh is allowed, False otherwise
        """
        try:
            active_goal = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).first()
            
            if not active_goal:
                # No active goals, can initialize
                return True
            
            # Check if cycle has ended
            return date.today() >= active_goal.cycle_end_date
            
        except Exception as e:
            logger.error(f"Error checking refresh eligibility for user {user_id}: {str(e)}")
            return False
    
    def refresh_goals(self, user_id: str) -> Dict[str, Any]:
        """
        Manually refresh goals (create new 90-day cycle)
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with refresh result
        """
        try:
            # Check if refresh is allowed
            if not self.can_refresh_goals(user_id):
                return {
                    "success": False,
                    "message": "Cannot refresh goals yet. 90-day cycle not completed."
                }
            
            # Unlock old goals (archive them)
            self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).update({"is_locked": False})
            
            self.db.commit()
            
            # Initialize new cycle
            result = self.initialize_goals(user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error refreshing goals for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def update_goal_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Update current values and progress for all active goals
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with update results
        """
        try:
            # Get current metrics
            current_metrics = self._get_current_metrics(user_id)
            
            # Get active goals
            active_goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).all()
            
            updated_count = 0
            for goal in active_goals:
                # Update current value
                new_current = current_metrics.get(goal.goal_type, goal.baseline_value)
                goal.current_value = new_current
                
                # Calculate progress percentage
                progress = self._calculate_progress(
                    goal.baseline_value,
                    new_current,
                    goal.target_value,
                    goal.target_type
                )
                goal.progress_percentage = progress
                goal.last_calculated_at = datetime.utcnow()
                
                updated_count += 1
            
            self.db.commit()
            
            logger.info(f"Updated {updated_count} goals for user {user_id}")
            
            return {
                "success": True,
                "goals_updated": updated_count
            }
            
        except Exception as e:
            logger.error(f"Error updating goal progress for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _calculate_progress(
        self, 
        baseline: str, 
        current: str, 
        target: str, 
        target_type: str
    ) -> float:
        """Calculate progress percentage based on goal type"""
        try:
            if target_type == 'paused':
                return 0.0
            
            # Extract numeric values
            baseline_num = float(baseline.replace('#', '').replace(',', '').replace('+', ''))
            current_num = float(current.replace('#', '').replace(',', '').replace('+', ''))
            
            if target_type == 'growth':
                target_num = float(target.replace('+', '').replace(',', ''))
                actual_change = current_num - baseline_num
                progress = (actual_change / target_num * 100) if target_num > 0 else 0
                return min(max(progress, 0.0), 100.0)
            
            elif target_type == 'range':
                # For avg position reduction
                target_range = target.replace('−', '-').split(' to ')
                if len(target_range) == 2:
                    target_min = abs(float(target_range[0].strip()))
                    actual_change = baseline_num - current_num
                    progress = (actual_change / target_min * 100) if target_min > 0 else 0
                    return min(max(progress, 0.0), 100.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating progress: {str(e)}")
            return 0.0
    
    def _goal_to_dict(self, goal: StrategyGoal) -> Dict[str, Any]:
        """Convert goal model to dictionary"""
        return {
            "id": goal.id,
            "goal_type": goal.goal_type,
            "goal_category": goal.goal_category,
            "cycle_start_date": goal.cycle_start_date.isoformat(),
            "cycle_end_date": goal.cycle_end_date.isoformat(),
            "is_locked": goal.is_locked,
            "baseline_value": goal.baseline_value,
            "current_value": goal.current_value,
            "target_value": goal.target_value,
            "unit": goal.unit,
            "target_type": goal.target_type,
            "slab_data": goal.slab_data,
            "progress_percentage": goal.progress_percentage,
            "last_calculated_at": goal.last_calculated_at.isoformat() if goal.last_calculated_at else None,
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
        }
