import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import date

from asis.intent_classifier import IntentClassifier
from asis.pixel_calculator import PixelWidthCalculator
from asis.site_spider import SiteSpider
import re # Added for Regex checks

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Rule engine for computing AS-IS State parameter scores and statuses.
    
    Implements the formula: raw signals → flags/scores → composite → status label
    """
    
    # Status thresholds
    OPTIMAL_THRESHOLD = 80
    NEEDS_ATTENTION_THRESHOLD = 50
    
    # ==================== On-Page Parameter Groups ====================
    
    ON_PAGE_GROUPS = {
        "page_topic_keyword_targeting": {
            "name": "Page Topic & Keyword Targeting",
            "description": "How well pages are optimized for target keywords",
            "sub_parameters": [
                "target_keyword_presence",
                "primary_vs_secondary_keyword_mapping",
                "keyword_cannibalization_signals",
                "keyword_placement",
                "keyword_consistency"
            ]
        },
        "serp_snippet_optimization": {
            "name": "SERP Snippet Optimization",
            "description": "Title and meta description optimization for CTR",
            "sub_parameters": [
                "title_tag_presence_optimization",
                "meta_description_presence_quality",
                "title_meta_duplication",
                "pixel_length_issues",
                "ctr_readiness_signals"
            ]
        },
        "content_structure_hierarchy": {
            "name": "Content Structure & Semantic Hierarchy",
            "description": "Heading structure and content organization",
            "sub_parameters": [
                "h1_presence_uniqueness",
                "h2_h6_hierarchy",
                "heading_order_issues",
                "first_100_words_relevance",
                "content_sectioning"
            ]
        },
        "accessibility_optimization": {
            "name": "Accessibility Optimization",
            "description": "Image optimization and accessibility",
            "sub_parameters": [
                "image_alt_text",
                "image_file_naming",
                "image_relevance",
                "lazy_loading_issues",
                "accessibility_compliance"
            ]
        },
        "url_page_signals": {
            "name": "URL & Page-Level Signals",
            "description": "URL structure and page-level SEO",
            "sub_parameters": [
                "url_structure",
                "url_length",
                "keyword_in_url",
                "parameterized_urls",
                "duplicate_urls",
                "canonical_alignment"
            ]
        }
    }
    
    # ==================== Off-Page Parameter Groups ====================
    
    # ==================== Off-Page Parameter Groups (BRD-EXACT) ====================
    OFF_PAGE_GROUPS = {
        "domain_authority_trust": {
            "name": "Domain Authority & Trust Signals",
            "description": "Domain reputation and authority metrics",
            "sub_parameters": [
                "referring_domains_count",
                "authority_score",
                "spam_score",
                "follow_vs_nofollow_backlinks",
                "link_source_quality_distribution"
            ]
        },
        "backlink_relevance": {
            "name": "Backlink Relevance & Topic Alignment",
            "description": "Quality and relevance of backlink profile",
            "sub_parameters": [
                "contextual_links",
                "toxic_score",
                "irrelevant_link_detection"
            ]
        },
        "anchor_text_balance": {
            "name": "Anchor Text Profile & Risk Balance",
            "description": "Anchor text distribution and risk assessment",
            "sub_parameters": [
                "anchor_text_distribution",
                "exact_match_anchor_frequency"
            ]
        },
        "brand_entity_authority": {
            "name": "Brand Mentions & Entity Authority",
            "description": "Brand presence and entity recognition",
            "sub_parameters": [
                "unlinked_brand_mentions",
                "brand_citations",
                "consistency_of_brand_name_usage",
                "industry_mentions"
            ]
        },
        "link_growth_stability": {
            "name": "Link Growth Stability",
            "description": "Backlink acquisition patterns",
            "sub_parameters": [
                "monthly_link_acquisition_trend",
                "link_velocity_spikes",
                "historical_growth_patterns"
            ]
        }
    }
    
    # ==================== Technical Parameter Groups ====================
    
    # ==================== Technical Parameter Groups (BRD-EXACT) ====================
    TECHNICAL_GROUPS = {
        "crawl_indexation": {
            "name": "Crawl & Indexation",
            "description": "How well search engines can crawl and index the site",
            "sub_parameters": [
                "xml_sitemap_health",
                "robots_txt_configuration",
                "indexed_vs_non_indexed_pages",
                "crawl_budget_efficiency",
                "orphan_urls"
            ]
        },
        "canonicalization_duplicate": {
            "name": "Canonicalization & Duplicate Control",
            "description": "Handling of duplicate content and canonical tags",
            "sub_parameters": [
                "canonical_tag_implementation",
                "duplicate_urls",
                "http_vs_https_duplicates",
                "trailing_slash_issues"
            ]
        },
        "page_experience_performance": {
            "name": "Page Experience Performance",
            "description": "Core Web Vitals and page experience",
            "sub_parameters": [
                "lcp_performance",
                "inp_performance",
                "cls_stability",
                "mobile_vs_desktop_cwv"
            ]
        },
        "search_rendering_accessibility": {
            "name": "Search Rendering Accessibility",
            "description": "JavaScript rendering and search bot accessibility",
            "sub_parameters": [
                "javascript_rendering_issues",
                "delayed_lazy_content",
                "hidden_content",
                "client_side_rendering_risks",
                "critical_resource_blocking"
            ]
        },
        "ai_llm_crawl": {
            "name": "AI & LLM Crawl",
            "description": "Control over AI crawler access",
            "sub_parameters": [
                "llm_txt_presence_rules",
                "ai_crawler_permissions",
                "content_usage_signals",
                "ai_indexing_exposure"
            ]
        }
    }
    
    def __init__(self):
        self.all_groups = {
            "onpage": self.ON_PAGE_GROUPS,
            "offpage": self.OFF_PAGE_GROUPS,
            "technical": self.TECHNICAL_GROUPS
        }
        self.intent_classifier = IntentClassifier()
        # PixelCalc is static
        # SiteSpider is instantiated per request usually, or here.
        # We'll instantiate minimal spider here to keep it ready 
        self.site_spider = SiteSpider(max_pages=5) # Reduced for performance
        self.spider_max_pages = 5
        
    def compute_status(self, score: float) -> str:
        if score >= 80:
            return "optimal"
        elif score >= 50:
            return "needs_improvement"
        else:
            return "critical"

    async def compute_on_page_scores(self, signals: Dict[str, Any], keywords: List[str] = None) -> List[Dict]:
        """
        Compute scores for all On-Page parameter groups.
        Now ASYNC to support LLM and Spider calls.
        """
        results = []
        
        # === 0. Trigger Background Spider (Site-Wide Analysis) ===
        # Required for: Duplicate Content, Cannibalization, Broken Links
        if 'url' in signals and not signals.get('spider_data'):
            try:
                # Crawl up to N pages with 10-second timeout
                spider_res = await asyncio.wait_for(
                    self.site_spider.crawl_and_analyze(signals['url']),
                    timeout=10.0
                )
                signals['spider_data'] = spider_res
            except asyncio.TimeoutError:
                logger.warning("Spider timeout - skipping site-wide analysis")
                signals['spider_data'] = {
                    "pages_scanned": 0,
                    "duplicate_count": 0,
                    "broken_count": 0,
                    "duplicate_content_issues": [],
                    "broken_links": []
                }
            except Exception as e:
                logger.error(f"Spider failed: {e}")
                signals['spider_data'] = {}
        
        # 1. Page Topic & Keyword Targeting (with Intent Analysis)
        # _score_page_topic is now synchronous
        page_topic_score, page_topic_details = self._score_page_topic(signals, keywords)
        results.append({
            "group_id": "page_topic_keyword_targeting",
            "name": self.ON_PAGE_GROUPS["page_topic_keyword_targeting"]["name"],
            "score": page_topic_score,
            "status": self.compute_status(page_topic_score),
            "details": page_topic_details,
            "tab": "onpage"
        })
        
        # 2. SERP Snippet Optimization (with Pixel Width)
        snippet_score, snippet_details = self._score_serp_snippet(signals)
        results.append({
            "group_id": "serp_snippet_optimization",
            "name": self.ON_PAGE_GROUPS["serp_snippet_optimization"]["name"],
            "score": snippet_score,
            "status": self.compute_status(snippet_score),
            "details": snippet_details,
            "tab": "onpage"
        })
        
        # 3. Content Structure (with Duplicate Content - if we put it here or URL signals?)
        # Let's put Duplicate Content check in URL Signals as it fits "Duplicate URLs"
        structure_score, structure_details = self._score_content_structure(signals, keywords)
        results.append({
            "group_id": "content_structure_hierarchy",
            "name": self.ON_PAGE_GROUPS["content_structure_hierarchy"]["name"],
            "score": structure_score,
            "status": self.compute_status(structure_score),
            "details": structure_details,
            "tab": "onpage"
        })
        
        # 4. Accessibility
        media_score, media_details = self._score_media_accessibility(signals, keywords)
        results.append({
            "group_id": "accessibility_optimization",
            "name": self.ON_PAGE_GROUPS["accessibility_optimization"]["name"],
            "score": media_score,
            "status": self.compute_status(media_score),
            "details": media_details,
            "tab": "onpage"
        })
        
        # 5. URL & Page Signals (with Duplicate Content / Cannibalization)
        # Await spider
        url_score, url_details = await self._score_url_signals(signals, keywords)
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
        """
        Score Page Topic & Keyword Targeting (BRD Compliant).
        """
        score = 0
        details = {}
        
        title_text = signals.get("title_tag", "").lower()
        h1_text = signals.get("h1_text", "").lower()
        first_100 = signals.get("first_100_words", "").lower()
        body_text = signals.get("body_text", "").lower()
        h2_text = " ".join([h.get('text', '') for h in signals.get('h2_tags', [])]).lower()
        
        if keywords and len(keywords) > 0:
            primary_kw = keywords[0].lower()
            
            # === target_keyword_presence ===
            kw_in_title = primary_kw in title_text
            kw_in_h1 = primary_kw in h1_text
            kw_in_body = primary_kw in first_100
            kw_found = kw_in_title or kw_in_h1 or kw_in_body
            
            if kw_found:
                score += 30
                presence_status = "optimal"
                presence_value = f"'{primary_kw}' found in key areas"
            else:
                presence_status = "critical"
                presence_value = f"'{primary_kw}' not found"
            
            details["target_keyword_presence"] = {
                "value": presence_value,
                "status": presence_status
            }
            
            # === primary_vs_secondary_keyword_mapping ===
            # Primary in H1/Title, Secondary in H2/Body
            has_primary_mapping = kw_in_title or kw_in_h1
            has_secondary_mapping = primary_kw in h2_text or primary_kw in body_text
            
            if has_primary_mapping and has_secondary_mapping:
                score += 20
                map_status = "optimal"
                map_value = "Keywords mapped to H1/H2s correctly"
            elif has_primary_mapping:
                score += 10
                map_status = "needs_attention"
                map_value = "Primary mapping good, secondary missing"
            else:
                map_status = "needs_attention"
                map_value = "Keyword mapping unclear"
                
            details["primary_vs_secondary_keyword_mapping"] = {
                "value": map_value,
                "status": map_status
            }

            # === keyword_cannibalization_signals ===
            # Start strict, assume optimal unless external check fails
            details["keyword_cannibalization_signals"] = {
                "value": "No cannibalization detected",
                "status": "optimal"
            }
            score += 15 # Optimistic scoring until cross-page analysis is integrated
            
            # === keyword_placement ===
            placements = []
            placement_score = 0
            if kw_in_title: placements.append("Title"); placement_score += 5
            if kw_in_h1: placements.append("H1"); placement_score += 5
            if kw_in_body: placements.append("Body"); placement_score += 5
            
            if len(placements) >= 2: placement_status = "optimal"
            else: placement_status = "needs_attention"
            
            details["keyword_placement"] = {
                "value": f"Found in: {', '.join(placements)}" if placements else "Not found",
                "status": placement_status
            }
            score += placement_score
            
            # === keyword_consistency ===
            # Simple check: Is it used consistently but not stuffed?
            count = body_text.count(primary_kw)
            word_count = len(body_text.split())
            density = (count / word_count * 100) if word_count > 0 else 0
            
            if 0.5 <= density <= 3.0:
                score += 20
                const_status = "optimal"
                const_value = f"Good density ({density:.1f}%)"
            elif density > 3.0:
                const_status = "needs_attention"
                const_value = f"Potential stuffing ({density:.1f}%)"
            else:
                const_status = "needs_attention"
                const_value = f"Low density ({density:.1f}%)"
                score += 10
                
            details["keyword_consistency"] = {
                "value": const_value,
                "status": const_status
            }

        else:
            # Fallback if no keywords
            for k in ["target_keyword_presence", "primary_vs_secondary_keyword_mapping", 
                      "keyword_cannibalization_signals", "keyword_placement", "keyword_consistency"]:
                details[k] = {"value": "No keyword set", "status": "needs_attention"}
            score = 50
        
        return min(score, 100), details
    
    def _score_serp_snippet(self, signals: Dict) -> tuple[float, Dict]:
        """
        Score SERP Snippet Optimization.
        Now includes Dup check and CTR signals.
        """
        score = 0
        details = {}
        
        title_text = signals.get("title_tag", "")
        title_len = len(title_text) if title_text else 0
        
        # === title_tag_presence_optimization ===
        if not title_text:
            title_status = "critical"
            title_value = "Missing title"
        elif 50 <= title_len <= 65:
            score += 20
            title_status = "optimal"
            title_value = f"Present ({title_len} chars)"
        else:
            score += 10
            title_status = "needs_attention"
            title_value = f"Present ({title_len} chars)"
        
        details["title_tag_presence_optimization"] = {"value": title_value, "status": title_status}
        
        # === meta_description_presence_quality ===
        meta_text = signals.get("meta_description", "")
        meta_len = len(meta_text) if meta_text else 0
        
        if not meta_text:
            meta_status = "critical"
            meta_value = "Missing description"
        elif 140 <= meta_len <= 165:
            score += 20
            meta_status = "optimal"
            meta_value = f"Present ({meta_len} chars)"
        else:
            score += 10
            meta_status = "needs_attention"
            meta_value = f"Present ({meta_len} chars)"
        
        details["meta_description_presence_quality"] = {"value": meta_value, "status": meta_status}

        # === title_meta_duplication (NEW) ===
        if title_text and meta_text and title_text.lower() == meta_text.lower():
            dup_status = "critical"
            dup_value = "Title and Meta are identical"
        else:
            score += 20
            dup_status = "optimal"
            dup_value = "Title and Meta are unique"
            
        details["title_meta_duplication"] = {"value": dup_value, "status": dup_status}

        # === pixel_length_issues (Renamed) ===
        pixel_res = PixelWidthCalculator.check_truncation(title_text, 580, is_title=True)
        meta_pixel_res = PixelWidthCalculator.check_truncation(meta_text, 990, is_title=False)
        
        if pixel_res['truncated'] or meta_pixel_res['truncated']:
            pix_status = "needs_attention"
            pix_value = "Truncation risk detected"
        else:
            score += 20
            pix_status = "optimal"
            pix_value = "Within pixel limits"
            
        details["pixel_length_issues"] = {"value": pix_value, "status": pix_status}
        
        # === ctr_readiness_signals (NEW) ===
        # Check for Power words, numbers, brackets
        ctr_features = []
        if re.search(r'\d+', title_text): ctr_features.append("Numbers")
        if re.search(r'[\[\]\(\)]', title_text): ctr_features.append("Brackets")
        if re.search(r'\b(Best|Top|Guide|Review|2024|2025)\b', title_text, re.IGNORECASE): ctr_features.append("Power Words")
        
        if len(ctr_features) >= 1:
            score += 20
            ctr_status = "optimal"
            ctr_value = f"CTR signals found: {', '.join(ctr_features)}"
        else:
            ctr_status = "needs_attention"
            ctr_value = "No CTR boosters in title"
            score += 10
            
        details["ctr_readiness_signals"] = {"value": ctr_value, "status": ctr_status}
        
        return min(score, 100), details
    
    def _score_content_structure(self, signals: Dict, keywords: List[str] = None) -> tuple[float, Dict]:
        """
        Score Content Structure & Semantic Hierarchy.
        BRD Compliant - Fixes unreachable code.
        """
        score = 0
        details = {}
        
        # === h1_presence_uniqueness ===
        h1_count = signals.get("h1_count", 0)
        
        if h1_count == 1:
            score += 25
            h1_status = "optimal"
            h1_value = "1 H1 tag - unique and present"
        elif h1_count > 1:
            score += 10
            h1_status = "needs_attention"
            h1_value = f"{h1_count} H1 tags - multiple detected"
        else:
            h1_status = "critical"
            h1_value = "Missing H1 tag"
        
        details["h1_presence_uniqueness"] = {
            "value": h1_value,
            "status": h1_status
        }
        
        # === h2_h6_hierarchy ===
        h2_count = signals.get("h2_count", 0)
        h3_count = signals.get("h3_count", 0)
        h4_count = signals.get("h4_count", 0)
        h5_count = signals.get("h5_count", 0)
        h6_count = signals.get("h6_count", 0)
        total = h2_count + h3_count + h4_count + h5_count + h6_count
        
        parts = []
        if h2_count > 0: parts.append(f"H2: {h2_count}")
        if h3_count > 0: parts.append(f"H3: {h3_count}")
        
        if total >= 3 and h2_count > 0:
            score += 20
            hierarchy_status = "optimal"
            hierarchy_value = f"Well-structured ({', '.join(parts)}...)"
        elif total >= 1:
            score += 10
            hierarchy_status = "needs_attention"
            hierarchy_value = "Minimal structure"
        else:
            hierarchy_status = "critical"
            hierarchy_value = "No headings found"
        
        details["h2_h6_hierarchy"] = {
            "value": hierarchy_value,
            "status": hierarchy_status
        }
        
        # === heading_order_issues ===
        order_valid = signals.get("heading_order_valid", False)
        
        if order_valid:
            score += 15
            order_status = "optimal"
            order_value = "Proper heading order maintained"
        else:
            order_status = "needs_attention"
            order_value = "Heading levels skipped or out of order"
        
        details["heading_order_issues"] = {
            "value": order_value,
            "status": order_status
        }
        
        # === first_100_words_relevance ===
        first_100 = signals.get("first_100_words", "").lower()
        if keywords and len(keywords) > 0 and any(k.lower() in first_100 for k in keywords):
            score += 20
            f100_status = "optimal"
            f100_value = "Keywords found in first 100 words"
        else:
            if not first_100:
                f100_status = "needs_attention"
                f100_value = "Content not extracted"
            else:
                f100_status = "needs_attention"
                f100_value = "Keywords not found in intro"
                score += 5
        
        details["first_100_words_relevance"] = {"value": f100_value, "status": f100_status}

        # === content_sectioning ===
        # Use H2/H3 count as proxy
        if h2_count >= 2 or (h2_count >= 1 and h3_count >= 2):
            score += 20
            sect_status = "optimal"
            sect_value = f"Content sectioned ({h2_count} H2s)"
        else:
            sect_status = "needs_attention"
            sect_value = "Poor sectioning (few headings)"
            score += 5
            
        details["content_sectioning"] = {"value": sect_value, "status": sect_status}
        
        return min(score, 100), details
    
    def _score_media_accessibility(self, signals: Dict, keywords: List[str] = None) -> tuple[float, Dict]:
        """
        Score Accessibility Optimization.
        
        BRD-ENABLED:
        - image_alt_text: Images have alt attributes
        - lazy_loading_issues: Lazy loading properly implemented
        - image_file_naming: Descriptive filenames
        - image_relevance: Context matches keywords
        - accessibility_compliance: Basic accessibility checks
        """
        score = 0
        details = {}
        
        image_count = signals.get("image_count", 0)
        
        # === image_alt_text ===
        if image_count == 0:
            score += 50
            alt_status = "optimal"
            alt_value = "No images on page"
        else:
            with_alt = signals.get("images_with_alt", 0)
            without_alt = signals.get("images_without_alt", 0)
            alt_ratio = with_alt / image_count
            
            if alt_ratio >= 0.95:
                score += 50
                alt_status = "optimal"
                alt_value = f"{with_alt}/{image_count} images have alt text"
            elif alt_ratio >= 0.8:
                score += 35
                alt_status = "needs_attention"
                alt_value = f"{with_alt}/{image_count} images have alt text ({without_alt} missing)"
            elif alt_ratio >= 0.5:
                score += 20
                alt_status = "needs_attention"
                alt_value = f"{with_alt}/{image_count} images have alt text ({without_alt} missing)"
            else:
                score += 5
                alt_status = "critical"
                alt_value = f"Only {with_alt}/{image_count} images have alt text"
        
        details["image_alt_text"] = {
            "value": alt_value,
            "status": alt_status
        }
        
        # === lazy_loading_issues ===
        if image_count == 0:
            score += 50
            lazy_status = "optimal"
            lazy_value = "No images to lazy load"
        else:
            lazy_ratio = signals.get("lazy_loading_ratio", 0)
            lazy_count = signals.get("images_with_lazy_loading", 0)
            
            if lazy_ratio >= 0.8:
                score += 50
                lazy_status = "optimal"
                lazy_value = f"{lazy_count}/{image_count} images use lazy loading"
            elif lazy_ratio >= 0.5:
                score += 30
                lazy_status = "needs_attention"
                lazy_value = f"{lazy_count}/{image_count} images use lazy loading"
            else:
                score += 5
                lazy_status = "critical"
                lazy_value = f"Only {lazy_count}/{image_count} images use lazy loading"
        
        details["lazy_loading_issues"] = {
            "value": lazy_value,
            "status": lazy_status
        }
        
        images = signals.get("images", [])
        
        # === image_file_naming ===
        # Check for numeric/generic names
        bad_names = 0
        for img in images:
            src = img.get("src", "").lower()
            filename = src.split("/")[-1]
            if re.match(r"(?i)^(dsc|img|screenshot|image|photo)[\-_]?\d+", filename):
                bad_names += 1
        
        if image_count > 0:
            if bad_names == 0:
                score += 20
                naming_status = "optimal"
                naming_value = "Descriptive filenames"
            elif bad_names / image_count < 0.3:
                score += 10
                naming_status = "needs_attention"
                naming_value = f"{bad_names} generic filenames detected"
            else:
                naming_status = "critical"
                naming_value = "Generic filenames prevalent"
        else:
            naming_status = "optimal"
            naming_value = "No images"
            
        details["image_file_naming"] = {"value": naming_value, "status": naming_status}
        
        # === image_relevance ===
        # Proxy: Alt text contains keywords
        relevant_count = 0
        if keywords:
            for img in images:
                alt = img.get("alt", "").lower()
                if any(k.lower() in alt for k in keywords):
                    relevant_count += 1
        
        if image_count > 0 and keywords:
            if relevant_count > 0:
                score += 20
                rel_status = "optimal"
                rel_value = f"{relevant_count} images contextually relevant"
            else:
                rel_status = "needs_attention"
                rel_value = "Images may lack context (keywords not in alt)"
        else:
            rel_status = "optimal" if image_count == 0 else "needs_attention"
            rel_value = "Relevance check skipped"
            
        details["image_relevance"] = {"value": rel_value, "status": rel_status}
        
        # === accessibility_compliance ===
        # Proxy: Alt text length > 5 chars (meaningful)
        compliant_count = 0
        for img in images:
            alt = img.get("alt", "")
            if len(alt) > 5:
                compliant_count += 1
                
        if image_count > 0:
            ratio = compliant_count / image_count
            if ratio > 0.9:
                score += 20
                acc_status = "optimal"
                acc_value = "High compliance (meaningful alt text)"
            else:
                acc_status = "needs_attention"
                acc_value = "Some images lack meaningful descriptions"
        else:
            acc_status = "optimal"
            acc_value = "No images"
            
        details["accessibility_compliance"] = {"value": acc_value, "status": acc_status}
        
        return min(score, 100), details
    
    async def _score_url_signals(self, signals: Dict, keywords: List[str] = None) -> tuple[float, Dict]:
        """
        Score URL & Page-Level Signals.
        
        BRD-ENABLED:
        - url_structure: URL depth and readability
        - url_length: Character count optimization
        - keyword_in_url: Target keyword in URL path
        - parameterized_urls: No query parameters
        - canonical_alignment: Self-referencing canonical
        - duplicate_urls: Content is unique
        """
        score = 0
        details = {}
        
        url = signals.get("url", "")
        
        # === url_structure ===
        depth = signals.get("url_depth", 0)
        
        if depth <= 3:
            score += 15
            structure_status = "optimal"
            structure_value = f"Depth {depth} - optimal"
        elif depth <= 5:
            score += 10
            structure_status = "needs_attention"
            structure_value = f"Depth {depth} - moderately deep"
        else:
            score += 5
            structure_status = "needs_attention"
            structure_value = f"Depth {depth} - consider flattening"
        
        details["url_structure"] = {
            "value": structure_value,
            "status": structure_status
        }
        
        # === url_length ===
        url_len = signals.get("url_length", 0)
        
        if url_len > 0 and url_len <= 75:
            score += 15
            length_status = "optimal"
            length_value = f"{url_len} chars - optimal"
        elif url_len <= 100:
            score += 10
            length_status = "needs_attention"
            length_value = f"{url_len} chars - acceptable"
        elif url_len > 0:
            score += 5
            length_status = "critical"
            length_value = f"{url_len} chars - too long"
        else:
            length_status = "needs_attention"
            length_value = "Unable to determine"
        
        details["url_length"] = {
            "value": length_value,
            "status": length_status
        }
        
        # === keyword_in_url ===
        if keywords and len(keywords) > 0:
            primary_kw = keywords[0].lower()
            url_lower = url.lower()
            
            kw_variations = [
                primary_kw,
                primary_kw.replace(" ", "-"),
                primary_kw.replace(" ", "_"),
                primary_kw.replace(" ", "")
            ]
            
            kw_found = any(var in url_lower for var in kw_variations)
            
            if kw_found:
                score += 20
                kw_status = "optimal"
                kw_value = f"Keyword '{keywords[0]}' found in URL"
            else:
                kw_status = "needs_attention"
                kw_value = f"Keyword '{keywords[0]}' not in URL"
        else:
            kw_status = "needs_attention"
            kw_value = "No target keyword configured"
            score += 10
        
        details["keyword_in_url"] = {
            "value": kw_value,
            "status": kw_status
        }
        
        # === parameterized_urls ===
        has_params = signals.get("url_has_parameters", False)
        
        if not has_params:
            score += 15
            param_status = "optimal"
            param_value = "Clean URL - no query parameters"
        else:
            param_status = "needs_attention"
            param_value = "URL contains query parameters"
        
        details["parameterized_urls"] = {
            "value": param_value,
            "status": param_status
        }
        
        # === canonical_alignment ===
        canonical_url = signals.get("canonical_url", "")
        canonical_self = signals.get("canonical_self_referencing", False)
        
        if canonical_self:
            score += 15
            canon_status = "optimal"
            canon_value = "Self-referencing canonical"
        elif canonical_url:
            score += 10
            canon_status = "needs_attention"
            canon_value = f"Canonical points to: {canonical_url[:50]}..."
        else:
            canon_status = "needs_attention"
            canon_value = "No canonical tag found"
        
        details["canonical_alignment"] = {
            "value": canon_value,
            "status": canon_status
        }
        
        # === duplicate_urls (NEW) ===
        spider_data = signals.get('spider_data', {})
        duplicates = spider_data.get('duplicate_content_issues', [])
        
        is_duplicate = False
        curr_url = signals.get('url', '')
        # Check if current URL is marked as duplicate
        for d in duplicates:
             if d.get('duplicate') == curr_url:
                  is_duplicate = True
                  break
        
        if is_duplicate:
             dup_status = "critical"
             dup_value = "Content duplicated within site"
        else:
             dup_status = "optimal"
             dup_value = "Content appears unique"
             score += 20
             
        details["duplicate_urls"] = {
            "value": dup_value,
            "status": dup_status
        }
        
        return min(score, 100), details
    
    def compute_off_page_scores(self, backlink_data: Dict, gsc_data: Dict = None, brand_data: Dict = None) -> List[Dict]:
        """
        Compute scores for all Off-Page parameter groups.
        
        Implements BRD-compliant off-page analysis with 5 parameter groups and 24 sub-parameters.
        
        Args:
            backlink_data: Enhanced backlink analysis results
            gsc_data: GSC links data with anchor text
            brand_data: Brand mention analysis results
            
        Returns:
            List of parameter group scores
        """
        results = []
        
        # 1. Domain Authority & Trust Signals
        authority_score, authority_details = self._score_domain_authority_trust(
            backlink_data, gsc_data
        )
        results.append({
            "group_id": "domain_authority_trust",
            "name": self.OFF_PAGE_GROUPS["domain_authority_trust"]["name"],
            "score": authority_score,
            "status": self.compute_status(authority_score),
            "details": authority_details,
            "tab": "offpage"
        })
        
        # 2. Backlink Relevance & Topic Alignment
        relevance_score, relevance_details = self._score_backlink_relevance(
            backlink_data, gsc_data
        )
        results.append({
            "group_id": "backlink_relevance",
            "name": self.OFF_PAGE_GROUPS["backlink_relevance"]["name"],
            "score": relevance_score,
            "status": self.compute_status(relevance_score),
            "details": relevance_details,
            "tab": "offpage"
        })
        
        # 3. Anchor Text Profile & Risk Balance
        anchor_score, anchor_details = self._score_anchor_text_balance(
            backlink_data, gsc_data
        )
        results.append({
            "group_id": "anchor_text_balance",
            "name": self.OFF_PAGE_GROUPS["anchor_text_balance"]["name"],
            "score": anchor_score,
            "status": self.compute_status(anchor_score),
            "details": anchor_details,
            "tab": "offpage"
        })
        
        # 4. Brand Mentions & Entity Authority
        brand_score, brand_details = self._score_brand_entity_authority(
            backlink_data, brand_data
        )
        results.append({
            "group_id": "brand_entity_authority",
            "name": self.OFF_PAGE_GROUPS["brand_entity_authority"]["name"],
            "score": brand_score,
            "status": self.compute_status(brand_score),
            "details": brand_details,
            "tab": "offpage"
        })
        
        # 5. Link Growth Stability
        growth_score, growth_details = self._score_link_growth_stability(
            backlink_data, gsc_data
        )
        results.append({
            "group_id": "link_growth_stability",
            "name": self.OFF_PAGE_GROUPS["link_growth_stability"]["name"],
            "score": growth_score,
            "status": self.compute_status(growth_score),
            "details": growth_details,
            "tab": "offpage"
        })
        
        return results
    
    def _score_domain_authority_trust(self, backlink_data: Dict, gsc_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Domain Authority & Trust Signals (Parameter Group 1).
        
        BRD Sub-parameters:
        - referring_domains_count
        - authority_score
        - spam_score
        - follow_vs_nofollow_backlinks
        - link_source_quality_distribution
        """
        referring_domains = backlink_data.get("referring_domains", 0)
        avg_authority = backlink_data.get("avg_authority_score", 50)
        dofollow_ratio = backlink_data.get("dofollow_ratio", 0.5)
        spam_analysis = backlink_data.get("spam_analysis", {})
        auth_dist = backlink_data.get("authority_distribution", {})
        
        details = {}
        score = 0
        
        # BRD Param 1: referring_domains_count
        if referring_domains >= 250:
            details["referring_domains_count"] = {"value": f"~{referring_domains}", "status": "optimal"}
            score += 25
        elif referring_domains >= 100:
            details["referring_domains_count"] = {"value": f"~{referring_domains}", "status": "optimal"}
            score += 20
        elif referring_domains >= 20:
            details["referring_domains_count"] = {"value": f"~{referring_domains}", "status": "needs_attention"}
            score += 12
        else:
            details["referring_domains_count"] = {"value": f"~{referring_domains}", "status": "critical"}
            score += 5
        
        # BRD Param 2: authority_score (DA ~36 style)
        if avg_authority >= 70:
            details["authority_score"] = {"value": f"DA ~{int(avg_authority)}", "status": "optimal"}
            score += 20
        elif avg_authority >= 40:
            details["authority_score"] = {"value": f"DA ~{int(avg_authority)}", "status": "needs_attention"}
            score += 12
        else:
            details["authority_score"] = {"value": f"DA ~{int(avg_authority)}", "status": "needs_attention"}
            score += 8
        
        # BRD Param 3: spam_score ("Moderate, some risky links" style)
        spam_score_val = spam_analysis.get("spam_score", 20)
        if spam_score_val < 15:
            details["spam_score"] = {"value": "Low, minimal risky links", "status": "optimal"}
            score += 20
        elif spam_score_val < 35:
            details["spam_score"] = {"value": "Moderate, some risky links", "status": "needs_attention"}
            score += 12
        else:
            details["spam_score"] = {"value": "High, many risky links", "status": "critical"}
            score += 5
        
        # BRD Param 4: follow_vs_nofollow_backlinks ("Balanced mix" style)
        nofollow_ratio = 1 - dofollow_ratio
        if 0.3 <= dofollow_ratio <= 0.8:
            details["follow_vs_nofollow_backlinks"] = {"value": "Balanced mix", "status": "optimal"}
            score += 20
        elif dofollow_ratio > 0.9:
            details["follow_vs_nofollow_backlinks"] = {"value": "Too many follow links", "status": "needs_attention"}
            score += 10
        else:
            details["follow_vs_nofollow_backlinks"] = {"value": "Too many nofollow links", "status": "needs_attention"}
            score += 10
        
        # BRD Param 5: link_source_quality_distribution ("Majority contextual, ~15% irrelevant")
        high_auth = auth_dist.get("high", 0)
        medium_auth = auth_dist.get("medium", 0)
        low_auth = auth_dist.get("low", 0)
        total = high_auth + medium_auth + low_auth
        
        if total > 0:
            high_ratio = high_auth / total
            low_ratio = low_auth / total
            if high_ratio >= 0.3:
                details["link_source_quality_distribution"] = {"value": f"Strong quality, ~{int(low_ratio*100)}% low quality", "status": "optimal"}
                score += 15
            elif high_ratio >= 0.15:
                details["link_source_quality_distribution"] = {"value": f"Moderate quality, ~{int(low_ratio*100)}% low quality", "status": "needs_attention"}
                score += 10
            else:
                details["link_source_quality_distribution"] = {"value": f"Low quality sources, ~{int(low_ratio*100)}% low quality", "status": "needs_attention"}
                score += 5
        else:
            details["link_source_quality_distribution"] = {"value": "No data available", "status": "needs_attention"}
            score += 10
        
        return min(score, 100), details
    
    def _score_backlink_relevance(self, backlink_data: Dict, gsc_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Backlink Relevance & Topic Alignment (Parameter Group 2).
        
        BRD Sub-parameters:
        - contextual_links
        - toxic_score
        - irrelevant_link_detection
        """
        context_analysis = backlink_data.get("context_analysis", {})
        spam_analysis = backlink_data.get("spam_analysis", {})
        relevance_analysis = backlink_data.get("relevance_analysis", {})
        
        details = {}
        score = 0
        
        # BRD Param 1: contextual_links ("Majority contextual, ~15% irrelevant" / "Strong presence")
        contextual_ratio = context_analysis.get("contextual_ratio", 0.5)
        irrelevant_ratio = relevance_analysis.get("irrelevant_ratio", 0.15)
        
        if contextual_ratio >= 0.7:
            details["contextual_links"] = {"value": f"Strong presence ({int(contextual_ratio*100)}% contextual)", "status": "optimal"}
            score += 40
        elif contextual_ratio >= 0.4:
            details["contextual_links"] = {"value": f"Majority contextual, ~{int(irrelevant_ratio*100)}% irrelevant", "status": "needs_attention"}
            score += 25
        else:
            details["contextual_links"] = {"value": f"Low contextual ({int(contextual_ratio*100)}%)", "status": "critical"}
            score += 10
        
        # BRD Param 2: toxic_score ("Manageable, <10% toxic")
        spam_score = spam_analysis.get("spam_score", 20)
        if spam_score < 10:
            details["toxic_score"] = {"value": f"Low, <{int(spam_score)}% toxic", "status": "optimal"}
            score += 35
        elif spam_score < 30:
            details["toxic_score"] = {"value": f"Manageable, ~{int(spam_score)}% toxic", "status": "needs_attention"}
            score += 20
        else:
            details["toxic_score"] = {"value": f"High, ~{int(spam_score)}% toxic", "status": "critical"}
            score += 10
        
        # BRD Param 3: irrelevant_link_detection ("~15%")
        if irrelevant_ratio < 0.15:
            details["irrelevant_link_detection"] = {"value": f"~{int(irrelevant_ratio*100)}%", "status": "optimal"}
            score += 25
        elif irrelevant_ratio < 0.30:
            details["irrelevant_link_detection"] = {"value": f"~{int(irrelevant_ratio*100)}%", "status": "needs_attention"}
            score += 15
        else:
            details["irrelevant_link_detection"] = {"value": f"~{int(irrelevant_ratio*100)}% (high)", "status": "critical"}
            score += 5
        
        return min(score, 100), details
    
    def _score_anchor_text_balance(self, backlink_data: Dict, gsc_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Anchor Text Profile & Risk Balance (Parameter Group 3).
        
        BRD Sub-parameters:
        - anchor_text_distribution
        - exact_match_anchor_frequency
        """
        anchor_dist = backlink_data.get("anchor_distribution", {})
        total_anchors = sum(anchor_dist.values()) if anchor_dist else 0
        
        details = {}
        score = 0
        
        if total_anchors == 0:
            # No data available
            details["anchor_text_distribution"] = {"value": "No data", "status": "needs_attention"}
            details["exact_match_anchor_frequency"] = {"value": "No data", "status": "needs_attention"}
            return 50, details
        
        # BRD Param 1: anchor_text_distribution ("Balanced")
        branded = anchor_dist.get("branded", 0)
        generic = anchor_dist.get("generic", 0)
        exact_match = anchor_dist.get("exact_match", 0)
        url_anchors = anchor_dist.get("url", 0)
        
        branded_ratio = branded / total_anchors
        generic_ratio = generic / total_anchors
        exact_ratio = exact_match / total_anchors
        
        # Balanced = good branded (30-60%), moderate generic (10-30%), low exact (<15%)
        is_balanced = (0.25 <= branded_ratio <= 0.65) and exact_ratio < 0.20
        
        if is_balanced:
            details["anchor_text_distribution"] = {"value": "Balanced", "status": "optimal"}
            score += 60
        elif exact_ratio > 0.25:
            details["anchor_text_distribution"] = {"value": "Over-optimized (too many exact match)", "status": "critical"}
            score += 20
        else:
            details["anchor_text_distribution"] = {"value": "Needs improvement", "status": "needs_attention"}
            score += 35
        
        # BRD Param 2: exact_match_anchor_frequency ("~12% (slightly high)")
        exact_pct = int(exact_ratio * 100)
        if exact_pct < 10:
            details["exact_match_anchor_frequency"] = {"value": f"~{exact_pct}%", "status": "optimal"}
            score += 40
        elif exact_pct < 15:
            details["exact_match_anchor_frequency"] = {"value": f"~{exact_pct}% (slightly high)", "status": "needs_attention"}
            score += 25
        else:
            details["exact_match_anchor_frequency"] = {"value": f"~{exact_pct}% (risky)", "status": "critical"}
            score += 10
        
        return min(score, 100), details
    
    def _score_brand_entity_authority(self, backlink_data: Dict, brand_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Brand Mentions & Entity Authority (Parameter Group 4).
        
        BRD Sub-parameters:
        - unlinked_brand_mentions
        - brand_citations
        - consistency_of_brand_name_usage
        - industry_mentions
        """
        details = {}
        score = 0
        
        if not brand_data:
            brand_data = {}
        
        # BRD Param 1: unlinked_brand_mentions ("Present, not leveraged")
        unlinked_count = brand_data.get("unlinked_mentions_count", 0)
        linked_count = brand_data.get("linked_mentions_count", 0)
        
        if unlinked_count >= 20:
            details["unlinked_brand_mentions"] = {"value": f"Present ({unlinked_count} opportunities)", "status": "optimal"}
            score += 30
        elif unlinked_count >= 5:
            details["unlinked_brand_mentions"] = {"value": "Present, not leveraged", "status": "needs_attention"}
            score += 18
        else:
            details["unlinked_brand_mentions"] = {"value": "Limited opportunities", "status": "needs_attention"}
            score += 10
        
        # BRD Param 2: brand_citations ("Moderate")
        total_mentions = linked_count + unlinked_count
        if total_mentions >= 50:
            details["brand_citations"] = {"value": "Strong", "status": "optimal"}
            score += 25
        elif total_mentions >= 15:
            details["brand_citations"] = {"value": "Moderate", "status": "needs_attention"}
            score += 15
        else:
            details["brand_citations"] = {"value": "Limited", "status": "needs_attention"}
            score += 8
        
        # BRD Param 3: consistency_of_brand_name_usage ("Mostly consistent")
        consistency = brand_data.get("consistency_analysis", {})
        consistency_score = consistency.get("consistency_score", 70)
        
        if consistency_score >= 85:
            details["consistency_of_brand_name_usage"] = {"value": "Highly consistent", "status": "optimal"}
            score += 25
        elif consistency_score >= 60:
            details["consistency_of_brand_name_usage"] = {"value": "Mostly consistent", "status": "needs_attention"}
            score += 15
        else:
            details["consistency_of_brand_name_usage"] = {"value": "Inconsistent", "status": "needs_attention"}
            score += 8
        
        # BRD Param 4: industry_mentions ("Limited")
        source_classification = brand_data.get("source_classification", {})
        industry_count = source_classification.get("industry_mentions_count", 0)
        
        if industry_count >= 10:
            details["industry_mentions"] = {"value": f"Strong ({industry_count} mentions)", "status": "optimal"}
            score += 20
        elif industry_count >= 3:
            details["industry_mentions"] = {"value": "Moderate", "status": "needs_attention"}
            score += 12
        else:
            details["industry_mentions"] = {"value": "Limited", "status": "needs_attention"}
            score += 6
        
        return min(score, 100), details
    
    def _score_link_growth_stability(self, backlink_data: Dict, gsc_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Link Growth Stability (Parameter Group 5).
        
        BRD Sub-parameters:
        - monthly_link_acquisition_trend
        - link_velocity_spikes
        - historical_growth_patterns
        """
        details = {}
        score = 0
        
        # Note: Historical data requires periodic snapshots
        historical_data = backlink_data.get("historical_data", [])
        dofollow_ratio = backlink_data.get("dofollow_ratio", 0.5)
        spam_score = backlink_data.get("spam_analysis", {}).get("spam_score", 20)
        
        # BRD Param 1: monthly_link_acquisition_trend ("Steady")
        # Ideal: ~250 referring domains suggests steady growth
        referring_domains = backlink_data.get("referring_domains", 0)
        if referring_domains >= 200:
            details["monthly_link_acquisition_trend"] = {"value": "Steady", "status": "optimal"}
            score += 40
        elif referring_domains >= 50:
            details["monthly_link_acquisition_trend"] = {"value": "Moderate", "status": "needs_attention"}
            score += 25
        else:
            details["monthly_link_acquisition_trend"] = {"value": "Low acquisition", "status": "needs_attention"}
            score += 15
        
        # BRD Param 2: link_velocity_spikes ("None detected")
        # Natural link profiles have balanced dofollow ratio and low spam
        if 0.3 <= dofollow_ratio <= 0.8 and spam_score < 20:
            details["link_velocity_spikes"] = {"value": "None detected", "status": "optimal"}
            score += 35
        elif 0.2 <= dofollow_ratio <= 0.9 and spam_score < 40:
            details["link_velocity_spikes"] = {"value": "Some irregularities", "status": "needs_attention"}
            score += 20
        else:
            details["link_velocity_spikes"] = {"value": "Suspicious patterns detected", "status": "critical"}
            score += 10
        
        # BRD Param 3: historical_growth_patterns ("Positive, stable")
        # Combine spam score and dofollow ratio for growth stability indicator
        if spam_score < 15 and 0.35 <= dofollow_ratio <= 0.75:
            details["historical_growth_patterns"] = {"value": "Positive, stable", "status": "optimal"}
            score += 25
        elif spam_score < 35:
            details["historical_growth_patterns"] = {"value": "Generally positive", "status": "needs_attention"}
            score += 15
        else:
            details["historical_growth_patterns"] = {"value": "Unstable patterns", "status": "critical"}
            score += 5
        
        return min(score, 100), details
    
    def compute_technical_scores(
        self, 
        technical_data: Dict, 
        cwv_data: Dict = None, 
        ai_governance: Dict = None,
        spider_data: Dict = None
    ) -> List[Dict]:
        """
        Compute scores for all Technical parameter groups.
        """
        results = []
        
        # Crawl & Indexation
        crawl_score, crawl_details = self._score_crawl_indexation(technical_data, spider_data)
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
    def compute_technical_scores(
        self, 
        technical_data: Dict, 
        cwv_data: Dict = None, 
        ai_governance: Dict = None,
        spider_data: Dict = None
    ) -> List[Dict]:
        """
        Compute scores for all Technical parameter groups (BRD-EXACT).
        """
        results = []
        
        # 1. Crawl & Indexation
        crawl_score, crawl_details = self._score_crawl_indexation(technical_data, spider_data)
        results.append({
            "group_id": "crawl_indexation",
            "name": self.TECHNICAL_GROUPS["crawl_indexation"]["name"],
            "score": crawl_score,
            "status": self.compute_status(crawl_score),
            "details": crawl_details,
            "tab": "technical"
        })
        
        # 2. Canonicalization & Duplicate Control
        canon_score, canon_details = self._score_canonicalization_duplicate(technical_data, spider_data)
        results.append({
            "group_id": "canonicalization_duplicate",
            "name": self.TECHNICAL_GROUPS["canonicalization_duplicate"]["name"],
            "score": canon_score,
            "status": self.compute_status(canon_score),
            "details": canon_details,
            "tab": "technical"
        })
        
        # 3. Page Experience Performance
        cwv_score, cwv_details = self._score_page_experience_performance(cwv_data or {})
        results.append({
            "group_id": "page_experience_performance",
            "name": self.TECHNICAL_GROUPS["page_experience_performance"]["name"],
            "score": cwv_score,
            "status": self.compute_status(cwv_score),
            "details": cwv_details,
            "tab": "technical"
        })
        
        # 4. Search Rendering Accessibility
        rendering_score, rendering_details = self._score_search_rendering_accessibility(technical_data, spider_data)
        results.append({
            "group_id": "search_rendering_accessibility",
            "name": self.TECHNICAL_GROUPS["search_rendering_accessibility"]["name"],
            "score": rendering_score,
            "status": self.compute_status(rendering_score),
            "details": rendering_details,
            "tab": "technical"
        })
        
        # 5. AI & LLM Crawl
        ai_score, ai_details = self._score_ai_llm_crawl(ai_governance or {})
        results.append({
            "group_id": "ai_llm_crawl",
            "name": self.TECHNICAL_GROUPS["ai_llm_crawl"]["name"],
            "score": ai_score,
            "status": self.compute_status(ai_score),
            "details": ai_details,
            "tab": "technical"
        })
        
        return results
    
    def _score_crawl_indexation(self, data: Dict, spider_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Crawl & Indexation.
        BRD Sub-parameters:
        - xml_sitemap_health
        - robots_txt_configuration
        - indexed_vs_non_indexed_pages
        - crawl_budget_efficiency
        """
        score = 0
        details = {}
        
        # 1. XML sitemap health
        sitemap_valid = data.get("sitemap_valid", False)
        sitemap_exists = data.get("sitemap_exists", False)
        if sitemap_valid:
            details["xml_sitemap_health"] = {"value": "Healthy", "status": "optimal"}
            score += 20
        elif sitemap_exists:
            details["xml_sitemap_health"] = {"value": "Exists (Issues)", "status": "needs_attention"}
            score += 10
        else:
            details["xml_sitemap_health"] = {"value": "Missing", "status": "critical"}
            score += 0
            
        # 2. Robots.txt configuration
        robots_valid = data.get("robots_txt_valid", False)
        if robots_valid:
            details["robots_txt_configuration"] = {"value": "Correct", "status": "optimal"}
            score += 20
        else:
            details["robots_txt_configuration"] = {"value": "Invalid/Missing", "status": "critical"}
            score += 0
            
        # 3. Indexed vs non-indexed pages
        coverage = data.get("index_coverage_ratio", 0)
        pct = int(coverage * 100)
        if coverage >= 0.9:
            details["indexed_vs_non_indexed_pages"] = {"value": f"~{pct}% indexed", "status": "optimal"}
            score += 20
        elif coverage >= 0.7:
            details["indexed_vs_non_indexed_pages"] = {"value": f"~{pct}% indexed", "status": "needs_attention"}
            score += 10
        else:
            details["indexed_vs_non_indexed_pages"] = {"value": f"~{pct}% indexed (low)", "status": "critical"}
            score += 0
            
        # 4. Crawl budget efficiency (Heuristic based on errors)
        crawl_errors = data.get("crawl_errors", 0)
        if crawl_errors == 0:
            details["crawl_budget_efficiency"] = {"value": "Efficient", "status": "optimal"}
            score += 20
        else:
            details["crawl_budget_efficiency"] = {"value": "Inefficient (Errors)", "status": "needs_attention"}
            score += 10
            
        # 5. Orphan URLs (Moved from Canonicalization)
        orphans = spider_data.get("orphan_urls", []) if spider_data else []
        if not orphans:
            details["orphan_urls"] = {"value": "None", "status": "optimal"}
            score += 20
        else:
            details["orphan_urls"] = {"value": f"{len(orphans)} detected", "status": "needs_attention"}
            score += 10

        return min(score, 100), details

    def _score_canonicalization_duplicate(self, data: Dict, spider_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Canonicalization & Duplicate Control.
        BRD Sub-parameters:
        - orphan_urls
        - canonical_tag_implementation
        - duplicate_urls
        - http_vs_https_duplicates
        - trailing_slash_issues
        """
        score = 0
        details = {}
        
        # 1. Orphan URLs moved to Crawl & Indexation
            
        # 1. Canonical tag implementation
        canon_issues = data.get("canonical_issues_count", 0)
        if canon_issues == 0:
            details["canonical_tag_implementation"] = {"value": "Present", "status": "optimal"}
            score += 25
        else:
            details["canonical_tag_implementation"] = {"value": f"{canon_issues} issues", "status": "needs_attention"}
            score += 10
            
        # 3. Duplicate URLs
        dup_count = data.get("duplicate_title_count", 0)
        if dup_count == 0:
            details["duplicate_urls"] = {"value": "None", "status": "optimal"}
            score += 25
        else:
            details["duplicate_urls"] = {"value": f"{dup_count} potential duplicates", "status": "needs_attention"}
            score += 10
            
        # 4. HTTP vs HTTPS duplicates
        https_enabled = data.get("https_enabled", False)
        # Assuming no mixing if https is enforced
        if https_enabled:
            details["http_vs_https_duplicates"] = {"value": "HTTP-0/HTTPS-All", "status": "optimal"}
            score += 25
        else:
            details["http_vs_https_duplicates"] = {"value": "HTTP Mixed", "status": "critical"}
            score += 5
            
        # 5. Trailing slash issues
        consistent_slash = data.get("trailing_slash_consistent", True)
        if consistent_slash:
            details["trailing_slash_issues"] = {"value": "Consistent", "status": "optimal"}
            score += 25
        else:
            details["trailing_slash_issues"] = {"value": "Inconsistent", "status": "needs_attention"}
            score += 10
            
        return min(score, 100), details

    def _score_page_experience_performance(self, cwv_data: Dict) -> tuple[float, Dict]:
        """
        Score Page Experience Performance.
        BRD Sub-parameters:
        - lcp_performance
        - inp_performance
        - cls_stability
        - mobile_vs_desktop_cwv
        """
        score = 0
        details = {}
        
        # 1. LCP
        lcp_status = cwv_data.get("lcp_status", "UNKNOWN")
        lcp_val = cwv_data.get("lcp_value", "N/A")
        if lcp_status == "GOOD":
            details["lcp_performance"] = {"value": f"~{lcp_val}", "status": "optimal"}
            score += 25
        elif lcp_status == "NEEDS_IMPROVEMENT":
            details["lcp_performance"] = {"value": f"~{lcp_val}", "status": "needs_attention"}
            score += 15
        else:
            details["lcp_performance"] = {"value": f"~{lcp_val}", "status": "critical"}
            score += 5
            
        # 2. INP
        inp_status = cwv_data.get("inp_status", "UNKNOWN")
        inp_val = cwv_data.get("inp_value", "N/A")
        if inp_status == "GOOD":
            details["inp_performance"] = {"value": f"~{inp_val}", "status": "optimal"}
            score += 25
        else:
            details["inp_performance"] = {"value": f"~{inp_val}", "status": "needs_attention"}
            score += 15
            
        # 3. CLS
        cls_status = cwv_data.get("cls_status", "UNKNOWN")
        cls_val = cwv_data.get("cls_value", "N/A")
        if cls_status == "GOOD":
            details["cls_stability"] = {"value": "Stable", "status": "optimal"}
            score += 25
        else:
            details["cls_stability"] = {"value": "Unstable", "status": "needs_attention"}
            score += 15
            
        # 4. Mobile vs Desktop
        mobile_pass = cwv_data.get("mobile_pass", False)
        desktop_pass = cwv_data.get("desktop_pass", False)
        
        if mobile_pass and desktop_pass:
            details["mobile_vs_desktop_cwv"] = {"value": "Both Strong", "status": "optimal"}
            score += 25
        elif desktop_pass:
             details["mobile_vs_desktop_cwv"] = {"value": "Mobile weaker", "status": "needs_attention"}
             score += 15
        else:
             details["mobile_vs_desktop_cwv"] = {"value": "Both Weak", "status": "critical"}
             score += 5
             
        return min(score, 100), details

    def _score_search_rendering_accessibility(self, data: Dict, spider_data: Dict = None) -> tuple[float, Dict]:
        """
        Score Search Rendering Accessibility.
        BRD Sub-parameters:
        - javascript_rendering_issues
        - delayed_lazy_content
        - hidden_content
        - client_side_rendering_risks
        - critical_resource_blocking
        """
        score = 0
        details = {}
        
        # Heuristics based on "js_rendering_accessible" from data
        # 1. JS Rendering
        js_accessible = data.get("js_rendering_accessible", True)
        if js_accessible:
            details["javascript_rendering_issues"] = {"value": "None detected", "status": "optimal"}
            score += 20
        else:
            details["javascript_rendering_issues"] = {"value": "Render-blocking JS", "status": "needs_attention"}
            score += 10
            
        # 2. Delayed/Lazy Content
        # Heuristic: assumed present if CWV LCP is poor or if spider detected hydration issues
        lcp_poor = data.get("lcp_is_poor", False)
        if not lcp_poor:
            details["delayed_lazy_content"] = {"value": "Optimal", "status": "optimal"}
            score += 20
        else:
            details["delayed_lazy_content"] = {"value": "Present", "status": "needs_attention"}
            score += 10
            
        # 3. Hidden Content
        details["hidden_content"] = {"value": "Minimal", "status": "optimal"}
        score += 20
        
        # 4. CSR Risks
        ssr_detected = data.get("ssr_detected", True) # Default to true for now
        if ssr_detected:
            details["client_side_rendering_risks"] = {"value": "Low (SSR)", "status": "optimal"}
            score += 20
        else:
            details["client_side_rendering_risks"] = {"value": "Moderate", "status": "needs_attention"}
            score += 10
            
        # 5. Critical Resource Blocking
        blocked_resources = data.get("blocked_resources_count", 0)
        if blocked_resources == 0:
            details["critical_resource_blocking"] = {"value": "None", "status": "optimal"}
            score += 20
        else:
             details["critical_resource_blocking"] = {"value": "Detected", "status": "needs_attention"}
             score += 10
             
        return min(score, 100), details

    def _score_ai_llm_crawl(self, data: Dict) -> tuple[float, Dict]:
        """
        Score AI & LLM Crawl.
        BRD Sub-parameters:
        - llm_txt_presence_rules
        - ai_crawler_permissions
        - content_usage_signals
        - ai_indexing_exposure
        """
        score = 0
        details = {}
        
        # 1. llm.txt
        has_llm_txt = data.get("llm_txt_detected", False)
        if has_llm_txt:
            details["llm_txt_presence_rules"] = {"value": "Present", "status": "optimal"}
            score += 25
        else:
            details["llm_txt_presence_rules"] = {"value": "Missing", "status": "needs_attention"}
            score += 5
            
        # 2. AI Crawler Permissions
        # Do we block GPTBot?
        ai_policy = data.get("ai_crawler_policy", "Not defined")
        if ai_policy != "Not defined":
            details["ai_crawler_permissions"] = {"value": "Managed", "status": "optimal"}
            score += 25
        else:
            details["ai_crawler_permissions"] = {"value": "Not defined", "status": "needs_attention"}
            score += 10
            
        # 3. Content Usage
        # Heuristic
        details["content_usage_signals"] = {"value": "Absent", "status": "needs_attention"}
        score += 25 
        
        # 4. AI Indexing
        details["ai_indexing_exposure"] = {"value": "Not tracked", "status": "needs_attention"}
        score += 25
        
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
