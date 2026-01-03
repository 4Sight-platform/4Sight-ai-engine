#Serp_services
"""
SERP API Service
Fetches SERP features and competitor visibility data
Uses the provided SERP API key (ValueSERP) or Google CSE credentials
"""

import logging
import httpx
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SERPService:
    """
    Service for fetching SERP data including:
    - SERP feature detection (featured snippets, PAA, local pack, etc.)
    - Domain visibility in SERP
    - Competitor presence analysis
    
    Supports:
    1. SerpApi (primary, rich features)
    2. Google Custom Search JSON API (fallback/alternative, organic results only)
    """
    
    # SerpApi Base URL
    SERPAPI_BASE = "https://serpapi.com/search"
    
    # Google CSE base URL
    GOOGLE_CSE_BASE = "https://www.googleapis.com/customsearch/v1"
    
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
    
    def __init__(
        self, 
        api_key: str = None, 
        google_cse_key: str = None, 
        google_cse_cx: str = None
    ):
        self.api_key = api_key
        self.google_cse_key = google_cse_key
        self.google_cse_cx = google_cse_cx
        
        if not self.api_key and not (self.google_cse_key and self.google_cse_cx):
            logger.warning("[SERP] No valid API keys provided (ValueSERP or Google CSE)")
    
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
        # Priority 1: SerpApi (Rich Features)
        if self.api_key:
            return await self._search_serpapi(keyword, location, language, device)
            
        # Priority 2: Google CSE (Organic Results Only)
        elif self.google_cse_key and self.google_cse_cx:
            return await self._search_google_cse(keyword, location, language)
            
        else:
            return {
                "keyword": keyword, 
                "error": "No API configuration available", 
                "organic_results": [], 
                "features": []
            }
            
    async def _search_serpapi(
        self,
        keyword: str,
        location: str,
        language: str,
        device: str
    ) -> Dict[str, Any]:
        """Search using SerpApi."""
        params = {
            "api_key": self.api_key,
            "q": keyword,
            "location": location,
            "hl": language,
            "device": device,
            "num": 10,
            "engine": "google"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.SERPAPI_BASE, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                logger.info(f"[SERP] SerpApi keys for '{keyword}': {list(data.keys())}")
                if "organic_results" in data:
                    logger.info(f"[SERP] Found {len(data['organic_results'])} organic results")
                else:
                    logger.warn("[SERP] No 'organic_results' key in SerpApi response")
                
                # SerpApi & ValueSERP share very similar JSON structure for these keys
                # So we can reuse _extract_features largely as is.
                
                return {
                    "keyword": keyword,
                    "organic_results": data.get("organic_results", []),
                    "features": self._extract_features(data),
                    "search_metadata": data.get("search_metadata", {}),
                    "source": "serpapi"
                }
                
        except Exception as e:
            logger.error(f"[SERP] SerpApi error for '{keyword}': {e}")
            # Failover to CSE if configured
            if self.google_cse_key and self.google_cse_cx:
                logger.info(f"[SERP] Failing over to Google CSE for '{keyword}'")
                return await self._search_google_cse(keyword, location, language)
                
            return {"keyword": keyword, "error": str(e), "organic_results": [], "features": []}

    async def _search_google_cse(
        self,
        keyword: str,
        location: str,
        language: str
    ) -> Dict[str, Any]:
        """Search using Google Custom Search JSON API."""
        # Note: CSE doesn't support 'device' param purely, it adapts.
        # Location is handled via gl (country) or near (if enabled, but gl is safer)
        # Using 'gl' parameter for country (e.g., 'us', 'in'). derived from location string is hard, defaulting to 'us' or user-config if available.
        
        params = {
            "key": self.google_cse_key,
            "cx": self.google_cse_cx,
            "q": keyword,
            "hl": language,
            "num": 10
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.GOOGLE_CSE_BASE, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                organic_results = []
                
                for i, item in enumerate(items):
                    organic_results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "position": i + 1,
                        "displayed_link": item.get("displayLink")
                    })
                
                # Google CSE doesn't provide structured features like PAA
                return {
                    "keyword": keyword,
                    "organic_results": organic_results,
                    "features": [], # CSE Limitation
                    "search_metadata": data.get("searchInformation", {}),
                    "source": "google_cse"
                }
                
        except Exception as e:
            logger.error(f"[SERP] Google CSE error for '{keyword}': {e}")
            return {"keyword": keyword, "error": str(e), "organic_results": [], "features": []}
    
    def _extract_features(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract detected SERP features from response."""
        features = []
        
        # Featured Snippet (SerpApi uses 'answer_box' or sometimes just 'organic_results' with snippet)
        if data.get("answer_box"):
            features.append({
                "type": "featured_snippet",
                "present": True,
                "data": data.get("answer_box")
            })
        
        # People Also Ask (SerpApi uses 'related_questions')
        if data.get("related_questions"):
            features.append({
                "type": "people_also_ask",
                "present": True,
                "count": len(data.get("related_questions", [])),
                "data": data.get("related_questions")
            })
        
        # Local Pack (SerpApi uses 'local_results')
        if data.get("local_results"):
            features.append({
                "type": "local_pack",
                "present": True,
                "count": len(data.get("local_results", [])),
                "data": data.get("local_results")
            })
        
        # Knowledge Graph (SerpApi uses 'knowledge_graph')
        if data.get("knowledge_graph"):
            features.append({
                "type": "knowledge_graph",
                "present": True,
                "data": data.get("knowledge_graph")
            })
        
        # Image Pack (SerpApi uses 'inline_images')
        if data.get("inline_images"):
            features.append({
                "type": "image_pack",
                "present": True,
                "count": len(data.get("inline_images", [])),
                "data": data.get("inline_images")
            })
        
        # Video Results (SerpApi uses 'inline_videos')
        if data.get("inline_videos"):
            features.append({
                "type": "video_results",
                "present": True,
                "count": len(data.get("inline_videos", [])),
                "data": data.get("inline_videos")
            })
        
        # Shopping Results (SerpApi uses 'shopping_results')
        if data.get("shopping_results"):
            features.append({
                "type": "shopping_results",
                "present": True,
                "count": len(data.get("shopping_results", [])),
                "data": data.get("shopping_results")
            })
        
        # Related Searches (SerpApi uses 'related_searches')
        if data.get("related_searches"):
            features.append({
                "type": "related_searches",
                "present": True,
                "count": len(data.get("related_searches", [])),
                "data": data.get("related_searches")
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
                "error": serp_data.get("error"),
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
