"""
Enhanced GSC Service for Comprehensive Off-Page Data
Fetches detailed backlink data including anchor text and historical data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)


class EnhancedGSCService:
    """
    Enhanced GSC service for comprehensive off-page parameter analysis.
    
    Provides:
    - Historical links data (time-series for link velocity)
    - Detailed anchor text from linking pages
    - Referring domain authority indicators
    - Brand mention queries from Performance API
    """
    
    BASE_URL = "https://www.googleapis.com/webmasters/v3"
    SEARCH_ANALYTICS_URL = "https://searchconsole.googleapis.com/v1"
    TIMEOUT = 30.0
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def fetch_links_with_anchors(self, site_url: str) -> Dict[str, Any]:
        """
        Fetch comprehensive links data including sample anchor texts.
        
        Returns:
            Dict with:
            - referring_domains: int
            - top_linking_sites: List[str]
            - sample_links: List[Dict] (with target_page, source_url)
        """
        try:
            encoded_url = quote(site_url, safe='')
            
            # 1. Get referring domains count
            links_url = f"{self.BASE_URL}/sites/{encoded_url}/links"
            
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(links_url, headers=self.headers)
                response.raise_for_status()
                links_data = response.json()
            
            referring_domains = len(links_data.get("sampleLinks", []))
            top_linking_sites = [
                urlparse(link.get("sourceUrl", "")).netloc 
                for link in links_data.get("sampleLinks", [])[:100]
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_linking_sites = []
            for site in top_linking_sites:
                if site and site not in seen:
                    seen.add(site)
                    unique_linking_sites.append(site)
            
            # 2. Get sample links with more details
            sample_links = []
            for link in links_data.get("sampleLinks", [])[:50]:  # Top 50 for analysis
                sample_links.append({
                    "source_url": link.get("sourceUrl", ""),
                    "target_page": link.get("targetPage", ""),
                    "source_domain": urlparse(link.get("sourceUrl", "")).netloc
                })
            
            return {
                "referring_domains": len(unique_linking_sites),
                "top_linking_sites": unique_linking_sites,
                "sample_links": sample_links,
                "total_sample_count": len(links_data.get("sampleLinks", []))
            }
            
        except Exception as e:
            logger.error(f"[Enhanced GSC] Error fetching links: {e}")
            return {
                "referring_domains": 0,
                "top_linking_sites": [],
                "sample_links": [],
                "error": str(e)
            }
    
    async def fetch_historical_links(
        self, 
        site_url: str, 
        months_back: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical links data for link velocity calculation.
        
        Note: GSC Links API doesn't provide historical data directly.
        This is a limitation - we can only get current snapshot.
        
        For link velocity, we'd need to:
        1. Store snapshots over time in our DB
        2. Or use external backlink APIs (Moz, Ahrefs - paid)
        
        Returns:
            List of time-series data points (if available from DB)
        """
        logger.warning("[Enhanced GSC] Historical links data not available from GSC API directly")
        logger.info("[Enhanced GSC] Link velocity requires periodic snapshots stored in DB")
        
        # Return current snapshot only
        current_links = await self.fetch_links_with_anchors(site_url)
        
        return [{
            "snapshot_date": datetime.now().isoformat(),
            "referring_domains": current_links.get("referring_domains", 0),
            "note": "Historical data requires periodic snapshots"
        }]
    
    async def fetch_brand_mentions(
        self,
        site_url: str,
        brand_name: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch brand mention queries from GSC Performance API.
        
        Searches for queries containing the brand name and analyzes:
        - Linked mentions (queries with clicks)
        - Unlinked mentions (queries with impressions but no clicks)
        
        Args:
            site_url: Website URL
            brand_name: Brand name to search for
            days_back: Days of historical data
            
        Returns:
            Dict with brand mention analysis
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            encoded_url = quote(site_url, safe='')
            search_url = f"{self.SEARCH_ANALYTICS_URL}/sites/{encoded_url}/searchAnalytics/query"
            
            request_body = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query"],
                "rowLimit": 1000,
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "query",
                        "operator": "contains",
                        "expression": brand_name.lower()
                    }]
                }]
            }
            
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    search_url, 
                    headers=self.headers, 
                    json=request_body
                )
                response.raise_for_status()
                data = response.json()
            
            rows = data.get("rows", [])
            
            # Analyze mentions
            linked_mentions = []
            unlinked_mentions = []
            total_brand_clicks = 0
            total_brand_impressions = 0
            
            for row in rows:
                query = row.get("keys", [""])[0]
                clicks = row.get("clicks", 0)
                impressions = row.get("impressions", 0)
                position = row.get("position", 100)
                
                total_brand_clicks += clicks
                total_brand_impressions += impressions
                
                if clicks > 0:
                    linked_mentions.append({
                        "query": query,
                        "clicks": clicks,
                        "impressions": impressions,
                        "position": position
                    })
                else:
                    unlinked_mentions.append({
                        "query": query,
                        "impressions": impressions,
                        "position": position
                    })
            
            return {
                "total_brand_queries": len(rows),
                "linked_mentions_count": len(linked_mentions),
                "unlinked_mentions_count": len(unlinked_mentions),
                "total_brand_clicks": total_brand_clicks,
                "total_brand_impressions": total_brand_impressions,
                "top_linked_mentions": linked_mentions[:10],
                "top_unlinked_mentions": unlinked_mentions[:10],
                "brand_ctr": (total_brand_clicks / total_brand_impressions * 100) if total_brand_impressions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"[Enhanced GSC] Error fetching brand mentions: {e}")
            return {
                "total_brand_queries": 0,
                "linked_mentions_count": 0,
                "unlinked_mentions_count": 0,
                "error": str(e)
            }
    
    async def fetch_linking_pages_with_context(
        self,
        site_url: str,
        target_page: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch linking pages for  specific target page to understand link context.
        
        Args:
            site_url: Website URL
            target_page: Specific page to get links for (optional)
            
        Returns:
            List of linking pages with metadata
        """
        try:
            encoded_url = quote(site_url, safe='')
            
            if target_page:
                encoded_target = quote(target_page, safe='')
                links_url = f"{self.BASE_URL}/sites/{encoded_url}/links?targetPage={encoded_target}"
            else:
                links_url = f"{self.BASE_URL}/sites/{encoded_url}/links"
            
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(links_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
            
            sample_links = data.get("sampleLinks", [])
            
            linking_pages = []
            for link in sample_links[:50]:
                source_url = link.get("sourceUrl", "")
                source_domain = urlparse(source_url).netloc
                
                linking_pages.append({
                    "source_url": source_url,
                    "source_domain": source_domain,
                    "target_page": link.get("targetPage", ""),
                    # Note: Anchor text not available directly from GSC API
                    # Would need to crawl source URLs to extract
                    "note": "Anchor text requires crawling source page"
                })
            
            return linking_pages
            
        except Exception as e:
            logger.error(f"[Enhanced GSC] Error fetching linking pages: {e}")
            return []
    
    async def estimate_link_authority_distribution(
        self,
        linking_domains: List[str]
    ) -> Dict[str, Any]:
        """
        Estimate authority distribution of linking domains using heuristics.
        
        Uses TLD-based and well-known domain heuristics.
        
        Args:
            linking_domains: List of linking domain names
            
        Returns:
            Authority distribution analysis
        """
        high_authority = 0
        medium_authority = 0
        low_authority = 0
        
        # High-authority TLDs
        high_auth_tlds = ['.gov', '.edu', '.mil']
        
        # Known high-authority domains (tier 1)
        known_high_auth = [
            'wikipedia.org', 'nytimes.com', 'wsj.com', 'bbc.com', 
            'forbes.com', 'bloomberg.com', 'reuters.com'
        ]
        
        for domain in linking_domains:
            domain_lower = domain.lower()
            
            # Check TLD
            is_high_tld = any(domain_lower.endswith(tld) for tld in high_auth_tlds)
            
            # Check known domains
            is_known_high = any(known in domain_lower for known in known_high_auth)
            
            if is_high_tld or is_known_high:
                high_authority += 1
            elif domain_lower.endswith('.org') or domain_lower.endswith('.com'):
                medium_authority += 1
            else:
                low_authority += 1
        
        total = len(linking_domains)
        
        return {
            "high_authority_count": high_authority,
            "medium_authority_count": medium_authority,
            "low_authority_count": low_authority,
            "high_authority_ratio": high_authority / total if total > 0 else 0,
            "medium_authority_ratio": medium_authority / total if total > 0 else 0,
            "low_authority_ratio": low_authority / total if total > 0 else 0
        }
