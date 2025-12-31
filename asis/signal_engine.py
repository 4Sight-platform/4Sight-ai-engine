"""
Signal Engine
Rules-based engine for computing AS-IS parameter scores and statuses
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import date

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Rule engine for computing AS-IS State parameter scores and statuses.
    
    Implements the formula: raw signals → flags/scores → composite → status label
    
    Parameter Groups:
    - On-Page: 5 sub-groups
    - Off-Page: 5 sub-groups  
    - Technical: 5 sub-groups
    """
    
    # Status thresholds
    OPTIMAL_THRESHOLD = 80  # Score >= 80 = Optimal
    NEEDS_ATTENTION_THRESHOLD = 50  # Score 50-79 = Needs Attention
    # Score < 50 = Weak/Poor
    
    # ==================== On-Page Parameter Groups ====================
    
    ON_PAGE_GROUPS = {
        "page_topic_keyword_targeting": {
            "name": "Page Topic & Keyword Targeting",
            "description": "How well pages are optimized for target keywords",
            "sub_parameters": [
                "primary_keyword_in_title",
                "primary_keyword_in_h1",
                "keyword_in_first_100_words",
                "keyword_density",
                "semantic_relevance"
            ]
        },
        "serp_snippet_optimization": {
            "name": "SERP Snippet Optimization",
            "description": "Title and meta description optimization for CTR",
            "sub_parameters": [
                "title_length_optimal",
                "title_unique",
                "meta_description_length_optimal",
                "meta_description_unique",
                "meta_description_cta"
            ]
        },
        "content_structure_hierarchy": {
            "name": "Content Structure & Semantic Hierarchy",
            "description": "Heading structure and content organization",
            "sub_parameters": [
                "single_h1",
                "h2_hierarchy_correct",
                "heading_keyword_usage",
                "content_length_adequate",
                "paragraph_structure"
            ]
        },
        "media_accessibility": {
            "name": "Media/Accessibility Optimization",
            "description": "Image optimization and accessibility",
            "sub_parameters": [
                "all_images_have_alt",
                "alt_text_descriptive",
                "image_file_names_seo",
                "lazy_loading_implemented",
                "image_compression"
            ]
        },
        "url_page_signals": {
            "name": "URL & Page-Level Signals",
            "description": "URL structure and page-level SEO",
            "sub_parameters": [
                "url_length_optimal",
                "url_no_parameters",
                "url_readable",
                "url_keyword_presence",
                "canonical_correct"
            ]
        }
    }
    
    # ==================== Off-Page Parameter Groups ====================
    
    OFF_PAGE_GROUPS = {
        "domain_authority_trust": {
            "name": "Domain Authority & Trust Signals",
            "description": "Domain reputation and authority metrics",
            "sub_parameters": [
                "referring_domains_count",
                "domain_authority_score",
                "trust_flow",
                "brand_mentions",
                "domain_age"
            ]
        },
        "backlink_relevance": {
            "name": "Backlink Relevance & Alignment",
            "description": "Quality and relevance of backlink profile",
            "sub_parameters": [
                "topical_relevance",
                "geographic_relevance",
                "industry_alignment",
                "linking_domain_quality",
                "content_context"
            ]
        },
        "anchor_text_balance": {
            "name": "Anchor Text Risk Balance",
            "description": "Anchor text distribution and risk assessment",
            "sub_parameters": [
                "branded_anchor_ratio",
                "exact_match_anchor_ratio",
                "generic_anchor_ratio",
                "naked_url_ratio",
                "anchor_diversity"
            ]
        },
        "brand_entity_authority": {
            "name": "Brand Mentions & Entity Authority",
            "description": "Brand presence and entity recognition",
            "sub_parameters": [
                "unlinked_brand_mentions",
                "entity_in_knowledge_graph",
                "social_signals",
                "news_mentions",
                "industry_citations"
            ]
        },
        "link_growth_stability": {
            "name": "Link Growth Stability",
            "description": "Backlink acquisition patterns",
            "sub_parameters": [
                "link_velocity",
                "link_loss_rate",
                "natural_growth_pattern",
                "spam_link_ratio",
                "link_reclamation_opportunities"
            ]
        }
    }
    
    # ==================== Technical Parameter Groups ====================
    
    TECHNICAL_GROUPS = {
        "crawl_indexation": {
            "name": "Crawl & Indexation",
            "description": "How well search engines can crawl and index the site",
            "sub_parameters": [
                "index_coverage_ratio",
                "crawl_errors",
                "sitemap_status",
                "robots_txt_valid",
                "crawl_budget_efficiency"
            ]
        },
        "canonicalization_duplicate": {
            "name": "Canonicalization & Duplicate Control",
            "description": "Handling of duplicate content and canonical tags",
            "sub_parameters": [
                "canonical_implementation",
                "duplicate_titles",
                "duplicate_descriptions",
                "http_https_consistency",
                "trailing_slash_consistency"
            ]
        },
        "page_experience_cwv": {
            "name": "Page Experience Performance",
            "description": "Core Web Vitals and page experience",
            "sub_parameters": [
                "lcp_score",
                "inp_score",
                "cls_score",
                "mobile_friendly",
                "https_enabled"
            ]
        },
        "search_rendering": {
            "name": "Search Rendering Accessibility",
            "description": "JavaScript rendering and search bot accessibility",
            "sub_parameters": [
                "js_rendering_accessible",
                "critical_content_in_html",
                "no_render_blocking",
                "structured_data_valid",
                "mobile_viewport_set"
            ]
        },
        "ai_crawl_governance": {
            "name": "AI & LLM Crawl Governance",
            "description": "Control over AI crawler access",
            "sub_parameters": [
                "ai_crawler_policy_defined",
                "llm_txt_present",
                "selective_ai_access",
                "content_protection",
                "ai_training_consent"
            ]
        }
    }
    
    def __init__(self):
        self.all_groups = {
            "onpage": self.ON_PAGE_GROUPS,
            "offpage": self.OFF_PAGE_GROUPS,
            "technical": self.TECHNICAL_GROUPS
        }
    
    def compute_status(self, score: float) -> str:
        """Determine status based on score."""
        if score >= self.OPTIMAL_THRESHOLD:
            return "optimal"
        elif score >= self.NEEDS_ATTENTION_THRESHOLD:
            return "needs_attention"
        else:
            return "needs_attention"  # For MVP, we use needs_attention instead of "weak"
    
    def compute_on_page_scores(self, signals: Dict[str, Any]) -> List[Dict]:
        """
        Compute scores for all On-Page parameter groups.
        
        Args:
            signals: Dict with on-page signal data from crawler
            
        Returns:
            List of parameter group scores
        """
        results = []
        
        # Page Topic & Keyword Targeting
        page_topic_score = self._score_page_topic(signals)
        results.append({
            "group_id": "page_topic_keyword_targeting",
            "name": self.ON_PAGE_GROUPS["page_topic_keyword_targeting"]["name"],
            "score": page_topic_score,
            "status": self.compute_status(page_topic_score),
            "tab": "onpage"
        })
        
        # SERP Snippet Optimization
        snippet_score = self._score_serp_snippet(signals)
        results.append({
            "group_id": "serp_snippet_optimization",
            "name": self.ON_PAGE_GROUPS["serp_snippet_optimization"]["name"],
            "score": snippet_score,
            "status": self.compute_status(snippet_score),
            "tab": "onpage"
        })
        
        # Content Structure & Hierarchy
        structure_score = self._score_content_structure(signals)
        results.append({
            "group_id": "content_structure_hierarchy",
            "name": self.ON_PAGE_GROUPS["content_structure_hierarchy"]["name"],
            "score": structure_score,
            "status": self.compute_status(structure_score),
            "tab": "onpage"
        })
        
        # Media/Accessibility
        media_score = self._score_media_accessibility(signals)
        results.append({
            "group_id": "media_accessibility",
            "name": self.ON_PAGE_GROUPS["media_accessibility"]["name"],
            "score": media_score,
            "status": self.compute_status(media_score),
            "tab": "onpage"
        })
        
        # URL & Page-Level Signals
        url_score = self._score_url_signals(signals)
        results.append({
            "group_id": "url_page_signals",
            "name": self.ON_PAGE_GROUPS["url_page_signals"]["name"],
            "score": url_score,
            "status": self.compute_status(url_score),
            "tab": "onpage"
        })
        
        return results
    
    def _score_page_topic(self, signals: Dict) -> float:
        """Score Page Topic & Keyword Targeting."""
        score = 0
        max_score = 100
        
        # Check if content exists and has keywords (simplified)
        if signals.get("word_count", 0) >= 300:
            score += 30
        elif signals.get("word_count", 0) >= 100:
            score += 15
        
        # Has H1 with content
        if signals.get("h1_text"):
            score += 25
        
        # First 100 words exist
        if signals.get("first_100_words"):
            score += 25
        
        # Adequate heading structure suggests topic coverage
        if signals.get("h2_count", 0) >= 2:
            score += 20
        elif signals.get("h2_count", 0) >= 1:
            score += 10
        
        return min(score, max_score)
    
    def _score_serp_snippet(self, signals: Dict) -> float:
        """Score SERP Snippet Optimization."""
        score = 0
        
        # Title tag exists and optimal length (50-60 chars)
        title_len = signals.get("title_length", 0)
        if 50 <= title_len <= 60:
            score += 30
        elif 30 <= title_len <= 70:
            score += 20
        elif title_len > 0:
            score += 10
        
        # Meta description exists and optimal length (150-160 chars)
        meta_len = signals.get("meta_description_length", 0)
        if 150 <= meta_len <= 160:
            score += 30
        elif 100 <= meta_len <= 170:
            score += 20
        elif meta_len > 0:
            score += 10
        
        # Title is not empty
        if signals.get("title_tag"):
            score += 20
        
        # Meta description is not empty
        if signals.get("meta_description"):
            score += 20
        
        return min(score, 100)
    
    def _score_content_structure(self, signals: Dict) -> float:
        """Score Content Structure & Semantic Hierarchy."""
        score = 0
        
        # Single H1 is ideal
        h1_count = signals.get("h1_count", 0)
        if h1_count == 1:
            score += 30
        elif h1_count > 1:
            score += 10  # Multiple H1s is not ideal
        
        # Has H2 tags for structure
        h2_count = signals.get("h2_count", 0)
        if h2_count >= 3:
            score += 25
        elif h2_count >= 1:
            score += 15
        
        # Has H3 for deeper structure
        if signals.get("h3_count", 0) >= 1:
            score += 15
        
        # Adequate word count
        word_count = signals.get("word_count", 0)
        if word_count >= 1000:
            score += 30
        elif word_count >= 500:
            score += 20
        elif word_count >= 200:
            score += 10
        
        return min(score, 100)
    
    def _score_media_accessibility(self, signals: Dict) -> float:
        """Score Media/Accessibility Optimization."""
        score = 50  # Base score if no images
        
        image_count = signals.get("image_count", 0)
        if image_count > 0:
            with_alt = signals.get("images_with_alt", 0)
            without_alt = signals.get("images_without_alt", 0)
            
            alt_ratio = with_alt / image_count if image_count > 0 else 0
            
            if alt_ratio >= 0.9:
                score = 100
            elif alt_ratio >= 0.7:
                score = 80
            elif alt_ratio >= 0.5:
                score = 60
            else:
                score = 40
        
        return score
    
    def _score_url_signals(self, signals: Dict) -> float:
        """Score URL & Page-Level Signals."""
        score = 0
        
        # URL length optimal (< 75 chars)
        url_len = signals.get("url_length", 0)
        if url_len > 0 and url_len <= 75:
            score += 25
        elif url_len <= 100:
            score += 15
        elif url_len > 0:
            score += 5
        
        # No URL parameters
        if not signals.get("url_has_parameters", False):
            score += 25
        else:
            score += 10
        
        # Reasonable URL depth
        depth = signals.get("url_depth", 0)
        if depth <= 3:
            score += 25
        elif depth <= 5:
            score += 15
        else:
            score += 5
        
        # Has canonical (self-referencing is good)
        if signals.get("canonical_self_referencing", False):
            score += 25
        elif signals.get("canonical_url"):
            score += 15
        
        return min(score, 100)
    
    def compute_off_page_scores(self, backlink_data: Dict, gsc_data: Dict = None) -> List[Dict]:
        """
        Compute scores for all Off-Page parameter groups.
        
        Args:
            backlink_data: Backlink signals
            gsc_data: GSC links data
            
        Returns:
            List of parameter group scores
        """
        results = []
        
        # Domain Authority & Trust
        authority_score = self._score_domain_authority(backlink_data)
        results.append({
            "group_id": "domain_authority_trust",
            "name": self.OFF_PAGE_GROUPS["domain_authority_trust"]["name"],
            "score": authority_score,
            "status": self.compute_status(authority_score),
            "tab": "offpage"
        })
        
        # Backlink Relevance - placeholder score (requires external data)
        relevance_score = 60  # Default to needs_attention for MVP
        results.append({
            "group_id": "backlink_relevance",
            "name": self.OFF_PAGE_GROUPS["backlink_relevance"]["name"],
            "score": relevance_score,
            "status": self.compute_status(relevance_score),
            "tab": "offpage"
        })
        
        # Anchor Text Balance
        anchor_score = self._score_anchor_text(backlink_data)
        results.append({
            "group_id": "anchor_text_balance",
            "name": self.OFF_PAGE_GROUPS["anchor_text_balance"]["name"],
            "score": anchor_score,
            "status": self.compute_status(anchor_score),
            "tab": "offpage"
        })
        
        # Brand Entity Authority - placeholder
        brand_score = 60
        results.append({
            "group_id": "brand_entity_authority",
            "name": self.OFF_PAGE_GROUPS["brand_entity_authority"]["name"],
            "score": brand_score,
            "status": self.compute_status(brand_score),
            "tab": "offpage"
        })
        
        # Link Growth Stability - placeholder
        growth_score = 70
        results.append({
            "group_id": "link_growth_stability",
            "name": self.OFF_PAGE_GROUPS["link_growth_stability"]["name"],
            "score": growth_score,
            "status": self.compute_status(growth_score),
            "tab": "offpage"
        })
        
        return results
    
    def _score_domain_authority(self, backlink_data: Dict) -> float:
        """Score Domain Authority based on referring domains."""
        referring_domains = backlink_data.get("referring_domains", 0)
        
        # Simple scoring based on referring domain count
        if referring_domains >= 100:
            return 90
        elif referring_domains >= 50:
            return 80
        elif referring_domains >= 20:
            return 70
        elif referring_domains >= 10:
            return 60
        elif referring_domains >= 5:
            return 50
        else:
            return 40
    
    def _score_anchor_text(self, backlink_data: Dict) -> float:
        """Score anchor text diversity."""
        anchor_distribution = backlink_data.get("anchor_text_distribution", {})
        
        if not anchor_distribution:
            return 60  # Default when no data
        
        # Check for healthy distribution
        branded = anchor_distribution.get("branded", 0)
        exact_match = anchor_distribution.get("exact_match", 0)
        generic = anchor_distribution.get("generic", 0)
        
        # Ideal: 40-60% branded, <10% exact match
        score = 70
        
        if exact_match > 20:
            score -= 20  # Too many exact match anchors is risky
        
        if branded >= 30 and branded <= 60:
            score += 15
        
        if generic >= 10 and generic <= 30:
            score += 15
        
        return min(max(score, 0), 100)
    
    def compute_technical_scores(
        self, 
        technical_data: Dict, 
        cwv_data: Dict = None, 
        ai_governance: Dict = None
    ) -> List[Dict]:
        """
        Compute scores for all Technical parameter groups.
        
        Args:
            technical_data: Technical signals
            cwv_data: Core Web Vitals data
            ai_governance: AI crawl governance data
            
        Returns:
            List of parameter group scores
        """
        results = []
        
        # Crawl & Indexation
        crawl_score = self._score_crawl_indexation(technical_data)
        results.append({
            "group_id": "crawl_indexation",
            "name": self.TECHNICAL_GROUPS["crawl_indexation"]["name"],
            "score": crawl_score,
            "status": self.compute_status(crawl_score),
            "tab": "technical"
        })
        
        # Canonicalization & Duplicate Control
        canonical_score = self._score_canonicalization(technical_data)
        results.append({
            "group_id": "canonicalization_duplicate",
            "name": self.TECHNICAL_GROUPS["canonicalization_duplicate"]["name"],
            "score": canonical_score,
            "status": self.compute_status(canonical_score),
            "tab": "technical"
        })
        
        # Page Experience (CWV)
        cwv_score = self._score_cwv(cwv_data or {})
        results.append({
            "group_id": "page_experience_cwv",
            "name": self.TECHNICAL_GROUPS["page_experience_cwv"]["name"],
            "score": cwv_score,
            "status": self.compute_status(cwv_score),
            "tab": "technical"
        })
        
        # Search Rendering
        rendering_score = 75  # Default for MVP
        results.append({
            "group_id": "search_rendering",
            "name": self.TECHNICAL_GROUPS["search_rendering"]["name"],
            "score": rendering_score,
            "status": self.compute_status(rendering_score),
            "tab": "technical"
        })
        
        # AI & LLM Crawl Governance
        ai_score = self._score_ai_governance(ai_governance or {})
        results.append({
            "group_id": "ai_crawl_governance",
            "name": self.TECHNICAL_GROUPS["ai_crawl_governance"]["name"],
            "score": ai_score,
            "status": self.compute_status(ai_score),
            "tab": "technical"
        })
        
        return results
    
    def _score_crawl_indexation(self, data: Dict) -> float:
        """Score Crawl & Indexation."""
        score = 0
        
        # Index coverage ratio
        coverage = data.get("index_coverage_ratio", 0)
        if coverage >= 0.9:
            score += 40
        elif coverage >= 0.7:
            score += 30
        elif coverage >= 0.5:
            score += 20
        
        # Robots.txt exists and valid
        if data.get("robots_txt_valid", False):
            score += 20
        elif data.get("robots_txt_exists", False):
            score += 10
        
        # Sitemap exists and valid
        if data.get("sitemap_valid", False):
            score += 20
        elif data.get("sitemap_exists", False):
            score += 10
        
        # HTTPS enabled
        if data.get("https_enabled", False):
            score += 20
        
        return min(score, 100)
    
    def _score_canonicalization(self, data: Dict) -> float:
        """Score Canonicalization & Duplicate Control."""
        score = 80  # Start with good score
        
        # Deduct for issues
        if data.get("canonical_issues_count", 0) > 5:
            score -= 30
        elif data.get("canonical_issues_count", 0) > 0:
            score -= 15
        
        if data.get("duplicate_title_count", 0) > 5:
            score -= 20
        elif data.get("duplicate_title_count", 0) > 0:
            score -= 10
        
        if data.get("duplicate_description_count", 0) > 5:
            score -= 15
        elif data.get("duplicate_description_count", 0) > 0:
            score -= 5
        
        if not data.get("trailing_slash_consistent", True):
            score -= 10
        
        return max(score, 0)
    
    def _score_cwv(self, data: Dict) -> float:
        """Score Core Web Vitals."""
        status = data.get("overall_status", "").lower()
        
        if status == "good":
            return 95
        elif status == "needs_improvement":
            return 65
        elif status == "poor":
            return 35
        
        # If no overall status, check individual metrics
        score = 0
        metrics_count = 0
        
        for metric in ["lcp_status", "inp_status", "cls_status"]:
            metric_status = data.get(metric, "").lower()
            if metric_status == "good":
                score += 33
                metrics_count += 1
            elif metric_status == "needs_improvement":
                score += 20
                metrics_count += 1
            elif metric_status == "poor":
                score += 5
                metrics_count += 1
        
        return score if metrics_count > 0 else 60  # Default if no data
    
    def _score_ai_governance(self, data: Dict) -> float:
        """Score AI & LLM Crawl Governance."""
        score = 50  # Base score
        
        # Has explicit AI crawler policy
        if data.get("ai_crawlers_blocked") or data.get("ai_crawlers_allowed"):
            score += 30
        
        # Has llm.txt
        if data.get("llm_txt_detected", False):
            score += 20
        
        return min(score, 100)
    
    def compute_all_scores(
        self,
        on_page_signals: Dict,
        backlink_data: Dict,
        technical_data: Dict,
        cwv_data: Dict = None,
        ai_governance: Dict = None
    ) -> Dict[str, List[Dict]]:
        """
        Compute all parameter scores across all tabs.
        
        Returns:
            Dict with 'onpage', 'offpage', 'technical' keys
        """
        return {
            "onpage": self.compute_on_page_scores(on_page_signals),
            "offpage": self.compute_off_page_scores(backlink_data),
            "technical": self.compute_technical_scores(technical_data, cwv_data, ai_governance)
        }
    
    def get_group_details(self, tab: str, group_id: str) -> Dict[str, Any]:
        """Get detailed information about a parameter group."""
        groups = self.all_groups.get(tab, {})
        group = groups.get(group_id, {})
        
        return {
            "group_id": group_id,
            "name": group.get("name", ""),
            "description": group.get("description", ""),
            "sub_parameters": group.get("sub_parameters", [])
        }
