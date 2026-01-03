"""
Action Plan Governance Service
Provides governance-level metrics for action plan progress tracking
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from Database.models import (
    ActionPlanTask,
    ActionPlanProgressSnapshot,
    StrategyGoal
)

logger = logging.getLogger(__name__)


class ActionPlanGovernanceService:
    """Service for action plan governance metrics and progress tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_performance(self, user_id: str) -> Dict[str, Any]:
        """
        Get overall action plan performance metrics
        
        Returns:
            - completion_percentage: Overall completion %
            - completed_tasks / total_tasks
            - delta from baseline
        """
        try:
            # Get current task counts
            current = self._calculate_current_metrics(user_id)
            
            # Get baseline for comparison
            baseline = self._get_baseline(user_id)
            
            # Calculate delta
            delta = 0.0
            if baseline:
                delta = current['completion_percentage'] - baseline.completion_percentage
            
            return {
                "completion_percentage": current['completion_percentage'],
                "completed_tasks": current['completed_tasks'],
                "in_progress_tasks": current['in_progress_tasks'],
                "total_tasks": current['total_tasks'],
                "baseline_percentage": baseline.completion_percentage if baseline else 0.0,
                "delta": delta,
                "has_baseline": baseline is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting action plan performance for {user_id}: {str(e)}")
            raise
    
    def get_categories(self, user_id: str) -> Dict[str, Any]:
        """
        Get action plan progress by category (onpage, offpage, technical)
        
        Returns category breakdown with completion % for each
        """
        try:
            categories = {}
            
            for category in ['onpage', 'offpage', 'technical']:
                # Count total tasks in category
                total = self.db.query(func.count(ActionPlanTask.id)).filter(
                    ActionPlanTask.user_id == user_id,
                    ActionPlanTask.category == category
                ).scalar() or 0
                
                # Count completed tasks in category
                completed = self.db.query(func.count(ActionPlanTask.id)).filter(
                    ActionPlanTask.user_id == user_id,
                    ActionPlanTask.category == category,
                    ActionPlanTask.status == 'completed'
                ).scalar() or 0
                
                # Count in progress tasks
                in_progress = self.db.query(func.count(ActionPlanTask.id)).filter(
                    ActionPlanTask.user_id == user_id,
                    ActionPlanTask.category == category,
                    ActionPlanTask.status == 'in_progress'
                ).scalar() or 0
                
                # Calculate percentage
                percentage = (completed / total * 100) if total > 0 else 0.0
                
                categories[category] = {
                    "total": total,
                    "completed": completed,
                    "in_progress": in_progress,
                    "not_started": total - completed - in_progress,
                    "completion_percentage": round(percentage, 1)
                }
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting action plan categories for {user_id}: {str(e)}")
            raise
    
    def get_timeline(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get action plan progress timeline (historical snapshots)
        
        Returns list of progress snapshots ordered by date
        """
        try:
            snapshots = self.db.query(ActionPlanProgressSnapshot).filter(
                ActionPlanProgressSnapshot.user_id == user_id
            ).order_by(
                ActionPlanProgressSnapshot.snapshot_date.desc()
            ).limit(limit).all()
            
            result = []
            for i, snapshot in enumerate(snapshots):
                # Calculate delta from previous snapshot
                delta = 0.0
                if i < len(snapshots) - 1:
                    prev = snapshots[i + 1]
                    delta = snapshot.completion_percentage - prev.completion_percentage
                
                result.append({
                    "id": snapshot.id,
                    "snapshot_date": snapshot.snapshot_date.isoformat(),
                    "completion_percentage": snapshot.completion_percentage,
                    "completed_tasks": snapshot.completed_tasks,
                    "total_tasks": snapshot.total_tasks,
                    "delta": round(delta, 1),
                    "is_baseline": snapshot.is_baseline,
                    "categories": {
                        "onpage": {
                            "percentage": snapshot.onpage_percentage,
                            "completed": snapshot.onpage_completed,
                            "total": snapshot.onpage_total
                        },
                        "offpage": {
                            "percentage": snapshot.offpage_percentage,
                            "completed": snapshot.offpage_completed,
                            "total": snapshot.offpage_total
                        },
                        "technical": {
                            "percentage": snapshot.technical_percentage,
                            "completed": snapshot.technical_completed,
                            "total": snapshot.technical_total
                        }
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting action plan timeline for {user_id}: {str(e)}")
            raise
    
    def capture_baseline(self, user_id: str, cycle_start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Capture baseline snapshot at the start of a 90-day cycle
        
        Args:
            user_id: User ID
            cycle_start_date: Start date of the cycle (defaults to today)
        """
        try:
            if cycle_start_date is None:
                # Get from strategy_goals or use today
                active_goal = self.db.query(StrategyGoal).filter(
                    StrategyGoal.user_id == user_id,
                    StrategyGoal.is_locked == True
                ).first()
                
                if active_goal:
                    cycle_start_date = active_goal.cycle_start_date
                else:
                    cycle_start_date = date.today()
            
            # Calculate current metrics
            current = self._calculate_current_metrics(user_id)
            categories = self.get_categories(user_id)
            
            # Create baseline snapshot
            snapshot = ActionPlanProgressSnapshot(
                user_id=user_id,
                snapshot_date=date.today(),
                cycle_start_date=cycle_start_date,
                total_tasks=current['total_tasks'],
                completed_tasks=current['completed_tasks'],
                in_progress_tasks=current['in_progress_tasks'],
                completion_percentage=current['completion_percentage'],
                onpage_total=categories['onpage']['total'],
                onpage_completed=categories['onpage']['completed'],
                onpage_percentage=categories['onpage']['completion_percentage'],
                offpage_total=categories['offpage']['total'],
                offpage_completed=categories['offpage']['completed'],
                offpage_percentage=categories['offpage']['completion_percentage'],
                technical_total=categories['technical']['total'],
                technical_completed=categories['technical']['completed'],
                technical_percentage=categories['technical']['completion_percentage'],
                is_baseline=True
            )
            
            self.db.add(snapshot)
            self.db.commit()
            
            logger.info(f"Captured action plan baseline for user {user_id}: {current['completion_percentage']}%")
            
            return {
                "success": True,
                "message": "Baseline captured successfully",
                "baseline": {
                    "completion_percentage": current['completion_percentage'],
                    "completed_tasks": current['completed_tasks'],
                    "total_tasks": current['total_tasks'],
                    "cycle_start_date": cycle_start_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error capturing action plan baseline for {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def capture_daily_snapshot(self, user_id: str) -> Dict[str, Any]:
        """
        Capture daily progress snapshot for timeline tracking
        Called by scheduler or manually
        """
        try:
            today = date.today()
            
            # Check if snapshot already exists for today
            existing = self.db.query(ActionPlanProgressSnapshot).filter(
                ActionPlanProgressSnapshot.user_id == user_id,
                ActionPlanProgressSnapshot.snapshot_date == today
            ).first()
            
            if existing:
                # Update existing snapshot
                current = self._calculate_current_metrics(user_id)
                categories = self.get_categories(user_id)
                
                existing.total_tasks = current['total_tasks']
                existing.completed_tasks = current['completed_tasks']
                existing.in_progress_tasks = current['in_progress_tasks']
                existing.completion_percentage = current['completion_percentage']
                existing.onpage_total = categories['onpage']['total']
                existing.onpage_completed = categories['onpage']['completed']
                existing.onpage_percentage = categories['onpage']['completion_percentage']
                existing.offpage_total = categories['offpage']['total']
                existing.offpage_completed = categories['offpage']['completed']
                existing.offpage_percentage = categories['offpage']['completion_percentage']
                existing.technical_total = categories['technical']['total']
                existing.technical_completed = categories['technical']['completed']
                existing.technical_percentage = categories['technical']['completion_percentage']
                
                self.db.commit()
                return {"success": True, "message": "Snapshot updated", "snapshot_date": today.isoformat()}
            
            # Get cycle start date
            baseline = self._get_baseline(user_id)
            cycle_start_date = baseline.cycle_start_date if baseline else today
            
            # Calculate current metrics
            current = self._calculate_current_metrics(user_id)
            categories = self.get_categories(user_id)
            
            # Create new snapshot
            snapshot = ActionPlanProgressSnapshot(
                user_id=user_id,
                snapshot_date=today,
                cycle_start_date=cycle_start_date,
                total_tasks=current['total_tasks'],
                completed_tasks=current['completed_tasks'],
                in_progress_tasks=current['in_progress_tasks'],
                completion_percentage=current['completion_percentage'],
                onpage_total=categories['onpage']['total'],
                onpage_completed=categories['onpage']['completed'],
                onpage_percentage=categories['onpage']['completion_percentage'],
                offpage_total=categories['offpage']['total'],
                offpage_completed=categories['offpage']['completed'],
                offpage_percentage=categories['offpage']['completion_percentage'],
                technical_total=categories['technical']['total'],
                technical_completed=categories['technical']['completed'],
                technical_percentage=categories['technical']['completion_percentage'],
                is_baseline=False
            )
            
            self.db.add(snapshot)
            self.db.commit()
            
            return {"success": True, "message": "Snapshot captured", "snapshot_date": today.isoformat()}
            
        except Exception as e:
            logger.error(f"Error capturing daily snapshot for {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def get_parameter_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get action plan progress by parameter_group (e.g., SERP Snippet, Accessibility, etc.)
        
        Returns list of parameter groups with completion % for each
        """
        try:
            # Query to get parameter groups with counts
            from sqlalchemy import case
            
            results = self.db.query(
                ActionPlanTask.parameter_group,
                func.count(ActionPlanTask.id).label('total'),
                func.sum(case((ActionPlanTask.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((ActionPlanTask.status == 'in_progress', 1), else_=0)).label('in_progress')
            ).filter(
                ActionPlanTask.user_id == user_id
            ).group_by(
                ActionPlanTask.parameter_group
            ).all()
            
            parameter_groups = []
            for row in results:
                total = row.total or 0
                completed = row.completed or 0
                in_progress = row.in_progress or 0
                not_started = total - completed - in_progress
                
                completion_percentage = (completed / total * 100) if total > 0 else 0.0
                
                parameter_groups.append({
                    "parameter_group": row.parameter_group,
                    "total": total,
                    "completed": completed,
                    "in_progress": in_progress,
                    "not_started": not_started,
                    "completion_percentage": round(completion_percentage, 1)
                })
            
            # Sort by completion percentage descending
            parameter_groups.sort(key=lambda x: x['completion_percentage'], reverse=True)
            
            return parameter_groups
            
        except Exception as e:
            logger.error(f"Error getting parameter groups for {user_id}: {str(e)}")
            raise
    
    def get_recent_activity(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent task activity from action_plan_task_history
        
        Returns list of recent task updates with status, priority, and completion date
        """
        try:
            from Database.models import ActionPlanTaskHistory
            
            # Get recent task updates from history
            history_records = self.db.query(
                ActionPlanTaskHistory,
                ActionPlanTask
            ).join(
                ActionPlanTask,
                ActionPlanTaskHistory.task_id == ActionPlanTask.id
            ).filter(
                ActionPlanTask.user_id == user_id
            ).order_by(
                ActionPlanTaskHistory.changed_at.desc()
            ).limit(limit).all()
            
            activity = []
            for history, task in history_records:
                activity.append({
                    "task_id": task.id,
                    "task_title": task.task_title,
                    "old_status": history.old_status,
                    "new_status": history.new_status,
                    "priority": task.priority,
                    "changed_at": history.changed_at.isoformat() if history.changed_at else None,
                    "notes": history.notes,
                    "category": task.category,
                    "parameter_group": task.parameter_group
                })
            
            return activity
            
        except Exception as e:
            logger.error(f"Error getting recent activity for {user_id}: {str(e)}")
            raise
    
    def get_detailed_overview(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive overview for Action Plan governance dashboard
        
        Returns:
            - Overall metrics
            - Parameter group breakdown
            - Recent activity
        """
        try:
            # Get current metrics
            current = self._calculate_current_metrics(user_id)
            
            # Get parameter groups breakdown
            parameter_groups = self.get_parameter_groups(user_id)
            
            # Get recent activity
            recent_activity = self.get_recent_activity(user_id, limit=10)
            
            return {
                "overview": {
                    "total_tasks": current['total_tasks'],
                    "completed": current['completed_tasks'],
                    "in_progress": current['in_progress_tasks'],
                    "pending": current['not_started_tasks'],
                    "completion_rate": current['completion_percentage']
                },
                "parameter_groups": parameter_groups,
                "recent_activity": recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed overview for {user_id}: {str(e)}")
            raise
    
    def get_category_overview(self, user_id: str, category: str) -> Dict[str, Any]:
        """
        Get overview filtered by specific category (onpage, offpage, technical)
        
        Returns:
            - Category-specific metrics
            - Parameter groups for this category
            - Recent activity for this category
        """
        try:
            from sqlalchemy import case
            
            # Calculate metrics for specific category
            total = self.db.query(func.count(ActionPlanTask.id)).filter(
                ActionPlanTask.user_id == user_id,
                ActionPlanTask.category == category
            ).scalar() or 0
            
            completed = self.db.query(func.count(ActionPlanTask.id)).filter(
                ActionPlanTask.user_id == user_id,
                ActionPlanTask.category == category,
                ActionPlanTask.status == 'completed'
            ).scalar() or 0
            
            in_progress = self.db.query(func.count(ActionPlanTask.id)).filter(
                ActionPlanTask.user_id == user_id,
                ActionPlanTask.category == category,
                ActionPlanTask.status == 'in_progress'
            ).scalar() or 0
            
            not_started = total - completed - in_progress
            completion_rate = (completed / total * 100) if total > 0 else 0.0
            
            # Get parameter groups for this category
            results = self.db.query(
                ActionPlanTask.parameter_group,
                func.count(ActionPlanTask.id).label('total'),
                func.sum(case((ActionPlanTask.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((ActionPlanTask.status == 'in_progress', 1), else_=0)).label('in_progress')
            ).filter(
                ActionPlanTask.user_id == user_id,
                ActionPlanTask.category == category
            ).group_by(
                ActionPlanTask.parameter_group
            ).all()
            
            parameter_groups = []
            for row in results:
                grp_total = row.total or 0
                grp_completed = row.completed or 0
                grp_in_progress = row.in_progress or 0
                grp_not_started = grp_total - grp_completed - grp_in_progress
                grp_percentage = (grp_completed / grp_total * 100) if grp_total > 0 else 0.0
                
                parameter_groups.append({
                    "parameter_group": row.parameter_group,
                    "total": grp_total,
                    "completed": grp_completed,
                    "in_progress": grp_in_progress,
                    "not_started": grp_not_started,
                    "completion_percentage": round(grp_percentage, 1)
                })
            
            parameter_groups.sort(key=lambda x: x['completion_percentage'], reverse=True)
            
            # Get recent activity for this category
            from Database.models import ActionPlanTaskHistory
            
            history_records = self.db.query(
                ActionPlanTaskHistory,
                ActionPlanTask
            ).join(
                ActionPlanTask,
                ActionPlanTaskHistory.task_id == ActionPlanTask.id
            ).filter(
                ActionPlanTask.user_id == user_id,
                ActionPlanTask.category == category
            ).order_by(
                ActionPlanTaskHistory.changed_at.desc()
            ).limit(5).all()
            
            recent_activity = []
            for history, task in history_records:
                recent_activity.append({
                    "task_id": task.id,
                    "task_title": task.task_title,
                    "old_status": history.old_status,
                    "new_status": history.new_status,
                    "priority": task.priority,
                    "changed_at": history.changed_at.isoformat() if history.changed_at else None,
                    "category": task.category,
                    "parameter_group": task.parameter_group
                })
            
            return {
                "category": category,
                "overview": {
                    "total_tasks": total,
                    "completed": completed,
                    "in_progress": in_progress,
                    "pending": not_started,
                    "completion_rate": round(completion_rate, 1)
                },
                "parameter_groups": parameter_groups,
                "recent_activity": recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting category overview for {user_id}/{category}: {str(e)}")
            raise
    
    def _calculate_current_metrics(self, user_id: str) -> Dict[str, Any]:


        """Calculate current task metrics from action_plan_tasks"""
        total_tasks = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id
        ).scalar() or 0
        
        completed_tasks = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id,
            ActionPlanTask.status == 'completed'
        ).scalar() or 0
        
        in_progress_tasks = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id,
            ActionPlanTask.status == 'in_progress'
        ).scalar() or 0
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "not_started_tasks": total_tasks - completed_tasks - in_progress_tasks,
            "completion_percentage": round(completion_percentage, 1)
        }
    
    def _get_baseline(self, user_id: str) -> Optional[ActionPlanProgressSnapshot]:
        """Get the baseline snapshot for the current cycle"""
        return self.db.query(ActionPlanProgressSnapshot).filter(
            ActionPlanProgressSnapshot.user_id == user_id,
            ActionPlanProgressSnapshot.is_baseline == True
        ).order_by(
            ActionPlanProgressSnapshot.snapshot_date.desc()
        ).first()
