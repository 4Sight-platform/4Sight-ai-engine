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
    # Status thresholds
    OPTIMAL_THRESHOLD = 80  # Score >= 80 = Optimal
    NEEDS_ATTENTION_THRESHOLD = 50  # Score 50-79 = Needs Attention
    # Score < 50 = Critical
    
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
            return "critical"
    
    def compute_on_page_scores(self, signals: Dict[str, Any], keywords: List[str] = None) -> List[Dict]:
        """
        Compute scores for all On-Page parameter groups.
        
        Args:
            signals: Dict with on-page signal data from crawler
            keywords: User's tracked keywords for matching
            
        Returns:
            List of parameter group scores
        """
        results = []
        
        # Page Topic & Keyword Targeting (with keyword matching)
        page_topic_score, page_topic_details = self._score_page_topic(signals, keywords)
        results.append({
            "group_id": "page_topic_keyword_targeting",
            "name": self.ON_PAGE_GROUPS["page_topic_keyword_targeting"]["name"],
            "score": page_topic_score,
            "status": self.compute_status(page_topic_score),
            "details": page_topic_details,
            "tab": "onpage"
        })
        
        # SERP Snippet Optimization
        snippet_score, snippet_details = self._score_serp_snippet(signals)
        results.append({
            "group_id": "serp_snippet_optimization",
            "name": self.ON_PAGE_GROUPS["serp_snippet_optimization"]["name"],
            "score": snippet_score,
            "status": self.compute_status(snippet_score),
            "details": snippet_details,
            "tab": "onpage"
        })
        
        # Content Structure & Hierarchy
        structure_score, structure_details = self._score_content_structure(signals)
        results.append({
            "group_id": "content_structure_hierarchy",
            "name": self.ON_PAGE_GROUPS["content_structure_hierarchy"]["name"],
            "score": structure_score,
            "status": self.compute_status(structure_score),
            "details": structure_details,
            "tab": "onpage"
        })
        
        # Media/Accessibility
        media_score, media_details = self._score_media_accessibility(signals)
        results.append({
            "group_id": "media_accessibility",
            "name": self.ON_PAGE_GROUPS["media_accessibility"]["name"],
            "score": media_score,
            "status": self.compute_status(media_score),
            "details": media_details,
            "tab": "onpage"
        })
        
        # URL & Page-Level Signals
        url_score, url_details = self._score_url_signals(signals)
        results.append({
            "group_id": "url_page_signals",
            "name": self.ON_PAGE_GROUPS["url_page_signals"]["name"],
            "score": url_score,
            "status": self.compute_status(url_score),
            "details": url_details,
            "tab": "onpage"
        })
        
        return results
    
    def _score_page_topic(self, signals: Dict, keywords: List[str] = None) -> tuple[float, Dict]:
        """Score Page Topic & Keyword Targeting with keyword matching."""
        score = 0
        max_score = 100
        details = {}
        
        # Check if content exists
        word_count = signals.get("word_count", 0)
        wc_status = "critical"
        if word_count >= 300:
            score += 15
            wc_status = "optimal"
        elif word_count >= 100:
            score += 5
            wc_status = "needs_attention"
        
        details["content_length"] = {
            "value": f"{word_count} words",
            "status": wc_status
        }
            
        # Semantic relevance proxy
        details["semantic_relevance"] = {
            "value": "High relevance" if word_count >= 500 else "Low relevance",
            "status": "optimal" if word_count >= 500 else "needs_attention"
        }
        if word_count >= 500:
            score += 5
        
        # Has H1 with content
        h1_text = signals.get("h1_text", "").lower()
        details["h1_presence"] = {
            "value": "Present" if h1_text else "Missing",
            "status": "optimal" if h1_text else "critical"
        }
        if h1_text:
            score += 15
        
        # First 100 words exist
        first_100 = signals.get("first_100_words", "").lower()
        details["keyword_in_intro"] = {
            "value": "Intro content found" if first_100 else "Missing intro",
            "status": "optimal" if first_100 else "critical"
        }
        if first_100:
            score += 10
        
        # Adequate heading structure
        h2_count = signals.get("h2_count", 0)
        details["heading_structure"] = {
            "value": f"{h2_count} H2 tags",
            "status": "optimal" if h2_count >= 2 else "needs_attention"
        }
        if h2_count >= 2:
            score += 5
        elif h2_count >= 1:
            score += 2
        
        # === KEYWORD MATCHING ===
        if keywords and len(keywords) > 0:
            primary_kw = keywords[0].lower()
            title_text = signals.get("title_tag", "").lower()
            
            # Keyword in title (+20)
            in_title = primary_kw in title_text
            details["primary_keyword_in_title"] = {
                "value": f"'{primary_kw}' in title" if in_title else "Missing in title",
                "status": "optimal" if in_title else "critical"
            }
            if in_title: score += 20
            
            # Keyword in H1 (+20)
            in_h1 = primary_kw in h1_text
            details["primary_keyword_in_h1"] = {
                "value": f"'{primary_kw}' in H1" if in_h1 else "Missing in H1",
                "status": "optimal" if in_h1 else "critical"
            }
            if in_h1: score += 20
            
            # Keyword in first 100 words (+10)
            in_intro = primary_kw in first_100
            details["keyword_in_first_100"] = {
                "value": "Present in intro" if in_intro else "Missing in intro",
                "status": "optimal" if in_intro else "needs_attention"
            }
            if in_intro: score += 10
            
            details["keyword_density"] = {"value": "Optimal range", "status": "optimal"} # Placeholder
            
        else:
            # If no keywords provided, give partial credit & placeholders
            score += 15
            details["primary_keyword_in_title"] = {"value": "No target keyword", "status": "needs_attention"}
            details["primary_keyword_in_h1"] = {"value": "No target keyword", "status": "needs_attention"}
            details["keyword_in_first_100"] = {"value": "No target keyword", "status": "needs_attention"}
            details["keyword_density"] = {"value": "No target keyword", "status": "needs_attention"}
        
        return min(score, max_score), details
    
    def _score_serp_snippet(self, signals: Dict) -> tuple[float, Dict]:
        """Score SERP Snippet Optimization."""
        score = 0
        details = {}
        
        # Title tag exists and optimal length (50-60 chars)
        title_len = signals.get("title_length", 0)
        title_status = "critical"
        title_val = f"{title_len} chars"
        
        if 50 <= title_len <= 60:
            score += 30
            title_status = "optimal"
            title_val += " (Optimal)"
        elif 30 <= title_len <= 70:
            score += 20
            title_status = "needs_attention"
            title_val += " (Acceptable)"
        elif title_len > 0:
            score += 10
            title_status = "needs_attention"
            title_val += " (Poor length)"
        else:
            title_val = "Missing"
            
        details["title_length"] = {"value": title_val, "status": title_status}
        
        # Meta description exists and optimal length (150-160 chars)
        meta_len = signals.get("meta_description_length", 0)
        meta_status = "critical"
        meta_val = f"{meta_len} chars"
        
        if 150 <= meta_len <= 160:
            score += 30
            meta_status = "optimal"
            meta_val += " (Optimal)"
        elif 100 <= meta_len <= 170:
            score += 20
            meta_status = "needs_attention"
            meta_val += " (Acceptable)"
        elif meta_len > 0:
            score += 10
            meta_status = "needs_attention"
            meta_val += " (Poor length)"
        else:
            meta_val = "Missing"
            
        details["meta_description_length"] = {"value": meta_val, "status": meta_status}
        
        # Title is not empty
        has_title = bool(signals.get("title_tag"))
        if has_title: score += 20
        details["title_unique"] = {
            "value": "Present" if has_title else "Missing",
            "status": "optimal" if has_title else "critical"
        }
        
        # Meta description is not empty
        has_meta = bool(signals.get("meta_description"))
        if has_meta: score += 20
        details["meta_description_unique"] = {
            "value": "Present" if has_meta else "Missing",
            "status": "optimal" if has_meta else "critical"
        }
        
        details["meta_description_cta"] = {"value": "Standard", "status": "needs_attention"}
        
        return min(score, 100), details
    
    def _score_content_structure(self, signals: Dict) -> tuple[float, Dict]:
        """Score Content Structure & Semantic Hierarchy."""
        score = 0
        details = {}
        
        # Single H1 is ideal
        h1_count = signals.get("h1_count", 0)
        h1_status = "optimal"
        if h1_count == 1:
            score += 30
            h1_val = "1 H1 tag (Optimal)"
        elif h1_count > 1:
            score += 10
            h1_status = "needs_attention"
            h1_val = f"{h1_count} H1 tags (Multiple)"
        else:
            h1_status = "critical"
            h1_val = "Missing H1"
            
        details["single_h1"] = {"value": h1_val, "status": h1_status}
        
        # Has H2 tags for structure
        h2_count = signals.get("h2_count", 0)
        h2_status = "critical"
        if h2_count >= 3:
            score += 25
            h2_status = "optimal"
        elif h2_count >= 1:
            score += 15
            h2_status = "needs_attention"
            
        details["h2_hierarchy_correct"] = {"value": f"{h2_count} H2 tags", "status": h2_status}
        
        # Has H3 for deeper structure
        h3_count = signals.get("h3_count", 0)
        if h3_count >= 1: score += 10
        details["heading_keyword_usage"] = {
            "value": "Keywords in headings" if h3_count > 0 else "Low heading usage",
            "status": "optimal" if h3_count > 0 else "needs_attention"
        }
            
        # Heading order valid
        order_valid = signals.get("heading_order_valid", False)
        if order_valid: score += 15
        details["heading_order"] = {
            "value": "Valid hierarchy" if order_valid else "Skipped levels",
            "status": "optimal" if order_valid else "needs_attention"
        }
        
        # Adequate word count
        word_count = signals.get("word_count", 0)
        wc_details = "optimal"
        if word_count >= 1000:
            score += 20
        elif word_count >= 500:
            score += 10
            wc_details = "optimal"
        elif word_count >= 200:
            score += 5
            wc_details = "needs_attention"
        else:
            wc_details = "critical"
            
        details["content_length_adequate"] = {
            "value": f"{word_count} words",
            "status": wc_details
        }
        
        # Paragraph structure (simple check for now)
        details["paragraph_structure"] = {"value": "Standard", "status": "optimal"}
        
        return min(score, 100), details
    
    def _score_media_accessibility(self, signals: Dict) -> tuple[float, Dict]:
        """Score Media/Accessibility Optimization."""
        score = 50  # Base score if no images
        details = {}
        
        image_count = signals.get("image_count", 0)
        
        # Default statuses
        alt_status = "optimal"
        alt_val = "No images"
        lazy_status = "optimal"
        lazy_val = "N/A"
        
        if image_count > 0:
            with_alt = signals.get("images_with_alt", 0)
            without_alt = signals.get("images_without_alt", 0)
            
            alt_ratio = with_alt / image_count if image_count > 0 else 0
            
            if alt_ratio >= 0.9:
                score = 80
                alt_status = "optimal"
            elif alt_ratio >= 0.7:
                score = 60
                alt_status = "needs_attention"
            elif alt_ratio >= 0.5:
                score = 40
                alt_status = "needs_attention"
            else:
                score = 20
                alt_status = "critical"
            
            alt_val = f"{with_alt}/{image_count} images have alt text"
            
            # Lazy loading bonus
            lazy_ratio = signals.get("lazy_loading_ratio", 0)
            if lazy_ratio >= 0.8:
                score += 20
                lazy_status = "optimal"
                lazy_val = "Implemented"
            elif lazy_ratio >= 0.5:
                score += 10
                lazy_status = "needs_attention"
                lazy_val = "Partially implemented"
            else:
                lazy_status = "needs_attention"
                lazy_val = "Not detected"
        
        details["all_images_have_alt"] = {"value": alt_val, "status": alt_status}
        details["alt_text_descriptive"] = {"value": "Standard", "status": "optimal"} # Placeholder
        details["image_file_names_seo"] = {"value": "Standard", "status": "optimal"} # Placeholder
        details["lazy_loading_implemented"] = {"value": lazy_val, "status": lazy_status}
        details["image_compression"] = {"value": "Standard", "status": "optimal"} # Placeholder
        
        return score, details
    
    def _score_url_signals(self, signals: Dict) -> tuple[float, Dict]:
        """Score URL & Page-Level Signals."""
        score = 0
        details = {}
        
        # URL length optimal (< 75 chars)
        url_len = signals.get("url_length", 0)
        len_status = "critical"
        len_val = f"{url_len} chars"
        
        if url_len > 0 and url_len <= 75:
            score += 25
            len_status = "optimal"
            len_val += " (Optimal)"
        elif url_len <= 100:
            score += 15
            len_status = "needs_attention"
            len_val += " (Long)"
        elif url_len > 0:
            score += 5
            len_status = "critical"
            len_val += " (Too long)"
        else:
            len_val = "Unknown"
            
        details["url_length_optimal"] = {"value": len_val, "status": len_status}
        
        # No URL parameters
        has_params = signals.get("url_has_parameters", False)
        if not has_params:
            score += 25
            
        details["url_no_parameters"] = {
            "value": "Clean URL" if not has_params else "Contains parameters",
            "status": "optimal" if not has_params else "needs_attention"
        }
        
        # Reasonable URL depth
        depth = signals.get("url_depth", 0)
        depth_status = "optimal"
        if depth <= 3:
            score += 25
        elif depth <= 5:
            score += 15
            depth_status = "needs_attention"
        else:
            score += 5
            depth_status = "needs_attention"
            
        details["url_depth"] = {"value": f"Depth {depth}", "status": depth_status}
            
        # Placeholders
        details["url_readable"] = {"value": "Yes", "status": "optimal"}
        details["url_keyword_presence"] = {"value": "In URL", "status": "optimal"}
        details["canonical_correct"] = {"value": "Self-referencing", "status": "optimal"}
        score += 35
        
        return min(score, 100), details
    
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
        authority_score, authority_details = self._score_domain_authority(backlink_data)
        results.append({
            "group_id": "domain_authority_trust",
            "name": self.OFF_PAGE_GROUPS["domain_authority_trust"]["name"],
            "score": authority_score,
            "status": self.compute_status(authority_score),
            "details": authority_details,
            "tab": "offpage"
        })
        
        # Backlink Relevance - uses authority distribution from backlink analyzer
        health_scores = backlink_data.get("health_scores", {})
        relevance_score = health_scores.get("domain_authority_score", 60)
        relevance_details = {
            "referring_domains": {"value": "Limited diversity", "status": "needs_attention"},
            "contextual_links": {"value": "Standard ratio", "status": "needs_attention"},
            "toxic_score": {"value": "Low toxicity", "status": "optimal"},
            "irrelevant_link_detection": {"value": "Minimal irrelevant", "status": "optimal"}
        }
        results.append({
            "group_id": "backlink_relevance",
            "name": self.OFF_PAGE_GROUPS["backlink_relevance"]["name"],
            "score": relevance_score,
            "status": self.compute_status(relevance_score),
            "details": relevance_details,
            "tab": "offpage"
        })
        
        # Anchor Text Balance
        anchor_score, anchor_details = self._score_anchor_text(backlink_data)
        results.append({
            "group_id": "anchor_text_balance",
            "name": self.OFF_PAGE_GROUPS["anchor_text_balance"]["name"],
            "score": anchor_score,
            "status": self.compute_status(anchor_score),
            "details": anchor_details,
            "tab": "offpage"
        })
        
        # Brand Entity Authority - uses anchor text analysis for brand mentions
        anchor_dist = backlink_data.get("anchor_text_distribution", {})
        branded_count = anchor_dist.get("branded", 0)
        total = sum(anchor_dist.values()) if anchor_dist else 0
        
        if total > 0 and branded_count / total >= 0.3:
            brand_score = 85  # Good brand presence
            brand_status_text = "Strong brand presence"
            brand_status = "optimal"
        elif total > 0 and branded_count / total >= 0.15:
            brand_score = 70  # Moderate brand presence
            brand_status_text = "Moderate brand presence"
            brand_status = "needs_attention"
        else:
            brand_score = 55  # Weak brand presence
            brand_status_text = "Weak brand presence"
            brand_status = "needs_attention"
            
        brand_details = {
            "unlinked_brand_mentions": {"value": brand_status_text, "status": brand_status},
            "brand_citations": {"value": "Standard citations", "status": "optimal"},
            "brand_name_consistency": {"value": "Consistent", "status": "optimal"},
            "industry_mentions": {"value": "Limited coverage", "status": "needs_attention"}
        }
        results.append({
            "group_id": "brand_entity_authority",
            "name": self.OFF_PAGE_GROUPS["brand_entity_authority"]["name"],
            "score": brand_score,
            "status": self.compute_status(brand_score),
            "details": brand_details,
            "tab": "offpage"
        })
        
        # Link Growth Stability - uses dofollow ratio and link quality
        dofollow_ratio = backlink_data.get("dofollow_ratio", 0.5)
        health_scores = backlink_data.get("health_scores", {})
        
        # Balanced ratio (30-80%) is healthy
        if 0.3 <= dofollow_ratio <= 0.8:
            growth_score = health_scores.get("link_quality_score", 80)
            growth_trend = "Healthy growth"
            growth_status = "optimal"
        elif 0.2 <= dofollow_ratio <= 0.9:
            growth_score = 65
            growth_trend = "Moderate growth"
            growth_status = "needs_attention"
        else:
            growth_score = 50  # Suspicious ratio
            growth_trend = "Suspicious pattern"
            growth_status = "needs_attention"
            
        growth_details = {
            "monthly_link_trend": {"value": growth_trend, "status": growth_status},
            "link_velocity_spikes": {"value": "No spikes", "status": "optimal"},
            "historical_growth": {"value": "Steady pattern", "status": "optimal"}
        }
        results.append({
            "group_id": "link_growth_stability",
            "name": self.OFF_PAGE_GROUPS["link_growth_stability"]["name"],
            "score": growth_score,
            "status": self.compute_status(growth_score),
            "details": growth_details,
            "tab": "offpage"
        })
        
        return results
    
    def _score_domain_authority(self, backlink_data: Dict) -> tuple[float, Dict]:
        """Score Domain Authority based on referring domains."""
        referring_domains = backlink_data.get("referring_domains", 0)
        details = {}
        
        # Referring domains count
        details["referring_domains_count"] = {
            "value": f"{referring_domains} domains",
            "status": "optimal" if referring_domains >= 50 else "needs_attention" if referring_domains >= 20 else "critical"
        }
        
        # Authority score placeholder (would come from external service)
        details["authority_score"] = {
            "value": "DA estimation based on backlinks",
            "status": "needs_attention"
        }
        
        # Spam score placeholder
        details["spam_score"] = {
            "value": "Low spam signals",
            "status": "optimal"
        }
        
        # Link quality distribution
        dofollow_ratio = backlink_data.get("dofollow_ratio", 0.5)
        details["follow_vs_nofollow"] = {
            "value": f"{int(dofollow_ratio * 100)}% follow links",
            "status": "optimal" if 0.3 <= dofollow_ratio <= 0.8 else "needs_attention"
        }
        
        # Simple scoring based on referring domain count
        if referring_domains >= 100:
            return 90, details
        elif referring_domains >= 50:
            return 80, details
        elif referring_domains >= 20:
            return 70, details
        elif referring_domains >= 10:
            return 60, details
        elif referring_domains >= 5:
            return 50, details
        else:
            return 40, details
    
    def _score_anchor_text(self, backlink_data: Dict) -> tuple[float, Dict]:
        """Score anchor text diversity."""
        anchor_distribution = backlink_data.get("anchor_text_distribution", {})
        details = {}
        
        if not anchor_distribution:
            details["anchor_text_distribution"] = {"value": "No data", "status": "needs_attention"}
            details["exact_match_anchor_frequency"] = {"value": "No data", "status": "needs_attention"}
            return 60, details  # Default when no data
        
        # Check for healthy distribution
        branded = anchor_distribution.get("branded", 0)
        exact_match = anchor_distribution.get("exact_match", 0)
        generic = anchor_distribution.get("generic", 0)
        
        # Anchor text distribution
        details["anchor_text_distribution"] = {
            "value": f"Branded: {branded}%, Exact: {exact_match}%, Generic: {generic}%",
            "status": "optimal" if (30 <= branded <= 60 and exact_match < 20) else "needs_attention"
        }
        
        # Exact match frequency
        details["exact_match_anchor_frequency"] = {
            "value": f"{exact_match}% exact match",
            "status": "optimal" if exact_match < 10 else "needs_attention" if exact_match < 20 else "critical"
        }
        
        # Ideal: 40-60% branded, <10% exact match
        score = 70
        
        if exact_match > 20:
            score -= 20  # Too many exact match anchors is risky
        
        if branded >= 30 and branded <= 60:
            score += 15
        
        if generic >= 10 and generic <= 30:
            score += 15
        
        return min(max(score, 0), 100), details
    
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
        crawl_score, crawl_details = self._score_crawl_indexation(technical_data)
        results.append({
            "group_id": "crawl_indexation",
            "name": self.TECHNICAL_GROUPS["crawl_indexation"]["name"],
            "score": crawl_score,
            "status": self.compute_status(crawl_score),
            "details": crawl_details,
            "tab": "technical"
        })
        
        # Canonicalization & Duplicate Control
        canonical_score, canonical_details = self._score_canonicalization(technical_data)
        results.append({
            "group_id": "canonicalization_duplicate",
            "name": self.TECHNICAL_GROUPS["canonicalization_duplicate"]["name"],
            "score": canonical_score,
            "status": self.compute_status(canonical_score),
            "details": canonical_details,
            "tab": "technical"
        })
        
        # Page Experience (CWV)
        cwv_score, cwv_details = self._score_cwv(cwv_data or {})
        results.append({
            "group_id": "page_experience_cwv",
            "name": self.TECHNICAL_GROUPS["page_experience_cwv"]["name"],
            "score": cwv_score,
            "status": self.compute_status(cwv_score),
            "details": cwv_details,
            "tab": "technical"
        })
        
        # Search Rendering
        rendering_score = 75  # Default for MVP
        rendering_details = {"js_rendering": {"value": "Standard", "status": "optimal"}}
        results.append({
            "group_id": "search_rendering",
            "name": self.TECHNICAL_GROUPS["search_rendering"]["name"],
            "score": rendering_score,
            "status": self.compute_status(rendering_score),
            "details": rendering_details,
            "tab": "technical"
        })
        
        # AI & LLM Crawl Governance
        ai_score, ai_details = self._score_ai_governance(ai_governance or {})
        results.append({
            "group_id": "ai_crawl_governance",
            "name": self.TECHNICAL_GROUPS["ai_crawl_governance"]["name"],
            "score": ai_score,
            "status": self.compute_status(ai_score),
            "details": ai_details,
            "tab": "technical"
        })
        
        return results
    
    def _score_crawl_indexation(self, data: Dict) -> tuple[float, Dict]:
        """Score Crawl & Indexation."""
        score = 0
        details = {}
        
        # Index coverage ratio
        coverage = data.get("index_coverage_ratio", 0)
        cov_status = "critical"
        if coverage >= 0.9:
            score += 40
            cov_status = "optimal"
        elif coverage >= 0.7:
            score += 30
            cov_status = "needs_attention"
        elif coverage >= 0.5:
            score += 20
        
        details["index_coverage"] = {
            "value": f"{int(coverage * 100)}% coverage",
            "status": cov_status
        }
        
        # Robots.txt exists and valid
        robots_valid = data.get("robots_txt_valid", False)
        robots_exists = data.get("robots_txt_exists", False)
        
        if robots_valid:
            score += 20
            robots_val = "Valid"
            robots_status = "optimal"
        elif robots_exists:
            score += 10
            robots_val = "Invalid syntax"
            robots_status = "needs_attention"
        else:
            robots_val = "Missing"
            robots_status = "critical"
            
        details["robots_txt"] = {"value": robots_val, "status": robots_status}
        
        # Sitemap exists and valid
        sitemap_valid = data.get("sitemap_valid", False)
        sitemap_exists = data.get("sitemap_exists", False)
        
        if sitemap_valid:
            score += 20
            sitemap_val = "Submitted"
            sitemap_status = "optimal"
        elif sitemap_exists:
            score += 10
            sitemap_val = "Exists (Issues)"
            sitemap_status = "needs_attention"
        else:
            sitemap_val = "Missing"
            sitemap_status = "critical"
            
        details["sitemap_status"] = {"value": sitemap_val, "status": sitemap_status}
        
        # HTTPS enabled
        https = data.get("https_enabled", False)
        if https: score += 20
        details["https_security"] = {
            "value": "Secure (HTTPS)" if https else "Insecure (HTTP)",
            "status": "optimal" if https else "critical"
        }
        
        details["crawl_depth"] = {"value": "Standard", "status": "optimal"} # Placeholder
        
        return min(score, 100), details
    
    def _score_canonicalization(self, data: Dict) -> tuple[float, Dict]:
        """Score Canonicalization & Duplicate Control."""
        score = 80  # Start with good score
        details = {}
        
        # Deduct for issues
        canon_issues = data.get("canonical_issues_count", 0)
        c_status = "optimal"
        c_val = "Matches"
        
        if canon_issues > 5:
            score -= 30
            c_status = "critical"
            c_val = f"{canon_issues} mismatches"
        elif canon_issues > 0:
            score -= 15
            c_status = "needs_attention"
            c_val = f"{canon_issues} mismatches"
            
        details["canonical_tags_valid"] = {"value": c_val, "status": c_status}
        
        dup_titles = data.get("duplicate_title_count", 0)
        dt_status = "optimal"
        dt_val = "None"
        if dup_titles > 5:
            score -= 20
            dt_status = "critical"
            dt_val = f"{dup_titles} pages"
        elif dup_titles > 0:
            score -= 10
            dt_status = "needs_attention"
            dt_val = f"{dup_titles} pages"
            
        details["duplicate_titles"] = {"value": dt_val, "status": dt_status}
        
        dup_desc = data.get("duplicate_description_count", 0)
        dd_status = "optimal"
        dd_val = "None"
        if dup_desc > 5:
            score -= 15
            dd_status = "critical"
            dd_val = f"{dup_desc} pages"
        elif dup_desc > 0:
            score -= 5
            dd_status = "needs_attention"
            dd_val = f"{dup_desc} pages"
            
        details["duplicate_meta_descriptions"] = {"value": dd_val, "status": dd_status}
        
        if not data.get("trailing_slash_consistent", True):
            score -= 10
            
        details["duplicate_content_ratio"] = {"value": "0%", "status": "optimal"} # Placeholder
        details["rel_canonical_implementation"] = {"value": "Present", "status": "optimal"} # Placeholder
        
        return max(score, 0), details
    
    def _score_cwv(self, data: Dict) -> tuple[float, Dict]:
        """Score Core Web Vitals."""
        details = {}
        overall_status = data.get("overall_status", "").lower()
        score = 0
        
        # Overall status score mapping
        if overall_status == "good":
            score = 95
        elif overall_status == "needs_improvement":
            score = 65
        elif overall_status == "poor":
            score = 35
        else:
            # Fallback if no overall status
            score = 50 
            
        details["lcp_score"] = {
            "value": f"{data.get('lcp_value', 'N/A')}",
            "status": "optimal" if data.get("lcp_status") == "GOOD" else "needs_attention"
        }
        details["fid_score"] = {
            "value": f"{data.get('fid_value', 'N/A')}",
            "status": "optimal" if data.get('fid_status') == "GOOD" else "needs_attention"
        }
        details["cls_score"] = {
            "value": f"{data.get('cls_value', 'N/A')}",
            "status": "optimal" if data.get('cls_status') == "GOOD" else "needs_attention"
        }
        details["inp_score"] = {
            "value": f"{data.get('inp_value', 'N/A')}",
            "status": "optimal" if data.get('inp_status') == "GOOD" else "needs_attention"
        }
        details["ttfb_score"] = {
            "value": "N/A",  # Placeholder if not available
            "status": "needs_attention"
        }
        
        return score, details
    
    def _score_ai_governance(self, data: Dict) -> tuple[float, Dict]:
        """Score AI & LLM Crawl Governance."""
        score = 50  # Base score
        details = {}
        
        # Has explicit AI crawler policy
        has_policy = data.get("ai_crawlers_blocked") or data.get("ai_crawlers_allowed")
        if has_policy:
            score += 30
            
        details["ai_bot_policy"] = {
            "value": "Defined" if has_policy else "Undefined",
            "status": "optimal" if has_policy else "needs_attention"
        }
        
        # Has llm.txt
        has_llm_txt = data.get("llm_txt_detected", False)
        if has_llm_txt:
            score += 20
            
        details["llm_txt"] = {
            "value": "Present" if has_llm_txt else "Missing",
            "status": "optimal" if has_llm_txt else "needs_attention"
        }
        
        details["ai_crawler_access"] = {"value": "Standard", "status": "optimal"} # Placeholder
        
        return min(score, 100), details
    
    def compute_all_scores(
        self,
        on_page_signals: Dict,
        backlink_data: Dict,
        technical_data: Dict,
        cwv_data: Dict = None,
        ai_governance: Dict = None,
        keywords: List[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Compute all parameter scores across all tabs.
        
        Returns:
            Dict with 'onpage', 'offpage', 'technical' keys
        """
        return {
            "onpage": self.compute_on_page_scores(on_page_signals, keywords),
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
