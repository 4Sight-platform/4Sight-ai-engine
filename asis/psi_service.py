"""
PageSpeed Insights Service
Fetches Core Web Vitals (LCP, INP, CLS) using Google PageSpeed Insights API
"""

import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PageSpeedService:
    """
    Service for fetching Core Web Vitals data using PageSpeed Insights API.
    
    Provides:
    - LCP (Largest Contentful Paint)
    - INP (Interaction to Next Paint)
    - CLS (Cumulative Layout Shift)
    - Overall performance score
    """
    
    BASE_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    TIMEOUT = 60.0  # PSI can be slow
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def get_cwv(
        self, 
        url: str, 
        strategy: str = "mobile"
    ) -> Dict[str, Any]:
        """
        Fetch Core Web Vitals for a URL.
        
        Args:
            url: URL to analyze
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Dict with CWV metrics and statuses
        """
        params = {
            "url": url,
            "strategy": strategy,
            "key": self.api_key,
            "category": "performance"
        }
        
        result = {
            "url": url,
            "strategy": strategy,
            "lcp_score": None,
            "lcp_status": None,
            "inp_score": None,
            "inp_status": None,
            "cls_score": None,
            "cls_status": None,
            "overall_status": None,
            "performance_score": None,
            "data_available": False,
            "error": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(self.BASE_URL, params=params)
                
                if response.status_code != 200:
                    result["error"] = f"API returned {response.status_code}"
                    logger.error(f"[PSI] Error for {url}: {result['error']}")
                    return result
                
                data = response.json()
                
                # Extract loading experience (field data - real user metrics)
                loading_exp = data.get("loadingExperience", {})
                metrics = loading_exp.get("metrics", {})
                
                # LCP
                lcp_data = metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {})
                if lcp_data:
                    result["lcp_score"] = lcp_data.get("percentile")
                    result["lcp_status"] = self._normalize_status(lcp_data.get("category"))
                
                # INP (replaces FID)
                inp_data = metrics.get("INTERACTION_TO_NEXT_PAINT", {})
                if inp_data:
                    result["inp_score"] = inp_data.get("percentile")
                    result["inp_status"] = self._normalize_status(inp_data.get("category"))
                
                # CLS
                cls_data = metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {})
                if cls_data:
                    # CLS is a ratio, not milliseconds
                    result["cls_score"] = cls_data.get("percentile")
                    result["cls_status"] = self._normalize_status(cls_data.get("category"))
                
                # Overall category
                result["overall_status"] = self._normalize_status(
                    loading_exp.get("overall_category")
                )
                
                # Performance score from Lighthouse
                lighthouse = data.get("lighthouseResult", {})
                categories = lighthouse.get("categories", {})
                perf = categories.get("performance", {})
                result["performance_score"] = perf.get("score", 0) * 100 if perf.get("score") else None
                
                result["data_available"] = True
                logger.info(f"[PSI] Successfully fetched CWV for {url} ({strategy})")
                
        except httpx.TimeoutException:
            result["error"] = "Request timed out"
            logger.error(f"[PSI] Timeout for {url}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"[PSI] Error for {url}: {e}")
        
        return result
    
    async def get_cwv_both_devices(self, url: str) -> Dict[str, Any]:
        """
        Fetch CWV for both mobile and desktop.
        
        Returns:
            Dict with mobile and desktop CWV data
        """
        mobile = await self.get_cwv(url, "mobile")
        desktop = await self.get_cwv(url, "desktop")
        
        # Determine overall status (mobile is primary for SEO)
        overall = self._compute_overall_status(mobile, desktop)
        
        return {
            "url": url,
            "mobile": mobile,
            "desktop": desktop,
            "overall_status": overall,
            "mobile_pass": mobile.get("overall_status") == "good",
            "desktop_pass": desktop.get("overall_status") == "good"
        }
    
    def _normalize_status(self, category: str) -> Optional[str]:
        """Normalize PSI category to our status format."""
        if not category:
            return None
        
        mapping = {
            "FAST": "good",
            "AVERAGE": "needs_improvement",
            "SLOW": "poor",
            "GOOD": "good",
            "NEEDS_IMPROVEMENT": "needs_improvement",
            "POOR": "poor"
        }
        return mapping.get(category.upper(), category.lower())
    
    def _compute_overall_status(
        self, 
        mobile: Dict, 
        desktop: Dict
    ) -> str:
        """
        Compute overall CWV status from mobile and desktop results.
        Mobile is weighted more heavily for SEO.
        """
        mobile_status = mobile.get("overall_status")
        desktop_status = desktop.get("overall_status")
        
        status_priority = {"poor": 0, "needs_improvement": 1, "good": 2}
        
        # If either is missing, use the available one
        if not mobile_status:
            return desktop_status or "needs_improvement"
        if not desktop_status:
            return mobile_status
        
        # Use the worse of the two (mobile-first approach)
        mobile_rank = status_priority.get(mobile_status, 1)
        desktop_rank = status_priority.get(desktop_status, 1)
        
        # Weight mobile more heavily
        combined = (mobile_rank * 0.7) + (desktop_rank * 0.3)
        
        if combined >= 1.5:
            return "good"
        elif combined >= 0.7:
            return "needs_improvement"
        else:
            return "poor"
