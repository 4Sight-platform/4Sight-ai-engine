"""
SERP API Service
Fetches SERP features and competitor visibility data
Uses the provided SERP API key
"""

import logging
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SERPService:
    """
    Service for fetching SERP data including:
    - SERP feature detection (featured snippets, PAA, local pack, etc.)
    - Domain visibility in SERP
    - Competitor presence analysis
    """
    
    # ValueSERP API base URL (commonly used SERP API)
    API_BASE = "https://api.valueserp.com/search"
    
    # SERP features to track
    TRACKED_FEATURES = [
        "featured_snippet",
        "people_also_ask",
        "local_pack",
        "knowledge_graph",
        "image_pack",
        "video_results",
        "top_stories",
        "shopping_results",
        "related_searches",
        "site_links"
    ]
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(
        self,
        keyword: str,
        location: str = "United States",
        language: str = "en",
        device: str = "desktop"
    ) -> Dict[str, Any]:
        """
        Perform a SERP search for a keyword.
        
        Args:
            keyword: Search query
            location: Geographic location
            language: Language code
            device: 'desktop' or 'mobile'
            
        Returns:
            Dict with SERP results and features
        """
        params = {
            "api_key": self.api_key,
            "q": keyword,
            "location": location,
            "hl": language,
            "device": device,
            "num": 10  # Top 10 results
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_BASE, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "keyword": keyword,
                    "organic_results": data.get("organic_results", []),
                    "features": self._extract_features(data),
                    "search_metadata": data.get("search_metadata", {})
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[SERP] HTTP error for '{keyword}': {e.response.status_code}")
            return {"keyword": keyword, "error": str(e), "organic_results": [], "features": []}
        except Exception as e:
            logger.error(f"[SERP] Error searching '{keyword}': {e}")
            return {"keyword": keyword, "error": str(e), "organic_results": [], "features": []}
    
    def _extract_features(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract detected SERP features from response."""
        features = []
        
        # Featured Snippet
        if data.get("answer_box") or data.get("featured_snippet"):
            features.append({
                "type": "featured_snippet",
                "present": True,
                "data": data.get("answer_box") or data.get("featured_snippet")
            })
        
        # People Also Ask
        if data.get("related_questions") or data.get("people_also_ask"):
            features.append({
                "type": "people_also_ask",
                "present": True,
                "count": len(data.get("related_questions", []) or data.get("people_also_ask", []))
            })
        
        # Local Pack
        if data.get("local_results") or data.get("local_pack"):
            features.append({
                "type": "local_pack",
                "present": True,
                "count": len(data.get("local_results", []) or data.get("local_pack", []))
            })
        
        # Knowledge Graph
        if data.get("knowledge_graph"):
            features.append({
                "type": "knowledge_graph",
                "present": True,
                "data": data.get("knowledge_graph")
            })
        
        # Image Pack
        if data.get("inline_images") or data.get("image_results"):
            features.append({
                "type": "image_pack",
                "present": True,
                "count": len(data.get("inline_images", []) or data.get("image_results", []))
            })
        
        # Video Results
        if data.get("inline_videos") or data.get("video_results"):
            features.append({
                "type": "video_results",
                "present": True,
                "count": len(data.get("inline_videos", []) or data.get("video_results", []))
            })
        
        # Shopping Results
        if data.get("shopping_results") or data.get("inline_shopping"):
            features.append({
                "type": "shopping_results",
                "present": True,
                "count": len(data.get("shopping_results", []) or data.get("inline_shopping", []))
            })
        
        # Related Searches
        if data.get("related_searches"):
            features.append({
                "type": "related_searches",
                "present": True,
                "count": len(data.get("related_searches", []))
            })
        
        return features
    
    async def analyze_keyword(
        self,
        keyword: str,
        target_domain: str,
        competitor_domains: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a keyword for SERP features and domain presence.
        
        Args:
            keyword: Search query to analyze
            target_domain: User's domain to check for presence
            competitor_domains: List of competitor domains to track
            
        Returns:
            Dict with feature presence and domain visibility
        """
        serp_data = await self.search(keyword)
        
        if "error" in serp_data:
            return {
                "keyword": keyword,
                "error": serp_data["error"],
                "target_in_top10": False,
                "target_position": None,
                "features": [],
                "competitors_in_top10": []
            }
        
        organic = serp_data.get("organic_results", [])
        features = serp_data.get("features", [])
        
        # Check target domain presence
        target_position = None
        target_in_top10 = False
        for i, result in enumerate(organic[:10]):
            result_domain = self._extract_domain(result.get("link", ""))
            if target_domain.lower() in result_domain.lower():
                target_position = i + 1
                target_in_top10 = True
                break
        
        # Check competitor presence
        competitors_in_top10 = []
        if competitor_domains:
            for result in organic[:10]:
                result_domain = self._extract_domain(result.get("link", ""))
                for comp in competitor_domains:
                    if comp.lower() in result_domain.lower():
                        competitors_in_top10.append({
                            "domain": comp,
                            "position": organic.index(result) + 1
                        })
                        break
        
        # Check if target appears in any SERP feature
        target_in_features = []
        for feature in features:
            if feature.get("data"):
                feature_data = str(feature.get("data", {}))
                if target_domain.lower() in feature_data.lower():
                    target_in_features.append(feature["type"])
        
        return {
            "keyword": keyword,
            "target_in_top10": target_in_top10,
            "target_position": target_position,
            "target_in_features": target_in_features,
            "features": [f["type"] for f in features],
            "features_count": len(features),
            "competitors_in_top10": competitors_in_top10
        }
    
    async def batch_analyze(
        self,
        keywords: List[str],
        target_domain: str,
        competitor_domains: List[str] = None,
        max_keywords: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze multiple keywords (limited to conserve API calls).
        
        Args:
            keywords: List of keywords to analyze
            target_domain: User's domain
            competitor_domains: List of competitor domains
            max_keywords: Maximum keywords to analyze (API rate limit consideration)
            
        Returns:
            Dict with aggregated analysis results
        """
        # Limit keywords to avoid excessive API usage
        keywords_to_analyze = keywords[:max_keywords]
        
        results = []
        for keyword in keywords_to_analyze:
            result = await self.analyze_keyword(keyword, target_domain, competitor_domains)
            results.append(result)
        
        # Aggregate results
        total_in_top10 = len([r for r in results if r.get("target_in_top10")])
        all_features = set()
        for r in results:
            all_features.update(r.get("features", []))
        
        feature_in_count = {}
        for r in results:
            for feature in r.get("target_in_features", []):
                feature_in_count[feature] = feature_in_count.get(feature, 0) + 1
        
        return {
            "analyzed_keywords": len(keywords_to_analyze),
            "keywords_in_top10": total_in_top10,
            "top10_rate": round(total_in_top10 / len(keywords_to_analyze) * 100, 1) if keywords_to_analyze else 0,
            "unique_features_found": list(all_features),
            "target_feature_presence": feature_in_count,
            "results": results
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return url
