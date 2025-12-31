"""
Crawler Service
Web crawler for extracting on-page SEO signals from priority URLs
"""

import logging
import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime

logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Web crawler for priority URLs that extracts:
    - Title tag, meta description
    - H1-H6 heading structure
    - First 100 visible words
    - Canonical tags
    - Internal/external links
    - Images with alt text analysis
    - URL properties
    """
    
    # User agent for crawling
    USER_AGENT = "4SightBot/1.0 (+https://4sight.ai/bot)"
    
    # Request timeout
    TIMEOUT = 30.0
    
    # Known AI crawler user-agents to check in robots.txt
    AI_CRAWLERS = [
        "GPTBot",
        "ChatGPT-User", 
        "Google-Extended",
        "CCBot",
        "anthropic-ai",
        "ClaudeBot",
        "Bytespider",
        "PerplexityBot"
    ]
    
    def __init__(self):
        self.headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single page and extract SEO signals.
        
        Args:
            url: URL to crawl
            
        Returns:
            Dict with all extracted signals
        """
        result = {
            "url": url,
            "crawl_status": "pending",
            "http_status": None,
            "crawled_at": datetime.now().isoformat(),
            "signals": {}
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)
                result["http_status"] = response.status_code
                
                if response.status_code != 200:
                    result["crawl_status"] = "failed"
                    result["error"] = f"HTTP {response.status_code}"
                    return result
                
                # Parse HTML
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract all signals
                result["signals"] = {
                    **self._extract_title(soup),
                    **self._extract_meta_description(soup),
                    **self._extract_headings(soup),
                    **self._extract_canonical(soup, url),
                    **self._extract_content(soup),
                    **self._extract_links(soup, url),
                    **self._extract_images(soup),
                    **self._extract_url_properties(url),
                }
                
                result["crawl_status"] = "success"
                
        except httpx.TimeoutException:
            result["crawl_status"] = "timeout"
            result["error"] = "Request timed out"
        except Exception as e:
            result["crawl_status"] = "failed"
            result["error"] = str(e)
            logger.error(f"[Crawler] Error crawling {url}: {e}")
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> Dict:
        """Extract title tag."""
        title_tag = soup.find('title')
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        
        return {
            "title_tag": title_text,
            "title_length": len(title_text)
        }
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Dict:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc_content = meta_desc.get('content', '').strip() if meta_desc else ""
        
        return {
            "meta_description": desc_content,
            "meta_description_length": len(desc_content)
        }
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict:
        """Extract heading hierarchy with order validation."""
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        
        h1_texts = [h.get_text(strip=True) for h in h1_tags]
        h2_texts = [h.get_text(strip=True) for h in h2_tags]
        h3_texts = [h.get_text(strip=True) for h in h3_tags]
        
        # Check for empty headings
        empty_headings = sum(1 for h in h1_texts + h2_texts + h3_texts if not h)
        
        # Check for duplicate headings
        all_headings = h1_texts + h2_texts + h3_texts
        duplicate_headings = len(all_headings) - len(set(all_headings))
        
        # Check heading order (H1 should come before H2, H2 before H3)
        heading_order_valid = True
        if h1_tags and h2_tags:
            first_h1_pos = str(soup).find(str(h1_tags[0]))
            first_h2_pos = str(soup).find(str(h2_tags[0]))
            if first_h2_pos < first_h1_pos:
                heading_order_valid = False
        
        return {
            "h1_count": len(h1_tags),
            "h1_text": h1_texts[0] if h1_texts else "",
            "h1_all": h1_texts,
            "h2_count": len(h2_tags),
            "h2_texts": h2_texts[:10],  # Limit for storage
            "h3_count": len(h3_tags),
            "h4_count": len(soup.find_all('h4')),
            "h5_count": len(soup.find_all('h5')),
            "h6_count": len(soup.find_all('h6')),
            "empty_headings": empty_headings,
            "duplicate_headings": duplicate_headings,
            "heading_order_valid": heading_order_valid
        }
    
    def _extract_canonical(self, soup: BeautifulSoup, current_url: str) -> Dict:
        """Extract canonical tag information."""
        canonical = soup.find('link', rel='canonical')
        canonical_url = canonical.get('href', '').strip() if canonical else ""
        
        # Normalize URLs for comparison
        current_parsed = urlparse(current_url)
        canonical_parsed = urlparse(canonical_url) if canonical_url else None
        
        # Check if self-referencing
        self_referencing = False
        if canonical_parsed:
            self_referencing = (
                current_parsed.netloc == canonical_parsed.netloc and
                current_parsed.path.rstrip('/') == canonical_parsed.path.rstrip('/')
            )
        
        return {
            "canonical_url": canonical_url,
            "canonical_self_referencing": self_referencing
        }
    
    def _extract_content(self, soup: BeautifulSoup) -> Dict:
        """Extract content signals (first 100 words, word count)."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Count words
        words = text.split()
        word_count = len(words)
        
        # First 100 words
        first_100 = ' '.join(words[:100])
        
        return {
            "first_100_words": first_100,
            "word_count": word_count
        }
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Extract internal and external links."""
        base_domain = urlparse(base_url).netloc.replace('www.', '')
        
        internal_links = []
        external_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Make absolute URL
            absolute_url = urljoin(base_url, href)
            link_domain = urlparse(absolute_url).netloc.replace('www.', '')
            
            if base_domain in link_domain:
                internal_links.append(absolute_url)
            else:
                external_links.append(absolute_url)
        
        return {
            "internal_link_count": len(internal_links),
            "external_link_count": len(external_links),
            "internal_links": internal_links[:50],  # Limit for storage
            "external_links": external_links[:20]
        }
    
    def _extract_images(self, soup: BeautifulSoup) -> Dict:
        """Extract image signals with lazy loading and alt quality."""
        images = soup.find_all('img')
        
        with_alt = 0
        without_alt = 0
        with_lazy_loading = 0
        generic_alt_count = 0
        
        # Generic alt text patterns
        generic_patterns = ['image', 'photo', 'picture', 'img', 'banner', 'logo', 'icon']
        
        for img in images:
            alt = img.get('alt', '').strip()
            
            if alt:
                with_alt += 1
                # Check for generic alt text
                if alt.lower() in generic_patterns or len(alt) < 5:
                    generic_alt_count += 1
            else:
                without_alt += 1
            
            # Check for lazy loading
            if img.get('loading') == 'lazy':
                with_lazy_loading += 1
        
        return {
            "image_count": len(images),
            "images_with_alt": with_alt,
            "images_without_alt": without_alt,
            "images_with_lazy_loading": with_lazy_loading,
            "images_with_generic_alt": generic_alt_count,
            "lazy_loading_ratio": with_lazy_loading / len(images) if images else 0,
            "alt_quality_ratio": (with_alt - generic_alt_count) / len(images) if images else 0
        }
    
    def _extract_url_properties(self, url: str) -> Dict:
        """Extract URL-level signals."""
        parsed = urlparse(url)
        path = parsed.path
        
        # URL depth (number of path segments)
        segments = [s for s in path.split('/') if s]
        depth = len(segments)
        
        # Has query parameters
        has_params = bool(parsed.query)
        
        return {
            "url_length": len(url),
            "url_has_parameters": has_params,
            "url_depth": depth
        }
    
    async def crawl_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Crawl multiple URLs.
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of crawl results
        """
        results = []
        for url in urls:
            result = await self.crawl_page(url)
            results.append(result)
        
        return results
    
    async def check_robots_txt(self, domain: str) -> Dict[str, Any]:
        """
        Check robots.txt for the domain.
        
        Args:
            domain: Domain to check (e.g., example.com)
            
        Returns:
            Dict with robots.txt info including AI crawler rules
        """
        robots_url = f"https://{domain}/robots.txt"
        
        result = {
            "robots_exists": False,
            "robots_valid": False,
            "ai_crawlers_blocked": [],
            "ai_crawlers_allowed": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(robots_url, headers=self.headers)
                
                if response.status_code == 200:
                    result["robots_exists"] = True
                    content = response.text.lower()
                    
                    # Check for AI crawlers
                    for crawler in self.AI_CRAWLERS:
                        crawler_lower = crawler.lower()
                        
                        # Look for user-agent directives
                        if f"user-agent: {crawler_lower}" in content:
                            # Check if followed by disallow: /
                            lines = content.split('\n')
                            in_agent_block = False
                            
                            for line in lines:
                                line = line.strip()
                                if line.startswith('user-agent:'):
                                    agent = line.replace('user-agent:', '').strip()
                                    in_agent_block = crawler_lower in agent or agent == '*'
                                elif in_agent_block and line.startswith('disallow:'):
                                    disallow_path = line.replace('disallow:', '').strip()
                                    if disallow_path == '/':
                                        if crawler not in result["ai_crawlers_blocked"]:
                                            result["ai_crawlers_blocked"].append(crawler)
                                elif in_agent_block and line.startswith('allow:'):
                                    if crawler not in result["ai_crawlers_allowed"]:
                                        result["ai_crawlers_allowed"].append(crawler)
                    
                    result["robots_valid"] = True
                    
        except Exception as e:
            logger.error(f"[Crawler] Error checking robots.txt for {domain}: {e}")
        
        return result
    
    async def check_llm_txt(self, domain: str) -> Dict[str, Any]:
        """
        Check for llm.txt file (emerging standard for AI crawler instructions).
        
        Args:
            domain: Domain to check
            
        Returns:
            Dict with llm.txt detection results
        """
        llm_url = f"https://{domain}/llm.txt"
        
        result = {
            "llm_txt_detected": False,
            "llm_txt_content": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(llm_url, headers=self.headers)
                
                if response.status_code == 200:
                    result["llm_txt_detected"] = True
                    result["llm_txt_content"] = response.text[:2000]  # Limit content stored
                    
        except Exception as e:
            logger.debug(f"[Crawler] llm.txt not found for {domain}: {e}")
        
        return result
    
    def _extract_meta_robots(self, soup: BeautifulSoup) -> Dict:
        """Extract meta robots directives."""
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        content = robots_meta.get('content', '').lower() if robots_meta else ""
        
        return {
            "meta_robots": content,
            "is_noindex": 'noindex' in content,
            "is_nofollow": 'nofollow' in content,
            "is_indexable": 'noindex' not in content
        }
    
    def _extract_schema(self, soup: BeautifulSoup) -> Dict:
        """Extract schema.org structured data."""
        import json
        schema_scripts = soup.find_all('script', type='application/ld+json')
        
        schemas_found = []
        has_organization = False
        has_article = False
        has_product = False
        has_faq = False
        has_breadcrumb = False
        
        for script in schema_scripts:
            try:
                data = json.loads(script.string or '{}')
                
                # Get @type (can be string or list)
                schema_type = data.get('@type', '')
                if isinstance(schema_type, list):
                    schema_types = schema_type
                else:
                    schema_types = [schema_type]
                
                schemas_found.extend(schema_types)
                
                for t in schema_types:
                    t_lower = t.lower()
                    if 'organization' in t_lower:
                        has_organization = True
                    if 'article' in t_lower or 'blogpost' in t_lower:
                        has_article = True
                    if 'product' in t_lower:
                        has_product = True
                    if 'faq' in t_lower:
                        has_faq = True
                    if 'breadcrumb' in t_lower:
                        has_breadcrumb = True
                        
            except:
                continue
        
        return {
            "has_schema": len(schemas_found) > 0,
            "schema_types": schemas_found[:10],
            "has_organization_schema": has_organization,
            "has_article_schema": has_article,
            "has_product_schema": has_product,
            "has_faq_schema": has_faq,
            "has_breadcrumb_schema": has_breadcrumb,
            "rich_result_eligible": has_faq or has_product or has_article or has_breadcrumb
        }
