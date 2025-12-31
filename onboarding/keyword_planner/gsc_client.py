"""
GSC Client - Google Search Console Integration for Keyword Planner

This module fetches "low-hanging fruit" keywords from GSC:
- Keywords where user ranks #11-50 (close to top 10, room for improvement)
- Sorted by impressions (highest opportunity first)

These keywords get 40% priority in the final keyword universe.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# Position thresholds for low-hanging fruit
POSITION_MIN = 11  # Exclude keywords already in top 10
POSITION_MAX = 50  # Upper limit for "low-hanging" opportunity


class GSCKeywordClient:
    """
    Client for fetching keyword opportunities from Google Search Console.
    
    Wraps the existing GSCConnector for keyword-specific use cases.
    """
    
    def __init__(self, oauth_manager=None):
        """
        Initialize GSC client.
        
        Args:
            oauth_manager: OAuthManager instance for token refresh.
        """
        self.oauth_manager = oauth_manager or self._get_default_oauth_manager()
    
    def _get_default_oauth_manager(self):
        """Get default OAuth manager from environment."""
        from onboarding.oauth_manager import OAuthManager
        
        return OAuthManager(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            encryption_key=os.getenv("ENCRYPTION_KEY")
        )
    
    async def get_low_hanging_fruit(
        self,
        user_id: str,
        website_url: str,
        days: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch low-hanging fruit keywords from GSC.
        
        Low-hanging fruit = Keywords where user ranks #11-50.
        These are close to breaking into top 10 with some optimization.
        
        Args:
            user_id: User ID for OAuth token refresh.
            website_url: Website URL to query GSC for.
            days: Number of days to look back (default: 30).
            limit: Maximum keywords to return (default: 50).
        
        Returns:
            List of keyword dictionaries with GSC metrics.
        """
        # Get fresh access token
        access_token = await self.oauth_manager.refresh_access_token(user_id)
        if not access_token:
            logger.warning(f"No GSC token for user {user_id}")
            return []
        
        # Import GSC connector
        from onboarding.ga_gsc_connection.gsc_connect import GSCConnector
        connector = GSCConnector(access_token)
        
        # Validate website ownership
        is_valid, site_url = await connector.validate_ownership(website_url)
        if not is_valid or not site_url:
            logger.warning(f"GSC ownership not validated for {website_url}")
            return []
        
        # Calculate date range
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        logger.info(f"Fetching GSC data for {site_url} ({start_date} to {end_date})")
        
        try:
            # Fetch search analytics
            rows = await connector.fetch_search_analytics(
                site_url,
                start_date,
                end_date,
                dimensions=["query"],
                row_limit=500  # Get more to filter
            )
            
            # Filter for low-hanging fruit (position 11-50)
            low_hanging = []
            for row in rows:
                keys = row.get('keys', [])
                if not keys:
                    continue
                
                query = keys[0]
                position = row.get('position', 100)
                clicks = row.get('clicks', 0)
                impressions = row.get('impressions', 0)
                ctr = row.get('ctr', 0)
                
                # Check if within low-hanging fruit range
                if POSITION_MIN <= position <= POSITION_MAX:
                    low_hanging.append({
                        "keyword": query,
                        "position": round(position, 1),
                        "clicks": clicks,
                        "impressions": impressions,
                        "ctr": round(ctr * 100, 2),  # Convert to percentage
                        "source": "verified",  # DB valid: verified, generated, custom
                        "opportunity_score": self._calculate_opportunity_score(
                            position, impressions, clicks
                        )
                    })
            
            # Sort by opportunity score (descending)
            low_hanging.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            # Return top N
            result = low_hanging[:limit]
            logger.info(f"Found {len(result)} low-hanging fruit keywords (rank {POSITION_MIN}-{POSITION_MAX})")
            
            return result
            
        except Exception as e:
            logger.error(f"GSC fetch error: {e}")
            return []
    
    def _calculate_opportunity_score(
        self,
        position: float,
        impressions: int,
        clicks: int
    ) -> float:
        """
        Calculate opportunity score for a keyword.
        
        Higher score = better opportunity for quick wins.
        
        Formula:
        - Closer to position 10 = higher score
        - More impressions = higher score
        - Some clicks already = validation of interest
        
        Args:
            position: Current average position.
            impressions: Total impressions.
            clicks: Total clicks.
        
        Returns:
            Opportunity score (0-100).
        """
        # Position score: closer to 10 = higher (max 40 points)
        # Position 11 = 40, Position 50 = 0
        position_score = max(0, (50 - position) / 40 * 40)
        
        # Impression score: more = better (max 40 points)
        # Normalize: 1000 impressions = 40 points
        impression_score = min(40, (impressions / 1000) * 40)
        
        # Click validation score: some clicks = validated interest (max 20 points)
        click_score = min(20, clicks * 2)
        
        return round(position_score + impression_score + click_score, 1)
    
    async def get_already_ranking_keywords(
        self,
        user_id: str,
        website_url: str,
        keywords_to_check: List[str],
        days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check which keywords user already ranks for.
        
        Used to filter out keywords from other sources if user already ranks top 10.
        
        Args:
            user_id: User ID for OAuth.
            website_url: Website URL.
            keywords_to_check: List of keywords to check.
            days: Lookback period.
        
        Returns:
            Dictionary mapping keyword -> position data (only for ranking keywords).
        """
        # Get fresh access token
        access_token = await self.oauth_manager.refresh_access_token(user_id)
        if not access_token:
            return {}
        
        from onboarding.ga_gsc_connection.gsc_connect import GSCConnector
        connector = GSCConnector(access_token)
        
        is_valid, site_url = await connector.validate_ownership(website_url)
        if not is_valid or not site_url:
            return {}
        
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        try:
            rows = await connector.fetch_search_analytics(
                site_url,
                start_date,
                end_date,
                dimensions=["query"],
                row_limit=1000
            )
            
            # Build lookup of all ranking keywords
            ranking_data = {}
            keywords_lower = {kw.lower() for kw in keywords_to_check}
            
            for row in rows:
                keys = row.get('keys', [])
                if not keys:
                    continue
                
                query = keys[0]
                if query.lower() in keywords_lower:
                    ranking_data[query.lower()] = {
                        "position": row.get('position', 100),
                        "clicks": row.get('clicks', 0),
                        "impressions": row.get('impressions', 0)
                    }
            
            return ranking_data
            
        except Exception as e:
            logger.error(f"GSC ranking check error: {e}")
            return {}


# Convenience function
async def get_low_hanging_fruit(user_id: str, website_url: str) -> List[Dict[str, Any]]:
    """
    Convenience function to get low-hanging fruit keywords.
    
    Args:
        user_id: User ID.
        website_url: Website URL.
    
    Returns:
        List of low-hanging fruit keywords with metrics.
    """
    client = GSCKeywordClient()
    return await client.get_low_hanging_fruit(user_id, website_url)
