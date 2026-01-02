"""
Action Plan Service
Generates SEO action plan tasks based on As-Is State scores
"""

import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from Database.models import (
    ActionPlanTask, ActionPlanTaskPage, ActionPlanTaskHistory,
    SeoGoal, AsIsScore
)

logger = logging.getLogger(__name__)


class ActionPlanService:
    """Service for generating and managing action plan tasks from As-Is scores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_action_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Generate complete action plan from As-Is scores
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with generated tasks count by category
        """
        try:
            # Delete existing tasks for fresh generation
            self.db.query(ActionPlanTask).filter(
                ActionPlanTask.user_id == user_id
            ).delete()
            self.db.commit()
            
            # Get user's SEO goals for alignment
            goals = self._get_user_goals(user_id)
            
            # Generate tasks from as_is_scores with critical/needs_attention status
            onpage_count = self._generate_tasks_from_scores(user_id, "onpage", goals)
            offpage_count = self._generate_tasks_from_scores(user_id, "offpage", goals)
            technical_count = self._generate_tasks_from_scores(user_id, "technical", goals)
            
            self.db.commit()
            
            return {
                "success": True,
                "tasks_generated": {
                    "onpage": onpage_count,
                    "offpage": offpage_count,
                    "technical": technical_count,
                    "total": onpage_count + offpage_count + technical_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating action plan for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _get_user_goals(self, user_id: str) -> List[str]:
        """Get user's SEO goals"""
        goal_record = self.db.query(SeoGoal).filter(SeoGoal.user_id == user_id).first()
        return goal_record.goals if goal_record else []
    
    def _generate_tasks_from_scores(self, user_id: str, tab: str, goals: List[str]) -> int:
        """Generate tasks from as_is_scores for a specific tab (onpage/offpage/technical)"""
        tasks_created = 0
        
        # Query as_is_scores for parameters with critical or needs_attention status
        problem_scores = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.parameter_tab == tab,
            AsIsScore.status.in_(['critical', 'needs_attention'])
        ).all()
        
        if not problem_scores:
            logger.info(f"No {tab} issues found for user {user_id}")
            return 0
        
        # Create a task for each problematic parameter
        for score in problem_scores:
            # Calculate priority based on status and score
            if score.status == 'critical':
                impact = 9
                effort = self._estimate_effort(score.parameter_group, score.sub_parameter, tab)
            else:  # needs_attention
                impact = 7
                effort = self._estimate_effort(score.parameter_group, score.sub_parameter, tab)
            
            priority = self._calculate_priority(impact, effort)
            
            # Generate title from parameter info
            title = self._generate_task_title(score)
            description = score.recommendation or f"Improve {score.parameter_group}"
            
            # Parse details for affected pages count
            affected_count = self._extract_affected_count(score.details)
            
            tasks_created += self._create_task(
                user_id=user_id,
                title=title,
                description=description,
                category=tab,
                priority=priority,
                impact_score=float(impact),
                effort_score=float(effort),
                parameter_group=score.parameter_group or f"{tab.capitalize()} Optimization",
                sub_parameter=score.sub_parameter,
                related_goal=self._align_goal(goals, self._get_goal_keywords(tab)),
                affected_pages_count=affected_count,
                impact_description=f"Current score: {score.score:.1f}/{score.max_score:.1f} - {score.status}",
                effort_description=self._effort_to_label(effort),
                page_urls=[]
            )
        
        return tasks_created
    
    def _generate_task_title(self, score: AsIsScore) -> str:
        """Generate a descriptive task title from AsIsScore"""
        param = score.sub_parameter or score.parameter_group
        
        # Try to extract count from details
        count = self._extract_affected_count(score.details)
        
        if count > 0:
            return f"Fix {param} ({count} pages affected)"
        else:
            return f"Improve {param}"
    
    def _extract_affected_count(self, details_json: Optional[str]) -> int:
        """Extract affected pages count from details JSON"""
        if not details_json:
            return 0
        
        try:
            details = json.loads(details_json) if isinstance(details_json, str) else details_json
            
            # Look for common count keys
            for key in ['affected_pages', 'page_count', 'count', 'total_pages', 'issues_count']:
                if key in details:
                    return int(details[key])
            
            return 0
        except:
            return 0
    
    def _estimate_effort(self, parameter_group: Optional[str], sub_parameter: Optional[str], tab: str) -> int:
        """Estimate effort score (1-10) based on parameter type"""
        group = (parameter_group or "").lower()
        sub = (sub_parameter or "").lower()
        
        # High effort (7-9) - off-page and technical usually require more work
        if tab == 'offpage':
            return 8
        
        if any(term in group + sub for term in ['backlink', 'authority', 'performance', 'core web vitals', 'lcp', 'cls', 'inp']):
            return 7
        
        # Medium effort (4-6)
        if any(term in group + sub for term in ['content', 'structure', 'canonical', 'robots', 'technical']):
            return 5
        
        # Low effort (2-3)
        if any(term in group + sub for term in ['title', 'meta', 'alt', 'h1', 'snippet', 'description']):
            return 2
        
        # Default medium
        return 5
    
    def _effort_to_label(self, effort: int) -> str:
        """Convert effort score to label"""
        if effort <= 3:
            return "Low"
        elif effort <= 6:
            return "Medium"
        else:
            return "High"
    
    def _get_goal_keywords(self, tab: str) -> List[str]:
        """Get goal alignment keywords for each tab"""
        if tab == 'onpage':
            return ["traffic", "rankings", "visibility"]
        elif tab == 'offpage':
            return ["authority", "rankings"]
        else:  # technical
            return ["position", "user experience", "performance"]
    
    def _calculate_priority(self, impact: int, effort: int) -> str:
        """Calculate task priority based on impact-effort matrix"""
        # High priority: High impact + Low-Medium effort (quick wins) OR Critical impact
        if impact >= 8 and effort <= 5:
            return 'high'
        if impact >= 9:  # Critical issues are always high priority
            return 'high'
        
        # Low priority: Low impact OR High effort with low-medium impact
        if impact <= 4:
            return 'low'
        if effort >= 7 and impact <= 6:
            return 'low'
        
        # Medium priority: Everything else
        return 'medium'
    
    def _align_goal(self, goals: List[str], keywords: List[str]) -> Optional[str]:
        """Align task with user's SEO goals"""
        if not goals:
            return None
        
        for goal in goals:
            goal_lower = goal.lower()
            if any(keyword in goal_lower for keyword in keywords):
                return goal
        
        # Return first goal if no match
        return goals[0] if goals else None
    
    def _create_task(
        self,
        user_id: str,
        title: str,
        description: str,
        category: str,
        priority: str,
        impact_score: float,
        effort_score: float,
        parameter_group: str,
        sub_parameter: Optional[str],
        related_goal: Optional[str],
        affected_pages_count: int,
        impact_description: str,
        effort_description: str,
        page_urls: List[str]
    ) -> int:
        """Create a task and its associated page relationships"""
        try:
            task = ActionPlanTask(
                user_id=user_id,
                task_title=title,
                task_description=description,
                category=category,
                priority=priority,
                impact_score=impact_score,
                effort_score=effort_score,
                status='not_started',
                parameter_group=parameter_group,
                sub_parameter=sub_parameter,
                related_goal=related_goal,
                affected_pages_count=affected_pages_count,
                impact_description=impact_description,
                effort_description=effort_description
            )
            
            self.db.add(task)
            self.db.flush()  # Get task ID
            
            # Create page relationships
            for page_url in page_urls[:10]:  # Limit to first 10 pages
                task_page = ActionPlanTaskPage(
                    task_id=task.id,
                    page_url=page_url
                )
                self.db.add(task_page)
            
            return 1
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return 0
    
    def get_tasks(
        self,
        user_id: str,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get action plan tasks with optional filters"""
        query = self.db.query(ActionPlanTask).filter(ActionPlanTask.user_id == user_id)
        
        if category:
            query = query.filter(ActionPlanTask.category == category)
        if priority:
            query = query.filter(ActionPlanTask.priority == priority)
        if status:
            query = query.filter(ActionPlanTask.status == status)
        
        tasks = query.order_by(
            ActionPlanTask.priority.desc(),
            ActionPlanTask.impact_score.desc()
        ).all()
        
        return [self._task_to_dict(task) for task in tasks]
    
    def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Get action plan summary with task counts"""
        total = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id
        ).scalar() or 0
        
        not_started = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id,
            ActionPlanTask.status == 'not_started'
        ).scalar() or 0
        
        in_progress = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id,
            ActionPlanTask.status == 'in_progress'
        ).scalar() or 0
        
        completed = self.db.query(func.count(ActionPlanTask.id)).filter(
            ActionPlanTask.user_id == user_id,
            ActionPlanTask.status == 'completed'
        ).scalar() or 0
        
        return {
            "total_tasks": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed
        }
    
    def update_task_status(
        self,
        task_id: int,
        user_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update task status and create history entry"""
        task = self.db.query(ActionPlanTask).filter(
            ActionPlanTask.id == task_id,
            ActionPlanTask.user_id == user_id
        ).first()
        
        if not task:
            raise ValueError(f"Task {task_id} not found for user {user_id}")
        
        old_status = task.status
        task.status = new_status
        task.updated_at = datetime.utcnow()
        
        if new_status == 'completed':
            task.completed_at = datetime.utcnow()
        
        # Create history entry
        history = ActionPlanTaskHistory(
            task_id=task_id,
            old_status=old_status,
            new_status=new_status,
            notes=notes
        )
        self.db.add(history)
        self.db.commit()
        
        return self._task_to_dict(task)
    
    def _task_to_dict(self, task: ActionPlanTask) -> Dict[str, Any]:
        """Convert task model to dictionary"""
        return {
            "id": task.id,
            "title": task.task_title,
            "description": task.task_description,
            "category": task.category,
            "priority": task.priority,
            "status": task.status,
            "impact_score": task.impact_score,
            "effort_score": task.effort_score,
            "parameter_group": task.parameter_group,
            "sub_parameter": task.sub_parameter,
            "related_goal": task.related_goal,
            "affected_pages_count": task.affected_pages_count,
            "impact_description": task.impact_description,
            "effort_description": task.effort_description,
            "recommendation": task.recommendation,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
