"""
Competitor Analysis Module for Onboarding
Replicates logic from CompetitorPOC to discover competitors based on Page 6 keywords
"""

import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import httpx
import re

logger = logging.getLogger(__name__)

# ==================== Domain Extraction ====================

def extract_root_domain(url: str) -> str:
    """
    Normalize a URL to its root domain.
    
    Examples:
        "https://www.example.com/page" → "example.com"
        "http://blog.example.com/" → "blog.example.com"
    """
    if not url:
        return ""
    
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        
        # Remove port number
        domain = domain.split(":")[0]
        
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Lowercase and strip
        return domain.lower().strip()
    except Exception:
        # Fallback: simple regex
        url = re.sub(r'^https?://', '', url)
        domain = url.split('/')[0].split(':')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.lower().strip()


# ==================== SERP Fetching ====================

class GoogleCSEFetcher:
    """
    Google Custom Search Engine fetcher for SERP results.
    Uses the same API keys from config.
    """
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx
    
    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx)
    
    async def search(
        self,
        keyword: str,
        num_results: int = 10,
        location: str = "India",
        language: str = "en"
    ) -> List[Dict[str, any]]:
        """
        Fetch SERP results for a keyword.
        
        Returns:
            List of {"rank": int, "url": str, "domain": str, "title": str}
        """
        if not self.is_configured():
            raise ValueError("Google CSE not configured (missing API key or CX)")
        
        # Google CSE returns max 10 results per request
        num = min(num_results, 10)
        
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": keyword,
            "num": num,
            "hl": language,
            "gl": self._map_location_to_country_code(location),
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[SERP] Google CSE API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"[SERP] Request failed: {e}")
            raise
        
        results = []
        items = data.get("items", [])
        
        for idx, item in enumerate(items, start=1):
            url = item.get("link", "")
            if not url:
                continue
            
            results.append({
                "rank": idx,
                "url": url,
                "domain": extract_root_domain(url),
                "title": item.get("title"),
                "snippet": item.get("snippet")
            })
        
        logger.info(f"[SERP] Found {len(results)} results for '{keyword}'")
        return results
    
    @staticmethod
    def _map_location_to_country_code(location: str) -> str:
        """Map location names to Google country codes."""
        location_map = {
            "india": "in",
            "united states": "us",
            "usa": "us",
            "uk": "uk",
            "united kingdom": "uk",
            "germany": "de",
            "france": "fr",
            "australia": "au",
            "canada": "ca",
        }
        return location_map.get(location.lower(), "in")


# ==================== Importance Scoring ====================

def compute_domain_importance(
    serp_results: Dict[str, List[Dict[str, any]]]
) -> Dict[str, Dict[str, any]]:
    """
    Compute importance scores for all domains across keywords.
    
    Algorithm:
    1. For each keyword's SERP results, extract unique domains
    2. For each domain, count how many keywords it appears in
    3. Importance = number of keywords the domain appeared in
    
    Args:
        serp_results: Dict mapping keyword → list of SERP result dicts
        
    Returns:
        Dict mapping domain → {importance, keywords_matched}
    """
    domain_keywords_map: Dict[str, List[str]] = {}
    
    for keyword, results in serp_results.items():
        # Get unique domains for this keyword
        seen_domains = set()
        for result in results:
            domain = result.get("domain")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                if domain not in domain_keywords_map:
                    domain_keywords_map[domain] = []
                domain_keywords_map[domain].append(keyword)
    
    # Convert to score objects
    domain_scores = {}
    for domain, keywords_matched in domain_keywords_map.items():
        domain_scores[domain] = {
            "domain": domain,
            "importance": len(keywords_matched),
            "keywords_matched": keywords_matched
        }
    
    return domain_scores


def assign_priority(importance: int, total_keywords: int) -> str:
    """
    Assign priority bucket based on keyword coverage.
    
    - HIGH: Appears in >66% of keywords
    - MEDIUM: Appears in 33-66% of keywords
    - LOW: Appears in <33% of keywords
    """
    coverage = importance / total_keywords if total_keywords > 0 else 0
    
    if coverage > 0.66:
        return "HIGH"
    elif coverage >= 0.33:
        return "MEDIUM"
    else:
        return "LOW"


def rank_competitors(
    domain_scores: Dict[str, Dict[str, any]],
    total_keywords: int,
    top_n: int = 10
) -> List[Dict[str, any]]:
    """
    Rank competitors by importance and assign priority.
    
    Returns:
        List of top N competitors with priority buckets
    """
    # Add priority to each domain
    for domain, score in domain_scores.items():
        score["priority"] = assign_priority(score["importance"], total_keywords)
    
    # Sort by importance (descending), then alphabetically
    sorted_scores = sorted(
        domain_scores.values(),
        key=lambda x: (-x["importance"], x["domain"])
    )
    
    return sorted_scores[:top_n]


# ==================== Main Analysis Function ====================

async def analyze_competitors(
    keywords: List[str],
    google_cse_api_key: str,
    google_cse_cx: str,
    top_results_per_keyword: int = 10,
    final_top_competitors: int = 10,
    location: str = "India",
    language: str = "en"
) -> Dict[str, any]:
    """
    Analyze competitors for given keywords using Google CSE.
    
    This is the main entry point that replicates CompetitorPOC logic.
    
    Args:
        keywords: List of keywords to analyze (from Page 6)
        google_cse_api_key: Google Custom Search API key
        google_cse_cx: Google Custom Search Engine ID
        top_results_per_keyword: How many SERP results to fetch per keyword
        final_top_competitors: How many top competitors to return
        location: Geographic location for search
        language: Language code
        
    Returns:
        {
            "keywords_analyzed": int,
            "top_competitors": [
                {
                    "domain": str,
                    "importance": int,
                    "priority": "HIGH" | "MEDIUM" | "LOW",
                    "keywords_matched": [str]
                }
            ]
        }
    """
    # Validate input
    if not keywords:
        raise ValueError("Keywords list cannot be empty")
    
    # Remove duplicates and filter
    keywords = list(set([k.strip() for k in keywords if k.strip()]))
    
    logger.info(f"[Competitor Analysis] Analyzing {len(keywords)} keywords")
    
    # Initialize fetcher
    fetcher = GoogleCSEFetcher(google_cse_api_key, google_cse_cx)
    
    # Fetch SERP results for all keywords
    serp_results = {}
    for keyword in keywords:
        try:
            results = await fetcher.search(
                keyword,
                num_results=top_results_per_keyword,
                location=location,
                language=language
            )
            serp_results[keyword] = results
        except Exception as e:
            logger.error(f"[Competitor Analysis] Failed to fetch SERP for '{keyword}': {e}")
            serp_results[keyword] = []
    
    # Compute importance scores
    domain_scores = compute_domain_importance(serp_results)
    
    # Rank and assign priorities
    top_competitors = rank_competitors(
        domain_scores,
        total_keywords=len(keywords),
        top_n=final_top_competitors
    )
    
    logger.info(f"[Competitor Analysis] Found {len(top_competitors)} competitors")
    
    return {
        "keywords_analyzed": len(keywords),
        "top_competitors": top_competitors
    }
