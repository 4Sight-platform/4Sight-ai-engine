"""
Goals Governance Service
Provides governance-level metrics for strategy goals progress tracking
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from Database.models import StrategyGoal

logger = logging.getLogger(__name__)


class GovernanceGoalsService:
    """Service for goals governance metrics and progress tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_performance(self, user_id: str) -> Dict[str, Any]:
        """
        Get overall goals performance metrics for governance dashboard
        
        Returns:
            - avg_progress_percentage: Average progress across all active goals
            - goals_on_track: Count of goals with progress >= 70%
            - total_goals: Total active goals count
            - delta: Change from baseline (computed as avg_progress change)
            - has_baseline: Whether baseline data exists
        """
        try:
            # Get all active goals for this user
            active_goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).all()
            
            if not active_goals:
                return {
                    "avg_progress_percentage": 0.0,
                    "goals_on_track": 0,
                    "total_goals": 0,
                    "goals_completed": 0,
                    "delta": 0.0,
                    "has_baseline": False
                }
            
            total_goals = len(active_goals)
            
            # Calculate aggregate metrics
            total_progress = 0.0
            goals_on_track = 0  # Goals with progress >= 70%
            goals_completed = 0  # Goals with progress >= 100%
            
            for goal in active_goals:
                progress = goal.progress_percentage or 0.0
                total_progress += progress
                
                if progress >= 100:
                    goals_completed += 1
                    goals_on_track += 1
                elif progress >= 70:
                    goals_on_track += 1
            
            avg_progress = total_progress / total_goals if total_goals > 0 else 0.0
            
            # Calculate delta from baseline
            # For now, delta is 0 since we don't have historical snapshots yet
            # TODO: Implement goals progress snapshots similar to action plan
            delta = 0.0
            has_baseline = False
            
            return {
                "avg_progress_percentage": round(avg_progress, 1),
                "goals_on_track": goals_on_track,
                "total_goals": total_goals,
                "goals_completed": goals_completed,
                "delta": delta,
                "has_baseline": has_baseline
            }
            
        except Exception as e:
            logger.error(f"Error getting goals performance for {user_id}: {str(e)}")
            raise
    
    def get_goals_breakdown(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get breakdown of each goal's progress
        
        Returns list of goals with their individual progress metrics
        """
        try:
            active_goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).order_by(
                StrategyGoal.goal_category.asc(),
                StrategyGoal.created_at.asc()
            ).all()
            
            goals_breakdown = []
            for goal in active_goals:
                progress = goal.progress_percentage or 0.0
                
                # Determine status based on progress
                if progress >= 100:
                    status = "completed"
                elif progress >= 70:
                    status = "on_track"
                elif progress >= 30:
                    status = "in_progress"
                else:
                    status = "at_risk"
                
                goals_breakdown.append({
                    "goal_type": goal.goal_type,
                    "goal_category": goal.goal_category,
                    "baseline_value": goal.baseline_value,
                    "current_value": goal.current_value,
                    "target_value": goal.target_value,
                    "unit": goal.unit,
                    "progress_percentage": round(progress, 1),
                    "status": status,
                    "cycle_end_date": goal.cycle_end_date.isoformat() if goal.cycle_end_date else None
                })
            
            return goals_breakdown
            
        except Exception as e:
            logger.error(f"Error getting goals breakdown for {user_id}: {str(e)}")
            raise
    
    def get_cycle_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current goal cycle information
        
        Returns cycle start/end dates and days remaining
        """
        try:
            active_goal = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).first()
            
            if not active_goal:
                return None
            
            today = date.today()
            days_remaining = (active_goal.cycle_end_date - today).days
            days_elapsed = (today - active_goal.cycle_start_date).days
            total_days = (active_goal.cycle_end_date - active_goal.cycle_start_date).days
            
            return {
                "cycle_start_date": active_goal.cycle_start_date.isoformat(),
                "cycle_end_date": active_goal.cycle_end_date.isoformat(),
                "days_remaining": max(0, days_remaining),
                "days_elapsed": days_elapsed,
                "total_days": total_days,
                "progress_percentage": round((days_elapsed / total_days * 100) if total_days > 0 else 0, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting cycle info for {user_id}: {str(e)}")
            raise
