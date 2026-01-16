"""
Universal Competitor Analysis Module for Onboarding
Enhanced with meta description extraction and multi-layer junk filtering
Works for ANY industry with accurate business similarity validation
"""

import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse
from collections import defaultdict
import httpx
import re

logger = logging.getLogger(__name__)

# ==================== Junk Domain Filtering ====================

# Comprehensive junk domain list
JUNK_DOMAINS = {
    # Social Media
    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
    'youtube.com', 'tiktok.com', 'pinterest.com', 'reddit.com',
    
    # Directories & Listings
    'justdial.com', 'yelp.com', 'yellowpages.com', 'sulekha.com',
    'indiamart.com', 'tradeindia.com', 'exportersindia.com',
    
    # Job Boards
    'indeed.com', 'naukri.com', 'monster.com', 'glassdoor.com',
    
    # Freelance Platforms
    'upwork.com', 'fiverr.com', 'freelancer.com', 'guru.com',
    
    # Review/Comparison Sites
    'clutch.co', 'goodfirms.co', 'trustpilot.com', 'g2.com',
    'capterra.com', 'softwareadvice.com',
    
    # Content/Educational Platforms
    'wikipedia.org', 'medium.com', 'quora.com', 'coursera.org',
    'udemy.com', 'edx.org', 'investopedia.com', 'hubspot.com',
    
    # News/Media
    'forbes.com', 'entrepreneur.com', 'inc.com', 'businessinsider.com',
    
    # E-commerce Platforms
    'amazon.com', 'flipkart.com', 'ebay.com', 'etsy.com',
    
    # Food Delivery
    'zomato.com', 'swiggy.com', 'ubereats.com', 'doordash.com',
    
    # Tech Giants
    'google.com', 'microsoft.com', 'apple.com', 'adobe.com',
    'salesforce.com', 'oracle.com', 'ibm.com',
    
    # Government/Educational
    'gov.in', 'nic.in', 'india.gov.in',
}

# Educational TLDs
EDUCATIONAL_TLDS = {'.edu', '.ac.in', '.ac.uk', '.edu.in'}

# Content subdomain patterns
CONTENT_SUBDOMAINS = {'blog', 'news', 'resources', 'learn', 'academy', 'help', 'support', 'docs', 'wiki', 'developers', 'developer', 'api'}


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


def is_junk_domain(url: str) -> tuple[bool, str]:
    """
    Check if domain is junk using multi-layer filtering
    Returns: (is_junk, reason)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')
    
    # Check hardcoded junk list
    for junk in JUNK_DOMAINS:
        if junk in domain:
            return True, f"Known platform: {junk}"
    
    # Check educational TLDs
    for tld in EDUCATIONAL_TLDS:
        if domain.endswith(tld):
            return True, "Educational institution"
    
    # Check content subdomains
    subdomain = domain.split('.')[0] if '.' in domain else ''
    if subdomain in CONTENT_SUBDOMAINS:
        return True, f"Content subdomain: {subdomain}"
    
    return False, ""


# ==================== Business Description Extraction ====================

async def extract_business_description(url: str, timeout: int = 10) -> Dict:
    """
    Extract accurate business description from website
    Priority: Meta description > OG description > Title
    """
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            
            # Extract meta description (most accurate)
            meta_desc = ''
            meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if meta_match:
                meta_desc = meta_match.group(1).strip()
            
            # Extract OG description as fallback
            og_desc = ''
            og_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if og_match:
                og_desc = og_match.group(1).strip()
            
            # Extract title
            title = ''
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            
            # Use meta description as primary, fallback to OG, then title
            description = meta_desc or og_desc or title
            
            # Extract business keywords from description
            business_keywords = extract_business_keywords(description)
            
            return {
                'url': url,
                'domain': extract_root_domain(url),
                'title': title,
                'description': description,
                'keywords': business_keywords,
                'accessible': True
            }
    
    except Exception as e:
        logger.warning(f"[Business Analysis] Could not access {url}: {e}")
        return {
            'url': url,
            'domain': extract_root_domain(url),
            'accessible': False,
            'error': str(e)
        }


def extract_business_keywords(text: str) -> Set[str]:
    """
    Extract meaningful business keywords from text
    Industry-agnostic approach
    """
    if not text:
        return set()
    
    text_lower = text.lower()
    keywords = set()
    
    # Remove HTML entities
    text_lower = re.sub(r'&[a-z]+;', ' ', text_lower)
    
    # Extract all words (2+ chars)
    words = re.findall(r'\b[a-z]{2,}\b', text_lower)
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'we', 'our', 'your', 'this', 'that', 'it', 'as', 'into', 'about',
        'has', 'have', 'had', 'will', 'can', 'may', 'also', 'more', 'than',
        'very', 'just', 'only', 'some', 'all', 'any', 'each', 'every', 'both'
    }
    
    # Keep meaningful words (3+ chars, not stop words)
    for word in words:
        if len(word) >= 3 and word not in stop_words:
            keywords.add(word)
    
    return keywords


# ==================== Similarity Validation ====================

# Industry/domain keywords that indicate business type
BUSINESS_DOMAIN_KEYWORDS = {
    # Marketing/Advertising
    'marketing', 'advertising', 'digital', 'social', 'media', 'seo', 'sem',
    'branding', 'campaign', 'content', 'analytics', 'strategy',
    
    # Development/Tech
    'development', 'developer', 'software', 'web', 'app', 'mobile', 'tech',
    'programming', 'coding', 'design', 'website', 'platform',
    
    # Business Services
    'consulting', 'consultant', 'agency', 'services', 'solutions', 'business',
    'professional', 'expert', 'specialist', 'company', 'firm',
    
    # E-commerce/Retail
    'shop', 'store', 'ecommerce', 'retail', 'products', 'shopping', 'online',
    'marketplace', 'seller', 'merchant',
    
    # Food/Hospitality
    'restaurant', 'cafe', 'bakery', 'food', 'dining', 'catering', 'kitchen',
    'chef', 'menu', 'cuisine', 'hotel', 'hospitality',
    
    # Healthcare
    'health', 'medical', 'clinic', 'hospital', 'doctor', 'healthcare',
    'wellness', 'therapy', 'treatment',
    
    # Education
    'education', 'training', 'learning', 'course', 'school', 'academy',
    'teaching', 'instructor', 'tutor',
    
    # Finance
    'finance', 'financial', 'accounting', 'investment', 'banking', 'insurance',
    'tax', 'wealth', 'money',
}


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Simplified similarity check focusing on business domain keywords
    Returns: 0.0 to 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    keywords1 = extract_business_keywords(text1)
    keywords2 = extract_business_keywords(text2)
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Extract domain-specific keywords
    domain_kw1 = keywords1 & BUSINESS_DOMAIN_KEYWORDS
    domain_kw2 = keywords2 & BUSINESS_DOMAIN_KEYWORDS
    
    # If both have domain keywords, check overlap
    if domain_kw1 and domain_kw2:
        domain_overlap = len(domain_kw1 & domain_kw2)
        domain_union = len(domain_kw1 | domain_kw2)
        domain_similarity = domain_overlap / domain_union if domain_union > 0 else 0.0
        
        # If they share domain keywords, boost similarity
        if domain_similarity > 0:
            # Also check general keyword overlap
            general_overlap = len(keywords1 & keywords2)
            general_union = len(keywords1 | keywords2)
            general_similarity = general_overlap / general_union if general_union > 0 else 0.0
            
            # Weighted: 70% domain keywords, 30% general keywords
            return (domain_similarity * 0.7) + (general_similarity * 0.3)
    
    # Fallback: simple Jaccard similarity
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    
    return intersection / union if union > 0 else 0.0



# ==================== SERP Fetching ====================

class BaseFetcher:
    """Base class for SERP fetchers"""
    async def search(self, keyword: str, num_results: int, location: str, language: str) -> List[Dict]:
        raise NotImplementedError


class GoogleCSEFetcher(BaseFetcher):
    """Google Custom Search Engine fetcher"""
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx
    
    async def search(self, keyword: str, num_results: int = 10, location: str = "India", language: str = "en") -> List[Dict]:
        if not self.api_key or not self.cx:
            raise ValueError("Google CSE not configured")
            
        num = min(num_results, 10)
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": keyword,
            "num": num,
            "hl": language,
            "gl": self._map_location(location),
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
        results = []
        for idx, item in enumerate(data.get("items", []), start=1):
            if item.get("link"):
                results.append({
                    "rank": idx,
                    "url": item.get("link"),
                    "domain": extract_root_domain(item.get("link")),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                })
        return results

    @staticmethod
    def _map_location(location: str) -> str:
        location_map = {"india": "in", "united states": "us", "usa": "us", "uk": "uk", "united kingdom": "uk", "germany": "de", "france": "fr", "australia": "au", "canada": "ca"}
        return location_map.get(location.lower(), "in")


class SerpApiFetcher(BaseFetcher):
    """SerpApi.com fetcher"""
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def search(self, keyword: str, num_results: int = 10, location: str = "India", language: str = "en") -> List[Dict]:
        if not self.api_key:
            raise ValueError("SerpApi not configured")
            
        params = {
            "api_key": self.api_key,
            "q": keyword,
            "num": num_results,
            "hl": language,
            "gl": GoogleCSEFetcher._map_location(location),
            "google_domain": "google.com",
            "engine": "google"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
        results = []
        for idx, item in enumerate(data.get("organic_results", []), start=1):
            if item.get("link"):
                results.append({
                    "rank": item.get("position", idx),
                    "url": item.get("link"),
                    "domain": extract_root_domain(item.get("link")),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                })
        return results


class SerperDevFetcher(BaseFetcher):
    """Serper.dev fetcher"""
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def search(self, keyword: str, num_results: int = 10, location: str = "India", language: str = "en") -> List[Dict]:
        if not self.api_key:
            raise ValueError("Serper.dev not configured")
            
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": keyword,
            "num": num_results,
            "gl": GoogleCSEFetcher._map_location(location),
            "hl": language
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
        results = []
        for idx, item in enumerate(data.get("organic", []), start=1):
            if item.get("link"):
                results.append({
                    "rank": item.get("position", idx),
                    "url": item.get("link"),
                    "domain": extract_root_domain(item.get("link")),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                })
        return results


# ==================== Competitor Discovery & Scoring ====================

async def discover_and_score_competitors(
    serp_results: Dict[str, List[Dict]],
    user_domain: str,
    user_description: str,
    min_similarity: float = 0.10
) -> Dict[str, Dict]:
    """
    Discover competitors with intelligent filtering and similarity validation
    
    Args:
        serp_results: Dict mapping keyword → list of SERP result dicts
        user_domain: User's domain to exclude
        user_description: User's business description for similarity check
        min_similarity: Minimum similarity threshold (0.15 = 15%)
    
    Returns:
        Dict mapping domain → competitor data with scores
    """
    competitors = {}
    filtered_stats = defaultdict(int)
    
    for keyword, results in serp_results.items():
        for result in results:
            url = result.get("url", "")
            domain = result.get("domain", "")
            snippet = result.get("snippet", "")
            
            # Skip user's own domain
            if domain == user_domain:
                continue
            
            # Check junk domains
            is_junk, junk_reason = is_junk_domain(url)
            if is_junk:
                filtered_stats[junk_reason] += 1
                logger.debug(f"[Filter] {domain} - {junk_reason}")
                continue
            
            # Similarity validation (only if user description is available)
            if user_description:
                similarity = calculate_similarity(user_description, snippet)
                
                if similarity < min_similarity:
                    filtered_stats['Low similarity'] += 1
                    logger.debug(f"[Filter] {domain} - Low similarity ({similarity:.0%})")
                    continue
            else:
                # No user description available - skip similarity check
                similarity = 0.5  # Default moderate similarity
            
            
            # Keep as competitor
            if domain not in competitors:
                competitors[domain] = {
                    'domain': domain,
                    'urls': set(),
                    'keywords': set(),
                    'titles': set(),
                    'snippets': set(),
                    'positions': [],
                    'frequency': 0,
                    'similarity': similarity,
                }
            
            competitors[domain]['urls'].add(url)
            competitors[domain]['keywords'].add(keyword)
            competitors[domain]['titles'].add(result.get('title', ''))
            competitors[domain]['snippets'].add(snippet)
            competitors[domain]['positions'].append(result.get('rank', 0))
            competitors[domain]['frequency'] += 1
            
            # Update similarity if higher
            if similarity > competitors[domain]['similarity']:
                competitors[domain]['similarity'] = similarity
    
    # Log filtering stats
    if filtered_stats:
        logger.info(f"[Competitor Analysis] Filtering summary:")
        for reason, count in sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  • {reason}: {count}")
    
    return competitors


def score_and_rank_competitors(
    competitors: Dict[str, Dict],
    total_keywords: int,
    top_n: int = 10
) -> List[Dict]:
    """
    Score competitors based on multiple factors and rank them
    
    Scoring Algorithm:
    - Frequency (30 points): How often they appear
    - Coverage (25 points): Percentage of keywords matched
    - Similarity (35 points): Business similarity to user
    - Position (10 points): SERP ranking bonus
    """
    scored = []
    
    for domain, data in competitors.items():
        score = 0
        
        # Frequency score (30 points)
        freq_score = min(data['frequency'] * 5, 30)
        score += freq_score
        
        # Coverage score (25 points)
        coverage = len(data['keywords']) / total_keywords if total_keywords > 0 else 0
        coverage_score = coverage * 25
        score += coverage_score
        
        # Similarity score (35 points) - MOST IMPORTANT
        similarity_score = data['similarity'] * 35
        score += similarity_score
        
        # Position bonus (10 points)
        if data['positions']:
            avg_pos = sum(data['positions']) / len(data['positions'])
            position_bonus = max(0, 10 - avg_pos)
            score += position_bonus
        else:
            avg_pos = 0
        
        # Assign priority bucket
        if score >= 70:
            priority = "CRITICAL"
        elif score >= 50:
            priority = "HIGH"
        elif score >= 30:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        scored.append({
            'domain': domain,
            'score': round(score, 2),
            'priority': priority,
            'frequency': data['frequency'],
            'coverage': round(coverage * 100, 1),
            'similarity': round(data['similarity'] * 100, 1),
            'keywords_matched': list(data['keywords']),
            'avg_position': round(avg_pos, 1) if avg_pos > 0 else 0,
        })
    
    # Sort by score (descending)
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    return scored[:top_n]


# ==================== Main Analysis Function ====================

async def analyze_competitors(
    keywords: List[str],
    google_cse_api_key: str,
    google_cse_cx: str,
    user_url: Optional[str] = None,
    top_results_per_keyword: int = 10,
    final_top_competitors: int = 10,
    location: str = "India",
    language: str = "en",
    min_similarity: float = 0.10,
    serp_api_key: Optional[str] = None,
    serper_api_key: Optional[str] = None
) -> Dict[str, any]:
    """
    Universal competitor analysis with business similarity validation.
    
    Args:
        keywords: List of keywords to analyze (from Page 6)
        google_cse_api_key: Google Custom Search API key
        google_cse_cx: Google Custom Search Engine ID
        user_url: User's website URL (for business description extraction)
        top_results_per_keyword: How many SERP results to fetch per keyword
        final_top_competitors: How many top competitors to return
        location: Geographic location for search
        language: Language code
        min_similarity: Minimum similarity threshold (0.15 = 15%)
        serp_api_key: Fallback 1 - SerpApi Key
        serper_api_key: Fallback 2 - Serper.dev Key
        
    Returns:
        Dict with competitor data
    """
    # Validate input
    if not keywords:
        raise ValueError("Keywords list cannot be empty")
    
    # Remove duplicates and filter
    keywords = list(set([k.strip() for k in keywords if k.strip()]))
    
    logger.info(f"[Competitor Analysis] Analyzing {len(keywords)} keywords")
    
    # Extract user's business description if URL provided
    user_business = None
    user_domain = ""
    user_description = ""
    
    if user_url:
        logger.info(f"[Competitor Analysis] Extracting business description from {user_url}")
        user_business = await extract_business_description(user_url)
        
        if user_business.get('accessible'):
            user_domain = user_business['domain']
            user_description = user_business['description']
            logger.info(f"[Competitor Analysis] User business: {user_domain}")
            logger.info(f"[Competitor Analysis] Description: {user_description[:100]}...")
        else:
            logger.warning(f"[Competitor Analysis] Could not access user website, proceeding without similarity validation")
    
    # Initialize fetchers
    fetchers = []
    
    # 1. Google CSE (Primary)
    if google_cse_api_key and google_cse_cx:
        fetchers.append(("Google CSE", GoogleCSEFetcher(google_cse_api_key, google_cse_cx)))
    
    # 2. SerpApi (Fallback 1)
    if serp_api_key:
        fetchers.append(("SerpApi", SerpApiFetcher(serp_api_key)))
        
    # 3. Serper.dev (Fallback 2)
    if serper_api_key:
        fetchers.append(("Serper.dev", SerperDevFetcher(serper_api_key)))
        
    if not fetchers:
        raise ValueError("No search APIs configured (CSE, SerpApi, or Serper)")

    # Fetch SERP results for all keywords using fallback logic per keyword OR globally
    # Strategy: Try primary for all. If it fails (globally or 429), switch to next for ALL remaining.
    
    serp_results = {}
    active_fetcher_idx = 0
    
    # Try using the active fetcher for all keywords. If it fails, switch to next.
    
    while active_fetcher_idx < len(fetchers):
        fetcher_name, fetcher_svc = fetchers[active_fetcher_idx]
        logger.info(f"[Competitor Analysis] Using search provider: {fetcher_name}")
        
        failed_keywords = [k for k in keywords if k not in serp_results]
        if not failed_keywords:
            break
            
        success_count = 0
        error_encountered = False
        
        for keyword in failed_keywords:
            try:
                results = await fetcher_svc.search(
                    keyword,
                    num_results=top_results_per_keyword,
                    location=location,
                    language=language
                )
                serp_results[keyword] = results
                success_count += 1
            except Exception as e:
                logger.error(f"[Competitor Analysis] {fetcher_name} failed for '{keyword}': {e}")
                # If it's a 429 or configured error, we might want to switch provider immediately
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning(f"[Competitor Analysis] {fetcher_name} quota exceeded. Switching to fallback...")
                    error_encountered = True
                    break
        
        if error_encountered or success_count < len(failed_keywords):
            # Move to next fetcher
            active_fetcher_idx += 1
        else:
            # All done
            break
            
    if not serp_results:
        logger.error("[Competitor Analysis] All search providers failed.")
        return {
            "keywords_analyzed": 0,
            "top_competitors": [],
            "total_found": 0,
        }

    # Discover competitors with filtering and similarity validation
    competitors = await discover_and_score_competitors(
        serp_results,
        user_domain,
        user_description,
        min_similarity
    )
    
    # Score and rank competitors
    top_competitors = score_and_rank_competitors(
        competitors,
        total_keywords=len(keywords),
        top_n=final_top_competitors
    )
    
    logger.info(f"[Competitor Analysis] Found {len(top_competitors)} top competitors from {len(serp_results)} keywords")
    
    return {
        "keywords_analyzed": len(keywords),
        "user_business": {
            "domain": user_domain,
            "description": user_description,
            "accessible": user_business.get('accessible', False) if user_business else False
        } if user_business else None,
        "top_competitors": top_competitors,
        "total_found": len(competitors),
        "total_filtered": sum(1 for kw_results in serp_results.values() for _ in kw_results) - len(competitors)
    }
