"""
Goals Governance Service
Provides governance-level metrics for strategy goals progress tracking
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from Database.models import (
    StrategyGoal, GoalMilestone, GoalProgressSnapshot,
    KeywordPositionSnapshot
)

logger = logging.getLogger(__name__)


# Goal type to UI mapping
GOAL_TYPE_TO_UI = {
    'organic-traffic': {
        'title': 'Increase Organic Traffic',
        'icon': 'ri-user-line',
        'color': 'from-green-500 to-emerald-600',
    },
    'keyword-rankings': {
        'title': 'Improve Keyword Rankings',
        'icon': 'ri-trophy-line',
        'color': 'from-green-500 to-emerald-600',
    },
    'serp-features': {
        'title': 'Capture Visibility Features',
        'icon': 'ri-star-line',
        'color': 'from-gray-400 to-gray-500',
    },
    'avg-position': {
        'title': 'Reduce Average Position',
        'icon': 'ri-arrow-down-line',
        'color': 'from-orange-500 to-red-600',
    },
    'impressions': {
        'title': 'Increase Impressions',
        'icon': 'ri-eye-line',
        'color': 'from-purple-500 to-violet-600',
    },
    'domain-authority': {
        'title': 'Improve Domain Authority',
        'icon': 'ri-shield-check-line',
        'color': 'from-orange-500 to-red-600',
    }
}


class GovernanceGoalsService:
    """Service for goals governance metrics and progress tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_performance(self, user_id: str) -> Dict[str, Any]:
        """
        Get overall goals performance metrics for governance dashboard
        
        Returns:
            - avg_progress_percentage: Average progress across all active goals
            - goals_on_track: Count of goals with status 'on_track'
            - total_goals: Total active goals count
            - goals_completed: Count of goals with status 'completed'
            - goals_paused: Count of goals with status 'paused'
            - goals_at_risk: Count of goals with status 'at_risk'
            - goals_in_progress: Count of non-completed/non-paused goals
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
                    "total_goals": 0,
                    "goals_completed": 0,
                    "goals_on_track": 0,
                    "goals_in_progress": 0,
                    "goals_paused": 0,
                    "goals_at_risk": 0,
                    "has_baseline": False
                }
            
            total_goals = len(active_goals)
            
            # Count by status
            goals_completed = 0
            goals_on_track = 0
            goals_in_progress = 0
            goals_paused = 0
            goals_at_risk = 0
            total_progress = 0.0
            
            for goal in active_goals:
                progress = goal.progress_percentage or 0.0
                status = goal.status or 'on_track'
                
                # Don't count paused goals in progress calculation
                if status != 'paused':
                    total_progress += progress
                
                if status == 'completed' or progress >= 100:
                    goals_completed += 1
                elif status == 'paused':
                    goals_paused += 1
                elif status == 'at_risk' or progress < 30:
                    goals_at_risk += 1
                elif status == 'on_track' or progress >= 70:
                    goals_on_track += 1
                else:
                    goals_in_progress += 1
            
            # Calculate average (excluding paused goals)
            non_paused_count = total_goals - goals_paused
            avg_progress = total_progress / non_paused_count if non_paused_count > 0 else 0.0
            
            return {
                "avg_progress_percentage": round(avg_progress, 1),
                "total_goals": total_goals,
                "goals_completed": goals_completed,
                "goals_on_track": goals_on_track,
                "goals_in_progress": goals_in_progress,
                "goals_paused": goals_paused,
                "goals_at_risk": goals_at_risk,
                "has_baseline": True
            }
            
        except Exception as e:
            logger.error(f"Error getting goals performance for {user_id}: {str(e)}")
            raise
    
    def get_goals_breakdown(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get breakdown of each goal's progress with milestones and trend data
        
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
                status = goal.status or self._determine_status(progress, goal.goal_type)
                
                # Get UI metadata
                ui_config = GOAL_TYPE_TO_UI.get(goal.goal_type, {})
                
                # Get milestones for this goal
                milestones = self._get_goal_milestones(goal.id)
                
                # Calculate trend from snapshots
                trend = self._calculate_trend(goal.id, goal.goal_type)
                
                # Calculate days remaining
                today = date.today()
                days_remaining = max(0, (goal.cycle_end_date - today).days)
                
                # Get slab distribution for keyword-rankings
                slab_data = None
                if goal.goal_type == 'keyword-rankings':
                    slab_data = self._get_keyword_slab_distribution(user_id) or goal.slab_data
                
                goals_breakdown.append({
                    "id": goal.id,
                    "goal_type": goal.goal_type,
                    "goal_category": goal.goal_category,
                    "title": ui_config.get('title', goal.goal_type),
                    "icon": ui_config.get('icon', 'ri-flag-line'),
                    "color": ui_config.get('color', 'from-gray-500 to-gray-600'),
                    "baseline_value": goal.baseline_value,
                    "current_value": goal.current_value,
                    "target_value": goal.target_value,
                    "unit": goal.unit,
                    "target_type": goal.target_type,
                    "progress_percentage": round(progress, 1),
                    "status": status,
                    "days_remaining": days_remaining,
                    "cycle_start_date": goal.cycle_start_date.isoformat() if goal.cycle_start_date else None,
                    "cycle_end_date": goal.cycle_end_date.isoformat() if goal.cycle_end_date else None,
                    "milestones": milestones,
                    "trend": trend,
                    "slab_data": slab_data
                })
            
            return goals_breakdown
            
        except Exception as e:
            logger.error(f"Error getting goals breakdown for {user_id}: {str(e)}")
            raise
    
    def _determine_status(self, progress: float, goal_type: str) -> str:
        """Determine goal status based on progress and type"""
        if goal_type == 'serp-features':
            return 'paused'
        if progress >= 100:
            return 'completed'
        elif progress >= 70:
            return 'on_track'
        elif progress >= 30:
            return 'on_track'  # in_progress treated as on_track
        else:
            return 'at_risk'
    
    def _get_goal_milestones(self, goal_id: int) -> List[Dict[str, Any]]:
        """Get milestones for a specific goal"""
        try:
            milestones = self.db.query(GoalMilestone).filter(
                GoalMilestone.goal_id == goal_id
            ).order_by(GoalMilestone.month_number.asc()).all()
            
            result = []
            for ms in milestones:
                result.append({
                    "month": f"Month {ms.month_number}",
                    "target": ms.target_value,
                    "actual": ms.actual_value,
                    "achieved": ms.achieved,
                    "recorded_at": ms.recorded_at.isoformat() if ms.recorded_at else None
                })
            
            # If no milestones exist, return placeholder structure
            if not result:
                return [
                    {"month": "Month 1", "target": None, "actual": None, "achieved": False, "recorded_at": None},
                    {"month": "Month 2", "target": None, "actual": None, "achieved": False, "recorded_at": None},
                    {"month": "Month 3", "target": None, "actual": None, "achieved": False, "recorded_at": None}
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting milestones for goal {goal_id}: {str(e)}")
            return []
    
    def _calculate_trend(self, goal_id: int, goal_type: str) -> Dict[str, Any]:
        """Calculate trend from recent snapshots"""
        try:
            # Get the two most recent snapshots
            snapshots = self.db.query(GoalProgressSnapshot).filter(
                GoalProgressSnapshot.goal_id == goal_id
            ).order_by(
                GoalProgressSnapshot.snapshot_date.desc()
            ).limit(2).all()
            
            if len(snapshots) < 2:
                # No trend data available, calculate from baseline vs current
                goal = self.db.query(StrategyGoal).filter(StrategyGoal.id == goal_id).first()
                if goal and goal.baseline_value and goal.current_value:
                    try:
                        # Extract numeric values
                        baseline = self._extract_numeric(goal.baseline_value)
                        current = self._extract_numeric(goal.current_value)
                        change = current - baseline
                        
                        return {
                            "value": change,
                            "direction": "up" if change > 0 else ("down" if change < 0 else "neutral"),
                            "formatted": self._format_trend(change, goal_type)
                        }
                    except:
                        pass
                
                return {"value": 0, "direction": "neutral", "formatted": "No data"}
            
            # Calculate change between snapshots
            latest = self._extract_numeric(snapshots[0].current_value)
            previous = self._extract_numeric(snapshots[1].current_value)
            change = latest - previous
            
            return {
                "value": change,
                "direction": "up" if change > 0 else ("down" if change < 0 else "neutral"),
                "formatted": self._format_trend(change, goal_type)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend for goal {goal_id}: {str(e)}")
            return {"value": 0, "direction": "neutral", "formatted": "Error"}
    
    def _extract_numeric(self, value: str) -> float:
        """Extract numeric value from string"""
        if not value:
            return 0.0
        # Remove common prefixes/suffixes
        clean = value.replace('#', '').replace('+', '').replace(',', '').replace('%', '').strip()
        try:
            return float(clean)
        except:
            return 0.0
    
    def _format_trend(self, change: float, goal_type: str) -> str:
        """Format trend value for display"""
        if change == 0:
            return "No change"
        
        sign = "+" if change > 0 else ""
        
        if goal_type == 'avg-position':
            # For position, negative is good
            return f"{change:+.1f} positions"
        elif goal_type in ['organic-traffic', 'impressions']:
            return f"{sign}{int(change):,}"
        elif goal_type == 'domain-authority':
            return f"{sign}{int(change)} points"
        else:
            return f"{sign}{change:.1f}"
    
    def _get_keyword_slab_distribution(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Calculate keyword ranking slab distribution from real data"""
        try:
            # Get the most recent snapshot date
            latest_date = self.db.query(func.max(KeywordPositionSnapshot.snapshot_date)).filter(
                KeywordPositionSnapshot.user_id == user_id,
                KeywordPositionSnapshot.period_type == 'current'
            ).scalar()
            
            if not latest_date:
                return None
            
            # Get all keyword positions for that date
            positions = self.db.query(KeywordPositionSnapshot.position).filter(
                KeywordPositionSnapshot.user_id == user_id,
                KeywordPositionSnapshot.snapshot_date == latest_date,
                KeywordPositionSnapshot.period_type == 'current',
                KeywordPositionSnapshot.position.isnot(None)
            ).all()
            
            if not positions:
                return None
            
            total = len(positions)
            
            # Count by position range
            top3 = sum(1 for p in positions if p.position and 1 <= p.position <= 3)
            top10 = sum(1 for p in positions if p.position and 4 <= p.position <= 10)
            top20 = sum(1 for p in positions if p.position and 11 <= p.position <= 20)
            top100 = sum(1 for p in positions if p.position and 21 <= p.position <= 100)
            
            return [
                {
                    "label": "#1-3",
                    "percentage": round((top3 / total) * 100, 1) if total > 0 else 0,
                    "count": top3,
                    "color": "bg-green-600"
                },
                {
                    "label": "#4-10",
                    "percentage": round((top10 / total) * 100, 1) if total > 0 else 0,
                    "count": top10,
                    "color": "bg-green-400"
                },
                {
                    "label": "#11-20",
                    "percentage": round((top20 / total) * 100, 1) if total > 0 else 0,
                    "count": top20,
                    "color": "bg-green-300"
                },
                {
                    "label": "#21-100",
                    "percentage": round((top100 / total) * 100, 1) if total > 0 else 0,
                    "count": top100,
                    "color": "bg-green-200"
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting keyword slab distribution for {user_id}: {str(e)}")
            return None
    
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
            days_remaining = max(0, (active_goal.cycle_end_date - today).days)
            days_elapsed = (today - active_goal.cycle_start_date).days
            total_days = (active_goal.cycle_end_date - active_goal.cycle_start_date).days
            
            return {
                "cycle_start_date": active_goal.cycle_start_date.isoformat(),
                "cycle_end_date": active_goal.cycle_end_date.isoformat(),
                "days_remaining": days_remaining,
                "days_elapsed": days_elapsed,
                "total_days": total_days,
                "progress_percentage": round((days_elapsed / total_days * 100) if total_days > 0 else 0, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting cycle info for {user_id}: {str(e)}")
            raise
    
    def capture_snapshot(self, user_id: str) -> Dict[str, Any]:
        """
        Capture daily snapshot of all goals for trend tracking
        """
        try:
            active_goals = self.db.query(StrategyGoal).filter(
                StrategyGoal.user_id == user_id,
                StrategyGoal.is_locked == True
            ).all()
            
            if not active_goals:
                return {"success": False, "message": "No active goals found"}
            
            today = date.today()
            snapshots_created = 0
            
            for goal in active_goals:
                # Check if snapshot already exists for today
                existing = self.db.query(GoalProgressSnapshot).filter(
                    GoalProgressSnapshot.goal_id == goal.id,
                    GoalProgressSnapshot.snapshot_date == today
                ).first()
                
                if existing:
                    # Update existing snapshot
                    existing.current_value = goal.current_value
                    existing.progress_percentage = goal.progress_percentage
                else:
                    # Create new snapshot
                    snapshot = GoalProgressSnapshot(
                        goal_id=goal.id,
                        snapshot_date=today,
                        current_value=goal.current_value or "0",
                        progress_percentage=goal.progress_percentage
                    )
                    self.db.add(snapshot)
                    snapshots_created += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Created {snapshots_created} snapshots",
                "date": today.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error capturing snapshots for {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def initialize_milestones(self, goal_id: int, baseline_value: str, target_value: str, goal_type: str) -> bool:
        """
        Initialize 3 monthly milestones for a goal
        Divides the target into 3 monthly chunks
        """
        try:
            # Check if milestones already exist
            existing = self.db.query(GoalMilestone).filter(
                GoalMilestone.goal_id == goal_id
            ).first()
            
            if existing:
                logger.info(f"Milestones already exist for goal {goal_id}")
                return True
            
            # Calculate milestone targets
            baseline_num = self._extract_numeric(baseline_value)
            target_num = self._extract_numeric(target_value)
            
            # For growth targets like "+500", add to baseline
            if target_value.startswith('+'):
                target_num = baseline_num + target_num
            elif target_value.startswith('-'):
                target_num = baseline_num + target_num  # target_num is already negative
            
            # Calculate incremental targets
            increment = (target_num - baseline_num) / 3
            
            for month in range(1, 4):
                milestone_target = baseline_num + (increment * month)
                
                # Format based on goal type
                if goal_type in ['organic-traffic', 'impressions']:
                    formatted_target = str(int(milestone_target))
                elif goal_type == 'avg-position':
                    formatted_target = f"#{milestone_target:.1f}"
                elif goal_type == 'domain-authority':
                    formatted_target = str(int(milestone_target))
                else:
                    formatted_target = str(milestone_target)
                
                milestone = GoalMilestone(
                    goal_id=goal_id,
                    month_number=month,
                    target_value=formatted_target,
                    actual_value=None,
                    achieved=False
                )
                self.db.add(milestone)
            
            self.db.commit()
            logger.info(f"Created 3 milestones for goal {goal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing milestones for goal {goal_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def update_milestone(self, goal_id: int, month_number: int, actual_value: str, achieved: bool) -> bool:
        """Update a specific milestone with actual value"""
        try:
            milestone = self.db.query(GoalMilestone).filter(
                GoalMilestone.goal_id == goal_id,
                GoalMilestone.month_number == month_number
            ).first()
            
            if not milestone:
                logger.warning(f"Milestone not found for goal {goal_id}, month {month_number}")
                return False
            
            milestone.actual_value = actual_value
            milestone.achieved = achieved
            milestone.recorded_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating milestone: {str(e)}")
            self.db.rollback()
            return False
