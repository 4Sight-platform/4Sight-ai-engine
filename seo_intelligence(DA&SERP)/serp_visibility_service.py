"""
SERP Visibility Features Service
Tracks owned SERP features (Featured Snippets, PAA, Image Pack) using Serper.dev API
"""

import os
import logging
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SERPVisibilityService:
    """
    Service for tracking SERP features ownership using Serper.dev API.
    
    Detects and counts SERP features where the client domain appears:
    - Featured Snippets
    - People Also Ask (PAA)
    - Image Pack
    - Video Results
    - Knowledge Graph
    - Local Pack
    """
    
    API_BASE = "https://google.serper.dev/search"
    
    # SERP features to track
    TRACKED_FEATURES = {
        "featured_snippet": "Featured Snippet",
        "people_also_ask": "People Also Ask",
        "image_pack": "Image Pack",
        "video_results": "Video Results",
        "knowledge_graph": "Knowledge Graph",
        "local_pack": "Local Pack"
    }
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        
        if not self.api_key:
            logger.warning("[SERP Visibility] Serper.dev API key not configured")
    
    async def fetch_serp_features(
        self,
        domain: str,
        keywords: List[str],
        country: str = "us",
        language: str = "en",
        max_keywords: int = 20
    ) -> Dict[str, Any]:
        """
        Fetch SERP features for multiple keywords and check domain ownership.
        
        Args:
            domain: Client domain to check for ownership (e.g., "example.com")
            keywords: List of keywords to analyze
            country: Country code (e.g., "us", "uk", "in")
            language: Language code (e.g., "en")
            max_keywords: Maximum keywords to analyze (rate limiting)
            
        Returns:
            Dict with aggregated SERP features data
        """
        if not self.api_key:
            logger.error("[SERP Visibility] Missing Serper.dev API key")
            return {
                "error": "Serper.dev API key not configured",
                "total_features_owned": 0,
                "features": {},
                "keywords_analyzed": 0
            }
        
        if not keywords:
            logger.warning(f"[SERP Visibility] No keywords provided for domain {domain}")
            return {
                "total_features_owned": 0,
                "features": {},
                "keywords_analyzed": 0,
                "message": "No keywords to analyze"
            }
        
        # Limit keywords to conserve API credits
        keywords_to_analyze = keywords[:max_keywords]
        logger.info(f"[SERP Visibility] Analyzing {len(keywords_to_analyze)} keywords for {domain}")
        
        # Normalize domain for comparison
        domain_clean = domain.lower().replace("www.", "").replace("http://", "").replace("https://", "").strip("/")
        
        # Track features across all keywords
        features_count = {feature: 0 for feature in self.TRACKED_FEATURES.keys()}
        total_owned = 0
        keywords_analyzed = 0
        
        # Process each keyword
        for keyword in keywords_to_analyze:
            try:
                result = await self._fetch_single_keyword(keyword, country, language)
                
                if result.get("error"):
                    logger.warning(f"[SERP Visibility] Error for keyword '{keyword}': {result['error']}")
                    continue
                
                keywords_analyzed += 1
                
                # Check each feature type
                owned = self._check_domain_ownership(domain_clean, result)
                
                for feature, count in owned.items():
                    features_count[feature] += count
                    total_owned += count
                    
            except Exception as e:
                logger.error(f"[SERP Visibility] Error analyzing keyword '{keyword}': {str(e)}")
                continue
        
        # Remove features with 0 count for cleaner response
        features_owned = {k: v for k, v in features_count.items() if v > 0}
        
        logger.info(f"[SERP Visibility] Found {total_owned} features for {domain}")
        
        return {
            "total_features_owned": total_owned,
            "features": features_owned,
            "keywords_analyzed": keywords_analyzed,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _fetch_single_keyword(
        self,
        keyword: str,
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Fetch SERP data for a single keyword from Serper.dev.
        
        Args:
            keyword: Search query
            country: Country code
            language: Language code
            
        Returns:
            Dict with SERP data
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": keyword,
            "gl": country,
            "hl": language
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_BASE,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[SERP Visibility] Serper.dev API error: {e.response.status_code} - {e.response.text}")
            return {"error": f"API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"[SERP Visibility] Error fetching SERP data: {str(e)}")
            return {"error": str(e)}
    
    def _check_domain_ownership(self, domain: str, serp_data: Dict) -> Dict[str, int]:
        """
        Check which SERP features are owned by the domain.
        
        Args:
            domain: Normalized client domain
            serp_data: SERP data from Serper.dev
            
        Returns:
            Dict with feature counts
        """
        owned = {feature: 0 for feature in self.TRACKED_FEATURES.keys()}
        
        # Featured Snippet (answerBox)
        answer_box = serp_data.get("answerBox")
        if answer_box:
            if self._domain_in_block(domain, answer_box):
                owned["featured_snippet"] = 1
        
        # People Also Ask
        paa = serp_data.get("peopleAlsoAsk", [])
        if paa:
            for item in paa:
                if self._domain_in_block(domain, item):
                    owned["people_also_ask"] = 1
                    break
        
        # Images
        images = serp_data.get("images", [])
        if images:
            for img in images:
                if self._domain_in_block(domain, img):
                    owned["image_pack"] = 1
                    break
        
        # Videos
        videos = serp_data.get("videos", [])
        if videos:
            for video in videos:
                if self._domain_in_block(domain, video):
                    owned["video_results"] = 1
                    break
        
        # Knowledge Graph
        knowledge_graph = serp_data.get("knowledgeGraph")
        if knowledge_graph:
            if self._domain_in_block(domain, knowledge_graph):
                owned["knowledge_graph"] = 1
        
        # Local Pack
        local_results = serp_data.get("places", [])
        if local_results:
            for place in local_results:
                if self._domain_in_block(domain, place):
                    owned["local_pack"] = 1
                    break
        
        return owned
    
    def _domain_in_block(self, domain: str, block: Dict) -> bool:
        """
        Check if domain appears in a SERP feature block.
        
        Args:
            domain: Normalized client domain
            block: SERP feature block data
            
        Returns:
            True if domain appears in the block
        """
        # Check common URL fields
        url_fields = ["link", "url", "source", "website"]
        
        for field in url_fields:
            url = block.get(field, "")
            if url:
                url_clean = url.lower().replace("www.", "").replace("http://", "").replace("https://", "")
                if domain in url_clean:
                    return True
        
        # Check domain field
        block_domain = block.get("domain", "")
        if block_domain:
            domain_clean = block_domain.lower().replace("www.", "")
            if domain in domain_clean:
                return True
        
        # Check nested items (for PAA, local pack, etc.)
        items = block.get("items", [])
        for item in items:
            if isinstance(item, dict):
                if self._domain_in_block(domain, item):
                    return True
        
        return False
    
    async def get_features_owned(
        self,
        domain: str,
        keywords: List[str],
        country: str = "us"
    ) -> Dict[str, Any]:
        """
        Public method to get SERP features owned by domain.
        This is the main entry point called by the API endpoint.
        
        Args:
            domain: Client domain
            keywords: List of tracked keywords
            country: Country code
            
        Returns:
            Dict with feature counts and metadata
        """
        result = await self.fetch_serp_features(
            domain=domain,
            keywords=keywords,
            country=country
        )
        
        return {
            "total_features_owned": result.get("total_features_owned", 0),
            "features": result.get("features", {}),
            "keywords_analyzed": result.get("keywords_analyzed", 0),
            "last_updated": datetime.utcnow().date().isoformat(),
            "error": result.get("error")
        }
