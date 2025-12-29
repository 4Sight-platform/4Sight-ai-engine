"""
Google Search Console Connection Module (Onboarding Validation)

Replicated from Tester/backend/services/search_console.py
Focus: Ownership Verification ONLY (No heavy data fetching)
"""

import logging
from typing import Optional, List, Tuple, Dict
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

def normalize_site_url(url: str) -> str:
    """
    Normalize site URL for comparison.
    Handles: https://example.com, sc-domain:example.com
    """
    url = url.strip().lower()
    
    # Handle domain property format
    if url.startswith("sc-domain:"):
        domain = url.replace("sc-domain:", "")
        return domain.rstrip("/")
    
    # Parse URL and extract domain
    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc.rstrip("/")
    
    # Fallback - treat as domain
    return url.rstrip("/")

class GSCConnector:
    """
    Handles GSC connection and ownership verification.
    """
    
    API_BASE = "https://www.googleapis.com/webmasters/v3"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    async def list_sites(self) -> List[Dict[str, str]]:
        """
        List all verified sites/properties in Search Console.
        Returns: List of {"site_url": url, "permission_level": level}
        """
        logger.info("[GSC] Listing sites...")
        
        url = f"{self.API_BASE}/sites"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            if response.status_code == 401:
                logger.error("[GSC] Unauthorized (401). Token may be expired.")
                raise ValueError("Unauthorized: Invalid/Expired Token")
                
            response.raise_for_status()
            data = response.json()
            
            sites = []
            for entry in data.get("siteEntry", []):
                sites.append({
                    "site_url": entry.get("siteUrl", ""),
                    "permission_level": entry.get("permissionLevel", "unknown")
                })
            
            return sites

    async def validate_ownership(self, target_url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the user owns the specific target URL.
        Returns: (is_owner, matched_site_url)
        """
        try:
            owned_sites = await self.list_sites()
            
            if not owned_sites:
                return False, None
            
            normalized_target = normalize_site_url(target_url)
            
            for site in owned_sites:
                site_url = site["site_url"]
                normalized_owned = normalize_site_url(site_url)
                
                # Check 1: Exact Match
                if normalized_target == normalized_owned:
                    return True, site_url
                
                # Check 2: Partial Match (Domain Property covers URL)
                if normalized_target in normalized_owned or normalized_owned in normalized_target:
                    return True, site_url
            
            return False, None
            
        except Exception as e:
            logger.error(f"[GSC] Validation failed: {e}")
            raise

    async def fetch_search_analytics(
        self, 
        site_url: str, 
        start_date: str, 
        end_date: str, 
        dimensions: List[str] = ["query"],
        row_limit: int = 1000
    ) -> List[Dict]:
        """Fetch search analytics data (ranking keywords)."""
        import urllib.parse
        encoded_site_url = urllib.parse.quote(site_url, safe='')
        
        url = f"{self.API_BASE}/sites/{encoded_site_url}/searchAnalytics/query"
        
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data.get("rows", [])
        except Exception as e:
            logger.error(f"[GSC] Error fetching analytics for {site_url}: {e}")
            return []
