"""
Snapshot Lock Service
Manages the snapshot-first locking system for As-Is State.

DESIGN PRINCIPLES:
- Lock is triggered AUTOMATICALLY from Keyword Universe finalize_selection
- NO separate lock button/endpoint for As-Is State
- Uses EXISTING tables (as_is_scores.is_baseline, as_is_summary_cache.baseline_*) for snapshots
- All reads redirect to baseline data during lock period

LOCK FLOW:
1. User completes keyword selection → finalize_selection() is called
2. System captures As-Is baseline data (is_baseline=True in as_is_scores)
3. keyword_universes.is_locked = True for 90 days
4. All subsequent As-Is reads check lock status and return baseline if locked
5. Lock expires after 90 days, live APIs resume
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from Database.models import (
    KeywordUniverse, AsIsScore, AsIsSummaryCache
)

logger = logging.getLogger(__name__)

# Lock duration: 3 months (90 days)
LOCK_DURATION_DAYS = 90


class SnapshotLockService:
    """
    Manages As-Is State snapshot locking using EXISTING tables.
    
    Lock is triggered automatically by Keyword Universe finalize_selection.
    Uses:
    - as_is_scores.is_baseline = True for parameter snapshots
    - as_is_summary_cache.baseline_* fields for summary snapshots
    - keyword_universes.is_locked and locked_until for lock status
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def is_locked(self, user_id: str) -> bool:
        """
        Check if As-Is State is currently locked for this user.
        
        Returns True if:
        - KeywordUniverse.is_locked == True
        - Lock has not expired (locked_until >= today)
        """
        universe = self.db.query(KeywordUniverse).filter(
            KeywordUniverse.user_id == user_id
        ).first()
        
        if not universe or not universe.is_locked:
            return False
        
        # Check if lock has expired
        if universe.locked_until and universe.locked_until < date.today():
            return False
        
        return True
    
    def get_lock_status(self, user_id: str) -> Dict[str, Any]:
        """Get detailed lock status for a user."""
        universe = self.db.query(KeywordUniverse).filter(
            KeywordUniverse.user_id == user_id
        ).first()
        
        if not universe:
            return {
                "is_locked": False,
                "status": "no_universe",
                "message": "Keyword universe not initialized. Complete onboarding first.",
                "locked_until": None,
                "has_baseline": False
            }
        
        is_expired = (
            universe.locked_until and 
            universe.locked_until < date.today()
        )
        
        # Check if baseline exists
        has_baseline = self._has_baseline(user_id)
        
        if is_expired:
            status = "expired"
            message = "Lock has expired. Live data fetching is now enabled."
        elif universe.is_locked:
            status = "locked"
            message = f"As-Is State is locked until {universe.locked_until}. Reading from baseline snapshot."
        else:
            status = "unlocked"
            message = "As-Is State is unlocked. Fetching live data from APIs."
        
        return {
            "is_locked": universe.is_locked and not is_expired,
            "status": status,
            "locked_until": universe.locked_until.isoformat() if universe.locked_until else None,
            "has_baseline": has_baseline,
            "message": message
        }
    
    def _has_baseline(self, user_id: str) -> bool:
        """Check if user has baseline data captured."""
        # Check as_is_scores for baseline
        baseline_score = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.is_baseline == True
        ).first()
        
        if baseline_score:
            return True
        
        # Check as_is_summary_cache for baseline
        cache = self.db.query(AsIsSummaryCache).filter(
            AsIsSummaryCache.user_id == user_id
        ).first()
        
        if cache and cache.baseline_captured_at:
            return True
        
        return False
    
    def get_baseline_snapshot_date(self, user_id: str) -> Optional[date]:
        """Get the snapshot_date of the baseline data."""
        baseline_score = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.is_baseline == True
        ).first()
        
        if baseline_score:
            return baseline_score.snapshot_date
        
        return None
    
    def should_read_from_baseline(self, user_id: str) -> bool:
        """
        Determine if As-Is reads should come from baseline.
        
        Returns True if:
        - User is locked
        - Baseline data exists
        """
        if not self.is_locked(user_id):
            return False
        
        return self._has_baseline(user_id)
    
    def get_baseline_scores(self, user_id: str, tab: str = None) -> list:
        """
        Get baseline scores for locked user.
        
        Args:
            user_id: User ID
            tab: Optional tab filter (onpage, offpage, technical)
        
        Returns:
            List of AsIsScore records marked as baseline
        """
        query = self.db.query(AsIsScore).filter(
            AsIsScore.user_id == user_id,
            AsIsScore.is_baseline == True
        )
        
        if tab:
            query = query.filter(AsIsScore.parameter_tab == tab)
        
        return query.all()
    
    def get_baseline_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get baseline summary data for locked user.
        
        Returns summary data from as_is_summary_cache.baseline_* fields.
        """
        cache = self.db.query(AsIsSummaryCache).filter(
            AsIsSummaryCache.user_id == user_id
        ).first()
        
        if not cache or not cache.baseline_captured_at:
            return None
        
        return {
            "organic_traffic": {
                "total_clicks": cache.baseline_total_clicks or 0,
                "total_impressions": cache.baseline_total_impressions or 0,
                "avg_ctr": 0,  # Can be calculated if needed
                "data_available": cache.baseline_total_clicks is not None
            },
            "keywords_performance": {
                "avg_position": cache.baseline_avg_position or 0,
                "top10_keywords": cache.baseline_top10_keywords or 0,
                "data_available": cache.baseline_avg_position is not None
            },
            "serp_features": {
                "features_count": cache.baseline_features_count or 0,
                "data_available": cache.baseline_features_count is not None
            },
            "competitor_rank": {
                "your_rank": cache.baseline_your_rank,
                "your_visibility_score": cache.baseline_visibility_score or 0,
                "data_available": cache.baseline_your_rank is not None
            },
            "baseline_captured_at": cache.baseline_captured_at.isoformat() if cache.baseline_captured_at else None
        }
    
    def reject_mutation_if_locked(self, user_id: str, operation: str = "mutation"):
        """
        Check if user is locked and raise error if mutation is attempted.
        
        Use this at the start of any write/mutation endpoints, such as:
        - /as-is/refresh
        
        Args:
            user_id: User ID to check
            operation: Description of the operation being attempted
        
        Raises:
            ValueError: If As-Is State is locked
        """
        if self.is_locked(user_id):
            lock_status = self.get_lock_status(user_id)
            raise ValueError(
                f"LOCKED_STATE: Cannot perform '{operation}' while As-Is State is locked. "
                f"Lock expires on {lock_status.get('locked_until', 'unknown')}. "
                f"During the lock period, all data is read from the baseline snapshot."
            )
