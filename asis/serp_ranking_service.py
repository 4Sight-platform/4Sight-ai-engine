"""
SERP Ranking Service
Fetches keyword rankings for user and competitors from multiple SERP providers.
Supports: Google Custom Search API (primary), Serper.dev (fallback)
"""

import logging
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class SERPRankingService:
    """Service to fetch SERP rankings for keywords and competitors."""
    
    def __init__(self, api_key: str = None, cx: str = None, serper_api_key: str = None):
        """
        Initialize SERP Ranking Service with multiple provider support.
        
        Args:
            api_key: Google Custom Search API key (primary)
            cx: Custom Search Engine ID (for Google CSE)
            serper_api_key: Serper.dev API key (fallback)
        """
        self.google_cse_api_key = api_key
        self.google_cse_cx = cx
        self.serper_api_key = serper_api_key
        self.google_cse_base_url = "https://www.googleapis.com/customsearch/v1"
        self.serper_base_url = "https://google.serper.dev/search"
        
        # Determine primary provider
        if self.google_cse_api_key and self.google_cse_cx:
            self.primary_provider = "google_cse"
            logger.info("[SERP Ranking] Primary provider: Google Custom Search")
        elif self.serper_api_key:
            self.primary_provider = "serper"
            logger.info("[SERP Ranking] Primary provider: Serper.dev")
        else:
            self.primary_provider = None
            logger.warning("[SERP Ranking] No SERP provider configured!")
    
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        try:
            parsed = urlparse(url if url.startswith('http') else f'https://{url}')
            domain = parsed.netloc.replace('www.', '')
            return domain.lower()
        except:
            return url.lower()
    
    async def fetch_keyword_rankings(
        self,
        keywords: List[str],
        competitors: List[str],
        user_domain: str,
        location: str = "India",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Fetch SERP positions for keywords and competitors.
        
        Args:
            keywords: List of keywords to check
            competitors: List of competitor domains
            user_domain: User's domain
            location: Geographic location for search
            language: Language code
        
        Returns:
            {
                "keyword": {
                    "user_position": int or None,
                    "competitors": [{"domain": str, "position": int, "url": str}]
                }
            }
        """
        logger.info(f"[SERP Ranking] Fetching rankings for {len(keywords)} keywords using {self.primary_provider}")
        
        results = {}
        user_domain_clean = self._extract_domain(user_domain)
        competitor_domains_clean = [self._extract_domain(c) for c in competitors]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for keyword in keywords:
                try:
                    # Try primary provider first
                    if self.primary_provider == "google_cse":
                        keyword_results = await self._fetch_with_google_cse(
                            client, keyword, location, language
                        )
                    elif self.primary_provider == "serper":
                        keyword_results = await self._fetch_with_serper(
                            client, keyword, location
                        )
                    else:
                        logger.error("[SERP Ranking] No provider configured")
                        keyword_results = []
                    
                    # Extract positions
                    user_position = None
                    competitor_positions = []
                    
                    for idx, result in enumerate(keyword_results, 1):
                        result_domain = self._extract_domain(result.get('link', ''))
                        
                        # Check if it's the user's domain
                        if user_domain_clean in result_domain or result_domain in user_domain_clean:
                            if user_position is None:  # Take first occurrence
                                user_position = idx
                        
                        # Check if it's a competitor
                        for comp_domain in competitor_domains_clean:
                            if comp_domain in result_domain or result_domain in comp_domain:
                                competitor_positions.append({
                                    'domain': comp_domain,
                                    'position': idx,
                                    'url': result.get('link', ''),
                                    'title': result.get('title', '')
                                })
                                break  # Don't count same result multiple times
                    
                    results[keyword] = {
                        'user_position': user_position,
                        'competitors': competitor_positions
                    }
                    
                    logger.info(
                        f"[SERP Ranking] {keyword}: User #{user_position or '>100'}, "
                        f"Competitors: {len(competitor_positions)}"
                    )
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"[SERP Ranking] Error fetching {keyword}: {e}")
                    
                    # Try fallback provider if available
                    if self.primary_provider == "google_cse" and self.serper_api_key:
                        logger.info(f"[SERP Ranking] Trying fallback (Serper) for {keyword}")
                        try:
                            keyword_results = await self._fetch_with_serper(client, keyword, location)
                            # Process results (same logic as above)
                            user_position = None
                            competitor_positions = []
                            for idx, result in enumerate(keyword_results, 1):
                                result_domain = self._extract_domain(result.get('link', ''))
                                if user_domain_clean in result_domain or result_domain in user_domain_clean:
                                    if user_position is None:
                                        user_position = idx
                                for comp_domain in competitor_domains_clean:
                                    if comp_domain in result_domain or result_domain in comp_domain:
                                        competitor_positions.append({
                                            'domain': comp_domain,
                                            'position': idx,
                                            'url': result.get('link', ''),
                                            'title': result.get('title', '')
                                        })
                                        break
                            results[keyword] = {
                                'user_position': user_position,
                                'competitors': competitor_positions
                            }
                            logger.info(f"[SERP Ranking] Fallback successful for {keyword}")
                        except Exception as fallback_error:
                            logger.error(f"[SERP Ranking] Fallback also failed: {fallback_error}")
                            results[keyword] = {
                                'user_position': None,
                                'competitors': [],
                                'error': str(e)
                            }
                    else:
                        results[keyword] = {
                            'user_position': None,
                            'competitors': [],
                            'error': str(e)
                        }
        
        return results
    
    async def _fetch_with_google_cse(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        location: str,
        language: str
    ) -> List[Dict]:
        """Fetch SERP results using Google Custom Search API."""
        all_results = []
        num_pages = 10  # Fetch 100 results (10 pages)
        
        for page in range(num_pages):
            start_index = page * 10 + 1
            
            params = {
                'key': self.google_cse_api_key,
                'cx': self.google_cse_cx,
                'q': keyword,
                'num': 10,
                'start': start_index,
                'gl': 'in' if location == 'India' else 'us',
                'hl': language
            }
            
            try:
                response = await client.get(self.google_cse_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break  # No more results
                
                all_results.extend(items)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"[Google CSE] Rate limit hit for {keyword}")
                    raise  # Trigger fallback
                else:
                    logger.error(f"[Google CSE] HTTP error for {keyword}: {e}")
                    break
            except Exception as e:
                logger.error(f"[Google CSE] Error fetching page {page} for {keyword}: {e}")
                break
        
        return all_results
    
    async def _fetch_with_serper(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        location: str
    ) -> List[Dict]:
        """Fetch SERP results using Serper.dev API."""
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': keyword,
            'gl': 'in' if location == 'India' else 'us',
            'num': 100  # Fetch 100 results
        }
        
        try:
            response = await client.post(
                self.serper_base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract organic results
            organic_results = data.get('organic', [])
            
            # Convert to Google CSE format for consistency
            formatted_results = []
            for result in organic_results:
                formatted_results.append({
                    'link': result.get('link', ''),
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', '')
                })
            
            logger.info(f"[Serper] Fetched {len(formatted_results)} results for {keyword}")
            return formatted_results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[Serper] HTTP error for {keyword}: {e}")
            raise
        except Exception as e:
            logger.error(f"[Serper] Error fetching {keyword}: {e}")
            raise
