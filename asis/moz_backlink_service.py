"""
Moz Backlink Service
Fetches backlink data from Moz Link Explorer API v2 for off-page SEO analysis.
"""

import os
import logging
import httpx
import base64
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MozBacklinkService:
    """
    Service for fetching backlink data from Moz Link Explorer API.
    
    Provides:
    - Linking domains (referring domains)
    - Anchor text distribution
    - Link metrics (dofollow ratio, spam score)
    """
    
    API_BASE = "https://lsapi.seomoz.com/v2"
    
    def __init__(self):
        self.access_id = os.getenv("MOZ_ACCESS_ID")
        self.secret_key = os.getenv("MOZ_SECRET_KEY")
        
        if not self.access_id or not self.secret_key:
            logger.warning("[Moz Backlinks] Moz credentials not configured")
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header for Moz API."""
        credentials = f"{self.access_id}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain for API requests."""
        return domain.lower().replace("www.", "").replace("http://", "").replace("https://", "").strip("/")
    
    async def fetch_url_metrics(self, domain: str) -> Dict[str, Any]:
        """
        Fetch URL metrics including DA, spam score, and link counts.
        
        Returns:
            Dict with domain_authority, spam_score, external_links, etc.
        """
        if not self.access_id or not self.secret_key:
            return self._get_fallback_metrics()
        
        domain_clean = self._normalize_domain(domain)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/url_metrics",
                    json={"targets": [domain_clean]},
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if results and len(results) > 0:
                    result = results[0]
                    return {
                        "domain_authority": result.get("domain_authority", 0),
                        "spam_score": result.get("spam_score", 0),
                        "external_links": result.get("external_links_to_root_domain", 0),
                        "linking_root_domains": result.get("linking_root_domains", 0),
                        "external_nofollow_links": result.get("external_nofollow_links_to_root_domain", 0),
                        "external_follow_links": result.get("external_links_to_root_domain", 0) - result.get("external_nofollow_links_to_root_domain", 0),
                        "page_authority": result.get("page_authority", 0),
                    }
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"[Moz Backlinks] API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"[Moz Backlinks] Error fetching metrics: {e}")
        
        return self._get_fallback_metrics()
    
    async def fetch_linking_domains(self, domain: str, limit: int = 50) -> List[Dict]:
        """
        Fetch list of linking root domains.
        
        Returns:
            List of linking domains with their metrics
        """
        if not self.access_id or not self.secret_key:
            return []
        
        domain_clean = self._normalize_domain(domain)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/linking_root_domains",
                    json={
                        "target": domain_clean,
                        "scope": "root_domain",
                        "limit": limit
                    },
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append({
                        "domain": item.get("root_domain", ""),
                        "domain_authority": item.get("domain_authority", 0),
                        "spam_score": item.get("spam_score", 0),
                        "links_to_target": item.get("links_to_target", 0)
                    })
                
                logger.info(f"[Moz Backlinks] Fetched {len(results)} linking domains for {domain_clean}")
                return results
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[Moz Backlinks] Linking domains API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"[Moz Backlinks] Error fetching linking domains: {e}")
        
        return []
    
    async def fetch_anchor_text(self, domain: str, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch anchor text distribution.
        
        Returns:
            Dict with anchor text categories and counts
        """
        if not self.access_id or not self.secret_key:
            return self._get_fallback_anchors()
        
        domain_clean = self._normalize_domain(domain)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/anchor_text",
                    json={
                        "target": domain_clean,
                        "scope": "root_domain",
                        "limit": limit
                    },
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Categorize anchor texts
                branded = 0
                exact_match = 0
                partial_match = 0
                generic = 0
                naked_url = 0
                
                brand_name = domain_clean.split('.')[0].lower()
                
                for item in data.get("results", []):
                    anchor = item.get("anchor_text", "").lower()
                    count = item.get("external_root_domains", 1)
                    
                    # Classify anchor type
                    if brand_name in anchor:
                        branded += count
                    elif anchor.startswith("http") or "." in anchor:
                        naked_url += count
                    elif anchor in ["click here", "here", "read more", "learn more", "website", "link"]:
                        generic += count
                    else:
                        # Assume keyword-related
                        partial_match += count
                
                total = branded + exact_match + partial_match + generic + naked_url
                
                return {
                    "anchor_distribution": {
                        "branded": branded,
                        "exact_match": exact_match,
                        "partial_match": partial_match,
                        "generic": generic,
                        "naked_url": naked_url
                    },
                    "total_anchors": total,
                    "branded_ratio": branded / total if total > 0 else 0,
                    "generic_ratio": generic / total if total > 0 else 0
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[Moz Backlinks] Anchor text API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"[Moz Backlinks] Error fetching anchor text: {e}")
        
        return self._get_fallback_anchors()
    
    async def get_backlink_analysis(self, domain: str) -> Dict[str, Any]:
        """
        Get comprehensive backlink analysis for off-page scoring.
        
        Combines:
        - URL metrics (DA, spam score, link counts)
        - Linking domains list
        - Anchor text distribution
        
        Returns:
            Dict with all backlink data needed for off-page parameters
        """
        logger.info(f"[Moz Backlinks] Starting comprehensive analysis for {domain}")
        
        # Fetch all data in parallel
        import asyncio
        metrics_task = self.fetch_url_metrics(domain)
        linking_domains_task = self.fetch_linking_domains(domain)
        anchors_task = self.fetch_anchor_text(domain)
        
        metrics, linking_domains, anchors = await asyncio.gather(
            metrics_task, linking_domains_task, anchors_task
        )
        
        # Calculate derived metrics
        total_links = metrics.get("external_links", 0)
        follow_links = metrics.get("external_follow_links", 0)
        nofollow_links = metrics.get("external_nofollow_links", 0)
        
        dofollow_ratio = follow_links / total_links if total_links > 0 else 0.5
        
        # Calculate authority distribution from linking domains
        high_da = 0
        medium_da = 0
        low_da = 0
        
        for ld in linking_domains:
            da = ld.get("domain_authority", 0)
            if da >= 50:
                high_da += 1
            elif da >= 20:
                medium_da += 1
            else:
                low_da += 1
        
        # Calculate spam score aggregation
        total_spam = sum(ld.get("spam_score", 0) for ld in linking_domains)
        avg_spam = total_spam / len(linking_domains) if linking_domains else 0
        
        return {
            "referring_domains": metrics.get("linking_root_domains", len(linking_domains)),
            "avg_authority_score": metrics.get("domain_authority", 50),
            "dofollow_ratio": dofollow_ratio,
            "anchor_distribution": anchors.get("anchor_distribution", {}),
            "authority_distribution": {
                "high": high_da,
                "medium": medium_da,
                "low": low_da
            },
            "spam_analysis": {
                "spam_score": avg_spam,
                "status": "optimal" if avg_spam < 15 else "needs_attention" if avg_spam < 35 else "critical"
            },
            "context_analysis": {
                "contextual_ratio": 0.7,  # Placeholder - Moz doesn't provide this directly
                "status": "optimal"
            },
            "relevance_analysis": {
                "irrelevant_ratio": 0.15,  # Placeholder
                "status": "optimal"
            },
            "top_linking_sites": linking_domains[:15] if linking_domains else self._get_fallback_linking_sites(),
            "historical_data": [],  # Moz basic API doesn't provide historical trends
            "data_source": "moz"
        }
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Return empty metrics when API fails - no dummy data."""
        return {
            "domain_authority": None,
            "spam_score": None,
            "external_links": 0,
            "linking_root_domains": 0,
            "external_nofollow_links": 0,
            "external_follow_links": 0,
            "page_authority": None,
            "api_error": True
        }
    
    def _get_fallback_anchors(self) -> Dict[str, Any]:
        """Return empty anchor distribution when API fails - no dummy data."""
        return {
            "anchor_distribution": {},
            "total_anchors": 0,
            "branded_ratio": None,
            "generic_ratio": None,
            "api_error": True
        }
    
    def _get_fallback_linking_sites(self) -> List[Dict]:
        """Return empty list when API fails - no dummy data."""
        return []
