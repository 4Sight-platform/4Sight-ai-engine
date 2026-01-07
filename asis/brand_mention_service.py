"""
Brand Mention Service
Detects and analyzes brand mentions from various sources
"""

import logging
from typing import Dict, List, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BrandMentionService:
    """
    Service for detecting and analyzing brand mentions.
    
    Uses:
    - GSC Performance API for search queries
    - Linking domain analysis
    - Social signal indicators
    """
    
    def __init__(self):
        pass
    
    def analyze_brand_consistency(
        self,
        brand_name: str,
        linked_mentions: List[Dict],
        unlinked_mentions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze brand name consistency across mentions.
        
        Args:
            brand_name: Official brand name
            linked_mentions: Mentions with clicks (linked)
            unlinked_mentions: Mentions with impressions only
            
        Returns:
            Consistency analysis
        """
        all_mentions = linked_mentions + unlinked_mentions
        
        if not all_mentions:
            return {
                "consistency_score": 100,
                "variations_found": [],
                "status": "optimal",
                "message": "No brand mentions found"
            }
        
        brand_lower = brand_name.lower()
        variations = set()
        exact_match_count = 0
        
        for mention in all_mentions:
            query = mention.get("query", "")
            
            # Check if exact match
            if brand_lower in query.lower():
                # Extract the brand part and check variations
                if query.lower().strip() == brand_lower:
                    exact_match_count += 1
                else:
                    # Check for common variations
                    if query.lower().replace("-", " ") == brand_lower.replace("-", " "):
                        variations.add("hyphenation")
                    elif query.lower().replace(" ", "") == brand_lower.replace(" ", ""):
                        variations.add("spacing")
        
        total_mentions = len(all_mentions)
        consistency_ratio = exact_match_count / total_mentions if total_mentions > 0 else 0
        consistency_score = int(consistency_ratio * 100)
        
        if consistency_score >= 80:
            status = "optimal"
        elif consistency_score >= 60:
            status = "needs_attention"
        else:
            status = "critical"
        
        return {
            "consistency_score": consistency_score,
            "exact_matches": exact_match_count,
            "total_mentions": total_mentions,
            "variations_found": list(variations),
            "status": status
        }
    
    def classify_mention_sources(
        self,
        linking_domains: List[str]
    ) -> Dict[str, Any]:
        """
        Classify linking domains by type (news, industry, social, etc.).
        
        Args:
            linking_domains: List of domains
            
        Returns:
            Classification results
        """
        news_domains = []
        industry_domains = []
        social_domains = []
        other_domains = []
        
        # Known patterns
        news_indicators = [
            'news', 'times', 'post', 'journal', 'herald', 'tribune',
            'reuters.com', 'bloomberg.com', 'bbc.com', 'cnn.com',
            'forbes.com', 'businessinsider.com'
        ]
        
        social_indicators = [
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'youtube.com', 'tiktok.com', 'reddit.com', 'medium.com'
        ]
        
        industry_indicators = [
            '.edu', '.gov', '.org', 'association', 'institute', 
            'foundation', 'council'
        ]
        
        for domain in linking_domains:
            domain_lower = domain.lower()
            
            # Check news
            if any(indicator in domain_lower for indicator in news_indicators):
                news_domains.append(domain)
            # Check social
            elif any(indicator in domain_lower for indicator in social_indicators):
                social_domains.append(domain)
            # Check industry
            elif any(indicator in domain_lower for indicator in industry_indicators):
                industry_domains.append(domain)
            else:
                other_domains.append(domain)
        
        total = len(linking_domains)
        
        return {
            "news_mentions_count": len(news_domains),
            "industry_mentions_count": len(industry_domains),
            "social_mentions_count": len(social_domains),
            "other_mentions_count": len(other_domains),
            "news_domains": news_domains[:5],  # Top 5
            "industry_domains": industry_domains[:5],
            "social_domains": social_domains[:5],
            "total_analyzed": total
        }
    
    def calculate_unlinked_opportunity_score(
        self,
        unlinked_count: int,
        linked_count: int
    ) -> Dict[str, Any]:
        """
        Calculate link reclamation opportunity score.
        
        High unlinked mentions = good opportunity for outreach.
        
        Args:
            unlinked_count: Unlinked brand mentions
            linked_count: Linked brand mentions
            
        Returns:
            Opportunity analysis
        """
        total_mentions = unlinked_count + linked_count
        
        if total_mentions == 0:
            return {
                "opportunity_score": 0,
                "potential_links": 0,
                "status": "needs_attention",
                "message": "No brand mentions detected"
            }
        
        unlinked_ratio = unlinked_count / total_mentions
        
        # Score based on how many could potentially be converted
        if unlinked_count >= 20:
            opportunity_score = 90
            status = "optimal"
            message = f"{unlinked_count} unlinked mentions - high outreach potential"
        elif unlinked_count >= 10:
            opportunity_score = 75
            status = "optimal"
            message = f"{unlinked_count} unlinked mentions - good outreach potential"
        elif unlinked_count >= 5:
            opportunity_score = 60
            status = "needs_attention"
            message = f"{unlinked_count} unlinked mentions - moderate opportunity"
        else:
            opportunity_score = 40
            status = "needs_attention"
            message = f"Only {unlinked_count} unlinked mentions found"
        
        return {
            "opportunity_score": opportunity_score,
            "potential_links": unlinked_count,
            "linked_mentions": linked_count,
            "unlinked_mentions": unlinked_count,
            "status": status,
            "message": message
        }
    
    def estimate_entity_recognition(
        self,
        domain: str,
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Estimate if brand has entity recognition (Knowledge Graph presence).
        
        Note: Actual verification requires manual check or Brand SERP API.
        This provides indicators that suggest entity status.
        
        Args:
            domain: Website domain
            brand_name: Brand name
            
        Returns:
            Entity recognition indicators
        """
        indicators = []
        score = 50  # Neutral default
        
        # Heuristic indicators:
        # 1. .com domain = more established
        if domain.endswith('.com'):
            indicators.append("Established TLD (.com)")
            score += 10
        
        # 2. Brand name in domain suggests brand focus
        brand_clean = brand_name.lower().replace(" ", "").replace("-", "")
        domain_clean = domain.lower().replace("www.", "").split(".")[0]
        
        if brand_clean in domain_clean or domain_clean in brand_clean:
            indicators.append("Brand-domain alignment")
            score += 15
        
        # 3. Simple, memorable brand name
        if len(brand_name.split()) == 1 and len(brand_name) < 15:
            indicators.append("Simple brand name (memorable)")
            score += 10
        
        # Final assessment
        if score >= 75:
            status = "optimal"
            message = "Strong entity recognition indicators"
        elif score >= 50:
            status = "needs_attention"
            message = "Moderate entity indicators - manual verification recommended"
        else:
            status = "needs_attention"
            message = "Limited entity indicators"
        
        return {
            "entity_score": min(score, 100),
            "indicators": indicators,
            "status": status,
            "message": message,
            "note": "Manual Google search recommended to verify Knowledge Graph presence"
        }
