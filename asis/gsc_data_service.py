"""
GSC Data Service
Fetches and stores Google Search Console data for AS-IS State
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from urllib.parse import quote

logger = logging.getLogger(__name__)


class GSCDataService:
    """
    Service for fetching comprehensive GSC data including:
    - Query metrics (clicks, impressions, CTR, position)
    - Page metrics
    - Index coverage
    - Links data
    """
    
    API_BASE = "https://www.googleapis.com/webmasters/v3"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _get_date_ranges(self) -> Dict[str, Dict[str, str]]:
        """
        Get current and previous 30-day periods.
        Returns dict with 'current' and 'previous' date ranges.
        """
        today = datetime.now().date()
        
        # Current period: last 30 days (excluding today as data may be incomplete)
        current_end = today - timedelta(days=1)
        current_start = current_end - timedelta(days=29)
        
        # Previous period: 30 days before current period
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=29)
        
        return {
            "current": {
                "start": current_start.isoformat(),
                "end": current_end.isoformat()
            },
            "previous": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat()
            }
        }
    
    async def fetch_query_metrics(
        self, 
        site_url: str,
        start_date: str,
        end_date: str,
        row_limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch query-level metrics from GSC.
        
        Returns:
            List of dicts with query, clicks, impressions, ctr, position
        """
        encoded_site = quote(site_url, safe='')
        url = f"{self.API_BASE}/sites/{encoded_site}/searchAnalytics/query"
        
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "rowLimit": row_limit,
            "aggregationType": "auto"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for row in data.get("rows", []):
                    results.append({
                        "query": row.get("keys", [""])[0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0) * 100, 2),  # Convert to percentage
                        "position": round(row.get("position", 0), 1)
                    })
                
                logger.info(f"[GSC] Fetched {len(results)} query metrics")
                return results
                
        except Exception as e:
            logger.error(f"[GSC] Error fetching query metrics: {e}")
            return []
    
    async def fetch_page_metrics(
        self,
        site_url: str,
        start_date: str,
        end_date: str,
        row_limit: int = 500
    ) -> List[Dict]:
        """
        Fetch page-level metrics from GSC.
        
        Returns:
            List of dicts with page, clicks, impressions, ctr, position
        """
        encoded_site = quote(site_url, safe='')
        url = f"{self.API_BASE}/sites/{encoded_site}/searchAnalytics/query"
        
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["page"],
            "rowLimit": row_limit,
            "aggregationType": "auto"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for row in data.get("rows", []):
                    results.append({
                        "page": row.get("keys", [""])[0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0) * 100, 2),
                        "position": round(row.get("position", 0), 1)
                    })
                
                logger.info(f"[GSC] Fetched {len(results)} page metrics")
                return results
                
        except Exception as e:
            logger.error(f"[GSC] Error fetching page metrics: {e}")
            return []
    
    async def fetch_links(self, site_url: str) -> Dict[str, Any]:
        """
        Fetch links data from GSC (referring domains and top linking sites).
        
        Returns:
            Dict with referring_domains and top_linking_sites
        """
        encoded_site = quote(site_url, safe='')
        
        result = {
            "referring_domains": 0,
            "top_linking_sites": []
        }
        
        # Fetch external links (linking sites)
        try:
            url = f"{self.API_BASE}/sites/{encoded_site}/searchAnalytics/query"
            
            # GSC doesn't have a direct links API in v3, but we can use the URL Inspection API
            # or fall back to Search Analytics
            # For now, we'll use a simplified approach
            
            # Get links from the sites API (limited data)
            sites_url = f"https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
            
            # Note: Full links data requires additional API access
            # For MVP, we'll return placeholder data and note this limitation
            logger.warning("[GSC] Links API has limited access in GSC v3. Using fallback.")
            
            return result
            
        except Exception as e:
            logger.error(f"[GSC] Error fetching links: {e}")
            return result
    
    async def fetch_site_totals(
        self,
        site_url: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Fetch site-wide aggregates without dimensions to include anonymized queries.
        This matches the GSC UI "Total" numbers.
        """
        encoded_site = quote(site_url, safe='')
        url = f"{self.API_BASE}/sites/{encoded_site}/searchAnalytics/query"
        
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": [],  # No dimensions = Site-wide totals
            "aggregationType": "byProperty"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                
                rows = data.get("rows", [])
                if rows:
                    # Without dimensions, we get a single row
                    row = rows[0]
                    return {
                        "total_clicks": row.get("clicks", 0),
                        "total_impressions": row.get("impressions", 0),
                        "avg_ctr": round(row.get("ctr", 0) * 100, 2),
                        "avg_position": round(row.get("position", 0), 1),
                        "top10_count": 0,    # Not applicable for site-wide
                        "keyword_count": 0   # Not applicable
                    }
                return self._calculate_totals([]) # Return zeros
                
        except Exception as e:
            logger.error(f"[GSC] Error fetching site totals: {e}")
            return self._calculate_totals([]) # Fallback to zeros

    async def fetch_all_metrics(self, site_url: str) -> Dict[str, Any]:
        """
        Fetch all GSC metrics for both current and previous periods.
        """
        date_ranges = self._get_date_ranges()
        
        # 1. Fetch site-wide totals (accurate traffic numbers)
        current_totals = await self.fetch_site_totals(
            site_url, 
            date_ranges["current"]["start"], 
            date_ranges["current"]["end"]
        )
        
        previous_totals = await self.fetch_site_totals(
            site_url, 
            date_ranges["previous"]["start"], 
            date_ranges["previous"]["end"]
        )
        
        # 2. Fetch specific query/page breakdowns
        current_queries = await self.fetch_query_metrics(
            site_url, 
            date_ranges["current"]["start"],
            date_ranges["current"]["end"]
        )
        
        current_pages = await self.fetch_page_metrics(
            site_url,
            date_ranges["current"]["start"],
            date_ranges["current"]["end"]
        )
        
        previous_queries = await self.fetch_query_metrics(
            site_url,
            date_ranges["previous"]["start"],
            date_ranges["previous"]["end"]
        )
        
        previous_pages = await self.fetch_page_metrics(
            site_url,
            date_ranges["previous"]["start"],
            date_ranges["previous"]["end"]
        )
        
        # 3. Augment totals with counts derived from query lists (since site-wide API doesn't give these)
        # Note: We keep the Clicks/Impressions from fetch_site_totals (Correct)
        # But we add top10_count from the query analysis (Best Effort)
        query_derived_stats = self._calculate_totals(current_queries)
        prev_derived_stats = self._calculate_totals(previous_queries)
        
        current_totals["top10_count"] = query_derived_stats["top10_count"]
        current_totals["keyword_count"] = query_derived_stats["keyword_count"]
        previous_totals["top10_count"] = prev_derived_stats["top10_count"]
        
        # Fetch links (single snapshot)
        links_data = await self.fetch_links(site_url)
        
        return {
            "date_ranges": date_ranges,
            "current": {
                "queries": current_queries,
                "pages": current_pages,
                "totals": current_totals
            },
            "previous": {
                "queries": previous_queries,
                "pages": previous_pages,
                "totals": previous_totals
            },
            "changes": self._calculate_changes(current_totals, previous_totals),
            "links": links_data
        }
    
    def _calculate_totals(self, queries: List[Dict], filter_keywords: List[str] = None) -> Dict[str, Any]:
        """Calculate aggregate totals from query metrics."""
        if not queries:
            return {
                "total_clicks": 0,
                "total_impressions": 0,
                "avg_ctr": 0.0,
                "avg_position": 0.0,
                "top10_count": 0,
                "keyword_count": 0
            }
        
        # Filter queries if keywords provided
        target_queries = queries
        if filter_keywords:
            target_queries = [q for q in queries if q["query"] in filter_keywords]
            
            # If filtration results in empty list, return zeros
            if not target_queries:
                return {
                    "total_clicks": 0,
                    "total_impressions": 0,
                    "avg_ctr": 0.0,
                    "avg_position": 0.0,
                    "top10_count": 0,
                    "keyword_count": 0
                }
        
        total_clicks = sum(q["clicks"] for q in target_queries)
        total_impressions = sum(q["impressions"] for q in target_queries)
        
        # Weighted average position (by impressions)
        if total_impressions > 0:
            weighted_position = sum(q["position"] * q["impressions"] for q in target_queries) / total_impressions
        else:
            weighted_position = 0.0
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        top10_count = len([q for q in target_queries if q["position"] <= 10])
        
        return {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": round(avg_ctr, 2),
            "avg_position": round(weighted_position, 1),
            "top10_count": top10_count,
            "keyword_count": len(target_queries)
        }
    
    def _calculate_changes(self, current: Dict, previous: Dict) -> Dict[str, float]:
        """Calculate percentage changes between periods."""
        def pct_change(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return round(((curr - prev) / prev) * 100, 1)
        
        return {
            "clicks_change": pct_change(current["total_clicks"], previous["total_clicks"]),
            "impressions_change": pct_change(current["total_impressions"], previous["total_impressions"]),
            "ctr_change": round(current["avg_ctr"] - previous["avg_ctr"], 2),
            "position_change": round(previous["avg_position"] - current["avg_position"], 1),  # Positive = improved
            "top10_change": current["top10_count"] - previous["top10_count"]
        }
