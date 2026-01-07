"""
Backlink Analyzer Service
Crawls linking domains to extract follow/nofollow, anchor text, and authority estimates
"""

import logging
import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


class BacklinkAnalyzer:
    """
    Analyzes backlinks by crawling linking domains.
    
    Provides:
    - Follow/Nofollow ratio
    - Anchor text distribution
    - Authority estimates (heuristic-based)
    """
    
    USER_AGENT = "4SightBot/1.0 (+https://4sight.ai/bot)"
    TIMEOUT = 15.0
    
    # High-authority domains (tier-based scoring)
    AUTHORITY_TIERS = {
        # Tier 1: Top-tier authority (90+)
        "tier1": [
            "wikipedia.org", "nytimes.com", "wsj.com", "bbc.com", "cnn.com",
            "forbes.com", "bloomberg.com", "reuters.com", "theguardian.com",
            "washingtonpost.com", "huffpost.com", "time.com", "businessinsider.com"
        ],
        # Tier 2: High authority (75-89)
        "tier2": [
            "techcrunch.com", "wired.com", "theverge.com", "arstechnica.com",
            "cnet.com", "zdnet.com", "mashable.com", "venturebeat.com",
            "medium.com", "linkedin.com", "github.com", "stackoverflow.com",
            "producthunt.com", "hackernews.com", "reddit.com"
        ],
        # Tier 3: Good authority (60-74)
        "tier3": [
            "dev.to", "hashnode.com", "substack.com", "quora.com",
            "twitter.com", "facebook.com", "youtube.com", "instagram.com"
        ]
    }
    
    # TLD-based authority boost
    AUTHORITY_TLDS = {
        ".gov": 90,
        ".edu": 85,
        ".org": 60,
        ".mil": 90
    }
    
    def __init__(self):
        self.headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }
    
    async def analyze_backlinks(
        self,
        target_domain: str,
        linking_domains: List[str],
        max_domains: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze backlinks from a list of linking domains.
        
        Args:
            target_domain: The domain we're analyzing backlinks for
            linking_domains: List of domains that link to us
            max_domains: Maximum domains to crawl
            
        Returns:
            Dict with backlink analysis results
        """
        results = {
            "target_domain": target_domain,
            "domains_analyzed": 0,
            "dofollow_count": 0,
            "nofollow_count": 0,
            "dofollow_ratio": 0.0,
            "anchor_distribution": {
                "branded": 0,
                "exact_match": 0,
                "partial_match": 0,
                "generic": 0,
                "url": 0,
                "other": 0
            },
            "authority_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "avg_authority_score": 0,
            "links_found": [],
            "errors": []
        }
        
        total_authority = 0
        
        for domain in linking_domains[:max_domains]:
            try:
                link_data = await self._analyze_single_domain(target_domain, domain)
                
                if link_data.get("link_found"):
                    results["domains_analyzed"] += 1
                    
                    # Follow/Nofollow
                    if link_data.get("is_dofollow"):
                        results["dofollow_count"] += 1
                    else:
                        results["nofollow_count"] += 1
                    
                    # Anchor text
                    anchor_type = link_data.get("anchor_type", "other")
                    if anchor_type in results["anchor_distribution"]:
                        results["anchor_distribution"][anchor_type] += 1
                    
                    # Authority
                    authority = link_data.get("authority_score", 50)
                    total_authority += authority
                    
                    if authority >= 75:
                        results["authority_distribution"]["high"] += 1
                    elif authority >= 50:
                        results["authority_distribution"]["medium"] += 1
                    else:
                        results["authority_distribution"]["low"] += 1
                    
                    results["links_found"].append(link_data)
                    
            except Exception as e:
                results["errors"].append({"domain": domain, "error": str(e)})
                logger.error(f"[Backlink] Error analyzing {domain}: {e}")
        
        # Calculate ratios
        total_links = results["dofollow_count"] + results["nofollow_count"]
        if total_links > 0:
            results["dofollow_ratio"] = results["dofollow_count"] / total_links
            results["avg_authority_score"] = total_authority / total_links
        
        return results
    
    def calculate_spam_score(
        self,
        analysis: Dict[str, Any],
        linking_domains: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate spam score based on link quality heuristics.
        
        Args:
            analysis: Backlink analysis results
            linking_domains: List of linking domains
            
        Returns:
            Spam score analysis
        """
        spam_indicators = 0
        max_indicators = 10
        
        dofollow_ratio = analysis.get("dofollow_ratio", 0.5)
        anchor_dist = analysis.get("anchor_distribution", {})
        exact_match = anchor_dist.get("exact_match", 0)
        total_anchors = sum(anchor_dist.values()) if anchor_dist else 0
        
        # Indicator 1: Excessive dofollow links (>95% suspicious)
        if dofollow_ratio > 0.95:
            spam_indicators += 2
        
        # Indicator 2: Excessive exact-match anchors (>30%)
        if total_anchors > 0 and (exact_match / total_anchors) > 0.3:
            spam_indicators += 2
        
        # Indicator 3: Low authority domains
        auth_dist = analysis.get("authority_distribution", {})
        low_auth = auth_dist.get("low", 0)
        total_analyzed = analysis.get("domains_analyzed", 1)
        if total_analyzed > 0 and (low_auth / total_analyzed) > 0.7:
            spam_indicators += 2
        
        # Indicator 4: Suspicious TLDs
        suspicious_tlds = ['.info', '.biz', '.xyz', '.top', '.win']
        suspicious_count = sum(
            1 for domain in linking_domains 
            if any(domain.endswith(tld) for tld in suspicious_tlds)
        )
        if len(linking_domains) > 0 and (suspicious_count / len(linking_domains)) > 0.2:
            spam_indicators += 2
        
        # Indicator 5: Very short domain names (often spam)
        short_domains = sum(
            1 for domain in linking_domains
            if len(domain.split('.')[0]) < 4
        )
        if len(linking_domains) > 0 and (short_domains / len(linking_domains)) > 0.3:
            spam_indicators += 2
        
        # Calculate spam score (0-100, higher = more spam)
        spam_score = int((spam_indicators / max_indicators) * 100)
        
        if spam_score < 20:
            status = "optimal"
            message = "Low spam signals detected"
        elif spam_score < 40:
            status = "needs_attention"
            message = "Moderate spam signals - review backlink profile"
        else:
            status = "critical"
            message = "High spam signals - toxic backlinks present"
        
        return {
            "spam_score": spam_score,
            "spam_indicators_found": spam_indicators,
            "status": status,
            "message": message,
            "details": {
                "excessive_dofollow": dofollow_ratio > 0.95,
                "excessive_exact_match": total_anchors > 0 and (exact_match / total_anchors) > 0.3,
                "low_authority_ratio": (low_auth / total_analyzed) if total_analyzed > 0 else 0,
                "suspicious_tld_count": suspicious_count
            }
        }
    
    def analyze_link_context_quality(
        self,
        links_found: List[Dict],
        target_domain: str
    ) -> Dict[str, Any]:
        """
        Analyze contextual quality of backlinks.
        
        Args:
            links_found: List of link data from analysis
            target_domain: Target domain
            
        Returns:
            Contextual link quality analysis
        """
        contextual_links = 0
        footer_sidebar_links = 0
        homepage_links = 0
        content_links = 0
        
        for link in links_found:
            source_url = link.get("link_url", "").lower()
            
            # Heuristic: Links from homepage or root
            if source_url.count('/') <= 3:
                homepage_links += 1
            else:
                content_links += 1
            
            # Assume content pages are more contextual
            if '/' in source_url and source_url.count('/') > 3:
                contextual_links += 1
        
        total = len(links_found)
        contextual_ratio = contextual_links / total if total > 0 else 0
        
        if contextual_ratio >= 0.7:
            status = "optimal"
            message = f"{int(contextual_ratio*100)}% contextual links - strong relevance"
        elif contextual_ratio >= 0.4:
            status = "needs_attention"
            message = f"{int(contextual_ratio*100)}% contextual links - moderate quality"
        else:
            status = "needs_attention"
            message = f"{int(contextual_ratio*100)}% contextual links - many sitewide/footer links"
        
        return {
            "contextual_link_count": contextual_links,
            "homepage_link_count": homepage_links,
            "content_link_count": content_links,
            "contextual_ratio": round(contextual_ratio, 2),
            "status": status,
            "message": message
        }
    
    def detect_irrelevant_links(
        self,
        linking_domains: List[str],
        target_domain: str,
        target_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Detect potentially irrelevant linking domains.
        
        Uses heuristics based on domain relevance indicators.
        
        Args:
            linking_domains: List of linking domains
            target_domain: Target website domain
            target_keywords: Keywords for relevance matching
            
        Returns:
            Irrelevant link analysis
        """
        irrelevant_count = 0
        relevant_count = 0
        
        # Get target domain's niche indicators from domain name
        target_name = target_domain.split('.')[0].lower()
        
        for domain in linking_domains:
            domain_lower = domain.lower()
            
            # Check if domains share keywords
            has_keyword_overlap = False
            if target_keywords:
                for keyword in target_keywords:
                    if keyword.lower() in domain_lower:
                        has_keyword_overlap = True
                        break
            
            # Check if domain names are related
            domain_name = domain.split('.')[0].lower()
            is_related = (
                has_keyword_overlap or
                target_name in domain_name or
                domain_name in target_name or
                len(set(target_name.split('-')) & set(domain_name.split('-'))) > 0
            )
            
            if is_related:
                relevant_count += 1
            else:
                irrelevant_count += 1
        
        total = len(linking_domains)
        irrelevant_ratio = irrelevant_count / total if total > 0 else 0
        
        if irrelevant_ratio < 0.2:
            status = "optimal"
            message = f"Only {int(irrelevant_ratio*100)}% potentially irrelevant links"
        elif irrelevant_ratio < 0.4:
            status = "needs_attention"
            message = f"{int(irrelevant_ratio*100)}% potentially irrelevant links"
        else:
            status = "critical"
            message = f"{int(irrelevant_ratio*100)}% irrelevant links - review link profile"
        
        return {
            "irrelevant_count": irrelevant_count,
            "relevant_count": relevant_count,
            "irrelevant_ratio": round(irrelevant_ratio, 2),
            "total_analyzed": total,
            "status": status,
            "message": message
        }

    
    async def _analyze_single_domain(
        self,
        target_domain: str,
        linking_domain: str
    ) -> Dict[str, Any]:
        """
        Crawl a single linking domain to find and analyze our backlink.
        """
        result = {
            "linking_domain": linking_domain,
            "link_found": False,
            "link_url": None,
            "is_dofollow": True,
            "anchor_text": None,
            "anchor_type": "other",
            "authority_score": self._estimate_authority(linking_domain)
        }
        
        # Clean domain
        clean_domain = linking_domain.replace("www.", "").strip("/")
        
        # Try to fetch the homepage
        urls_to_try = [
            f"https://{clean_domain}",
            f"https://www.{clean_domain}",
            f"http://{clean_domain}"
        ]
        
        html = None
        for url in urls_to_try:
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, 
                    timeout=self.TIMEOUT
                ) as client:
                    response = await client.get(url, headers=self.headers)
                    if response.status_code == 200:
                        html = response.text
                        break
            except:
                continue
        
        if not html:
            return result
        
        # Parse and find links to our domain
        soup = BeautifulSoup(html, 'html.parser')
        target_clean = target_domain.replace("www.", "").lower()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            
            if target_clean in href:
                result["link_found"] = True
                result["link_url"] = href
                
                # Check if nofollow
                rel = link.get('rel', [])
                if isinstance(rel, list):
                    result["is_dofollow"] = 'nofollow' not in rel
                else:
                    result["is_dofollow"] = 'nofollow' not in str(rel)
                
                # Get anchor text
                anchor = link.get_text(strip=True)
                result["anchor_text"] = anchor[:100] if anchor else ""
                result["anchor_type"] = self._classify_anchor(
                    anchor, target_domain
                )
                
                break  # Found our link
        
        return result
    
    def _estimate_authority(self, domain: str) -> int:
        """
        Estimate domain authority using heuristics.
        """
        clean_domain = domain.replace("www.", "").lower()
        
        # Check TLD
        for tld, score in self.AUTHORITY_TLDS.items():
            if clean_domain.endswith(tld):
                return score
        
        # Check tier lists
        for tier1_domain in self.AUTHORITY_TIERS["tier1"]:
            if tier1_domain in clean_domain:
                return 90
        
        for tier2_domain in self.AUTHORITY_TIERS["tier2"]:
            if tier2_domain in clean_domain:
                return 75
        
        for tier3_domain in self.AUTHORITY_TIERS["tier3"]:
            if tier3_domain in clean_domain:
                return 60
        
        # Default: Medium authority
        return 50
    
    def _classify_anchor(
        self, 
        anchor: str, 
        target_domain: str
    ) -> str:
        """
        Classify anchor text type.
        """
        if not anchor:
            return "other"
        
        anchor_lower = anchor.lower().strip()
        domain_clean = target_domain.replace("www.", "").lower()
        
        # Brand name (domain without TLD)
        brand = domain_clean.split('.')[0]
        
        # URL anchor
        if anchor_lower.startswith(('http', 'www.')) or domain_clean in anchor_lower:
            return "url"
        
        # Branded anchor
        if brand in anchor_lower:
            return "branded"
        
        # Generic anchors
        generic_terms = [
            'click here', 'read more', 'learn more', 'visit', 'here',
            'this', 'link', 'website', 'site', 'page', 'check out'
        ]
        if any(term in anchor_lower for term in generic_terms):
            return "generic"
        
        # Default to partial match (assumed keyword-related)
        return "partial_match"
    
    def compute_off_page_health(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute overall off-page health scores from analysis.
        """
        # Domain Authority Score (heuristic)
        avg_authority = analysis.get("avg_authority_score", 50)
        high_auth = analysis.get("authority_distribution", {}).get("high", 0)
        total = analysis.get("domains_analyzed", 1) or 1
        
        authority_score = (avg_authority * 0.6) + (high_auth / total * 100 * 0.4)
        
        # Anchor Text Risk Score
        anchor_dist = analysis.get("anchor_distribution", {})
        branded = anchor_dist.get("branded", 0)
        generic = anchor_dist.get("generic", 0)
        natural = branded + generic
        
        anchor_score = 70  # Default
        if total > 0:
            natural_ratio = natural / total
            if natural_ratio >= 0.6:
                anchor_score = 90
            elif natural_ratio >= 0.4:
                anchor_score = 75
            elif natural_ratio >= 0.2:
                anchor_score = 60
            else:
                anchor_score = 40  # Risky - too many exact match
        
        # Follow/Nofollow Balance Score
        dofollow_ratio = analysis.get("dofollow_ratio", 0.5)
        if 0.3 <= dofollow_ratio <= 0.8:
            link_quality_score = 85  # Balanced
        elif 0.2 <= dofollow_ratio <= 0.9:
            link_quality_score = 70
        else:
            link_quality_score = 50  # Unbalanced
        
        return {
            "domain_authority_score": min(authority_score, 100),
            "anchor_text_score": anchor_score,
            "link_quality_score": link_quality_score,
            "overall_off_page_score": (
                authority_score * 0.4 + 
                anchor_score * 0.3 + 
                link_quality_score * 0.3
            )
        }
