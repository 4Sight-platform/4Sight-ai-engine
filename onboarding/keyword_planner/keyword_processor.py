"""
Keyword Processor - Merge, Deduplicate, Proportion, Score, and Rank

This is the final processing stage that combines keywords from all sources:
1. Onboarding keywords (LLM-generated, validated via GKP)
2. GKP keywords (from various seed categories)
3. GSC low-hanging fruit (rank 11-50)

Applies proportionality:
- 40% from GSC (low-hanging fruit)
- 60% from intent-based categories

Then scores and ranks for final output.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

# Proportionality constants
GSC_PROPORTION = 0.40  # 40% from GSC
INTENT_PROPORTION = 0.60  # 60% from intent-based sources
DEFAULT_TARGET_COUNT = 20


@dataclass
class ProcessedKeyword:
    """Processed keyword with all metadata."""
    keyword: str
    volume: int
    competition: str
    competition_index: int
    difficulty: str
    intent: str
    source: str
    score: float
    gsc_position: Optional[float] = None
    gsc_impressions: Optional[int] = None


class KeywordProcessor:
    """
    Processes, merges, and ranks keywords from all sources.
    """
    
    def __init__(self):
        """Initialize processor."""
        pass
    
    def process(
        self,
        onboarding_keywords: List[Dict[str, Any]],
        gkp_keywords: List[Dict[str, Any]],
        gsc_keywords: List[Dict[str, Any]],
        user_intents: List[str],
        target_count: int = DEFAULT_TARGET_COUNT
    ) -> List[Dict[str, Any]]:
        """
        Process all keyword sources into final ranked list.
        
        Args:
            onboarding_keywords: Keywords from onboarding (validated).
            gkp_keywords: Keywords from GKP (validated).
            gsc_keywords: Low-hanging fruit from GSC.
            user_intents: User's stated search intents.
            target_count: Target number of keywords to return.
        
        Returns:
            List of processed, scored, and ranked keywords.
        """
        logger.info(
            f"Processing keywords: {len(onboarding_keywords)} onboarding, "
            f"{len(gkp_keywords)} GKP, {len(gsc_keywords)} GSC"
        )
        
        # Step 1: Deduplicate across all sources
        all_keywords = self._deduplicate(
            onboarding_keywords, gkp_keywords, gsc_keywords
        )
        logger.info(f"After deduplication: {len(all_keywords)} unique keywords")
        
        # Step 2: Calculate proportional slots
        gsc_slots = int(target_count * GSC_PROPORTION)  # 40%
        intent_slots = target_count - gsc_slots  # 60%
        
        logger.info(f"Slots: {gsc_slots} GSC, {intent_slots} intent-based")
        
        # Step 3: Select GSC keywords (40%)
        gsc_selected = self._select_gsc_keywords(
            [k for k in all_keywords if k.get('source') == 'verified'],
            gsc_slots
        )
        
        # Step 4: Select intent-based keywords (60%)
        non_gsc = [k for k in all_keywords if k.get('source') != 'verified']
        
        # Remove already selected GSC keywords from consideration
        selected_texts = {k['keyword'].lower() for k in gsc_selected}
        remaining = [k for k in non_gsc if k['keyword'].lower() not in selected_texts]
        
        intent_selected = self._select_intent_keywords(
            remaining, user_intents, intent_slots
        )
        
        # Step 5: Combine and score
        combined = gsc_selected + intent_selected
        
        # Step 6: Enrich with difficulty and final scoring
        scored = [self._score_keyword(k) for k in combined]
        
        # Step 7: Sort by score descending
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        # Step 8: Limit to target count
        final = scored[:target_count]
        
        logger.info(f"Final keyword count: {len(final)}")
        
        return final
    
    def _deduplicate(
        self,
        onboarding: List[Dict[str, Any]],
        gkp: List[Dict[str, Any]],
        gsc: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate keywords across all sources.
        
        Priority: GSC > GKP > Onboarding (GSC keywords preserved with most data)
        """
        seen: Set[str] = set()
        result = []
        
        # First add GSC keywords (highest priority for low-hanging fruit)
        for kw in gsc:
            text = kw.get('keyword', '').lower().strip()
            if text and text not in seen:
                seen.add(text)
                kw['source'] = 'verified'  # DB valid: verified, generated, custom
                result.append(kw)
        
        # Then GKP keywords
        for kw in gkp:
            text = kw.get('keyword', '').lower().strip()
            if text and text not in seen:
                seen.add(text)
                if 'source' not in kw:
                    kw['source'] = 'generated'  # DB valid: verified, generated, custom
                result.append(kw)
        
        # Finally onboarding keywords
        for kw in onboarding:
            text = kw.get('keyword', '').lower().strip()
            if text and text not in seen:
                seen.add(text)
                kw['source'] = 'custom'  # DB valid: verified, generated, custom
                result.append(kw)
        
        return result
    
    def _select_gsc_keywords(
        self,
        gsc_keywords: List[Dict[str, Any]],
        slots: int
    ) -> List[Dict[str, Any]]:
        """
        Select top GSC keywords based on opportunity score.
        
        GSC keywords are already sorted by opportunity_score from gsc_client.
        """
        if not gsc_keywords:
            logger.warning("No GSC keywords available")
            return []
        
        # Already sorted by opportunity_score, just take top N
        selected = gsc_keywords[:slots]
        
        logger.info(f"Selected {len(selected)}/{slots} GSC keywords")
        
        return selected
    
    def _select_intent_keywords(
        self,
        keywords: List[Dict[str, Any]],
        user_intents: List[str],
        slots: int
    ) -> List[Dict[str, Any]]:
        """
        Select keywords based on user's stated intents.
        
        Distributes slots proportionally across intents.
        """
        if not keywords:
            return []
        
        if not user_intents:
            # No intents specified - just return by volume
            sorted_by_volume = sorted(keywords, key=lambda x: x.get('volume', 0), reverse=True)
            return sorted_by_volume[:slots]
        
        # Map intents to keyword types
        intent_mapping = {
            'action': ['transactional'],
            'action-focused': ['transactional'],
            'comparison': ['comparison', 'commercial'],
            'deal': ['transactional', 'commercial'],
            'information': ['informational'],
            'informational': ['informational']
        }
        
        # Determine which types to prioritize
        priority_types = set()
        for intent in user_intents:
            types = intent_mapping.get(intent.lower(), [])
            priority_types.update(types)
        
        # If no valid mappings, default to all
        if not priority_types:
            priority_types = {'transactional', 'informational', 'comparison'}
        
        # Categorize keywords by their inferred intent
        categorized = defaultdict(list)
        for kw in keywords:
            intent_type = self._infer_intent(kw.get('keyword', ''))
            categorized[intent_type].append(kw)
        
        # Calculate slots per category
        num_categories = len(priority_types)
        slots_per_category = slots // num_categories if num_categories > 0 else slots
        
        selected = []
        remaining_slots = slots
        
        # First pass: select from priority categories
        for category in priority_types:
            if remaining_slots <= 0:
                break
            
            category_keywords = categorized.get(category, [])
            # Sort by volume within category
            sorted_kws = sorted(category_keywords, key=lambda x: x.get('volume', 0), reverse=True)
            
            take = min(slots_per_category, remaining_slots, len(sorted_kws))
            selected.extend(sorted_kws[:take])
            remaining_slots -= take
        
        # Second pass: fill remaining slots from any category
        if remaining_slots > 0:
            selected_texts = {k['keyword'].lower() for k in selected}
            remaining_kws = [
                k for k in keywords 
                if k['keyword'].lower() not in selected_texts
            ]
            remaining_kws.sort(key=lambda x: x.get('volume', 0), reverse=True)
            selected.extend(remaining_kws[:remaining_slots])
        
        logger.info(f"Selected {len(selected)}/{slots} intent-based keywords")
        
        return selected
    
    def _infer_intent(self, keyword: str) -> str:
        """
        Infer the intent type of a keyword.
        
        Returns: 'Transactional' or 'Informational' (DB-valid values)
        """
        kw_lower = keyword.lower()
        
        # Transactional indicators (action-oriented, buying intent)
        transactional_words = [
            'buy', 'purchase', 'order', 'book', 'hire', 'get',
            'pricing', 'price', 'cost', 'quote', 'near me',
            'agency', 'company', 'services', 'service',
            # Comparison words also indicate commercial/transactional intent
            'best', 'top', 'vs', 'versus', 'compare', 'comparison',
            'review', 'reviews', 'alternative', 'alternatives'
        ]
        if any(word in kw_lower for word in transactional_words):
            return 'Transactional'
        
        # Everything else is Informational
        return 'Informational'
    
    def _score_keyword(self, keyword: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate final score for a keyword.
        
        Scoring formula:
        - Volume score: 35% weight
        - Competition inverse: 25% weight
        - GSC bonus: 40% weight (if from GSC)
        
        Also adds difficulty classification.
        """
        volume = keyword.get('volume', 0)
        competition_index = keyword.get('competition_index', 50)
        source = keyword.get('source', 'generated')  # DB: verified, generated, custom
        gsc_position = keyword.get('position', 0)
        
        # Volume score (0-50, normalized to 10K max)
        volume_score = min(50, (volume / 10000) * 50)
        
        # Competition inverse (0-50)
        competition_score = ((100 - competition_index) / 100) * 50
        
        # GSC bonus (40 points if from GSC/verified and good position)
        if source == 'verified' and gsc_position:
            # Closer to position 10 = higher bonus
            position_factor = max(0, (50 - gsc_position)) / 40
            gsc_bonus = 40 * position_factor
        else:
            gsc_bonus = 0
        
        # Final score calculation
        final_score = (
            (volume_score * 0.35) +
            (competition_score * 0.25) +
            (gsc_bonus * 0.40)
        )
        
        # Difficulty classification
        if competition_index <= 33:
            difficulty = "Low"
        elif competition_index <= 66:
            difficulty = "Medium"
        else:
            difficulty = "High"
        
        # Infer intent
        intent = self._infer_intent(keyword.get('keyword', ''))
        
        # Determine keyword type (DB valid: Transactional, Informational, Branded, Long-tail)
        word_count = len(keyword.get('keyword', '').split())
        if word_count >= 4:
            keyword_type = "Long-tail"
        else:
            # Use intent as keyword type for shorter keywords
            keyword_type = intent  # Already 'Transactional' or 'Informational'
        
        # Build final keyword object
        return {
            'keyword': keyword.get('keyword', ''),
            'volume': volume,
            'competition': keyword.get('competition', 'UNKNOWN'),
            'competition_index': competition_index,
            'difficulty': difficulty,
            'intent': intent,
            'keyword_type': keyword_type,
            'source': source,
            'score': round(final_score, 2),
            # Preserve GSC-specific data
            'gsc_position': keyword.get('position'),
            'gsc_impressions': keyword.get('impressions'),
            'gsc_clicks': keyword.get('clicks'),
            'is_selected': False  # Default to not selected
        }


def process_keywords(
    onboarding_keywords: List[Dict[str, Any]],
    gkp_keywords: List[Dict[str, Any]],
    gsc_keywords: List[Dict[str, Any]],
    user_intents: List[str],
    target_count: int = DEFAULT_TARGET_COUNT
) -> List[Dict[str, Any]]:
    """
    Convenience function to process keywords.
    
    Args:
        onboarding_keywords: Validated onboarding keywords.
        gkp_keywords: Validated GKP keywords.
        gsc_keywords: GSC low-hanging fruit.
        user_intents: User's search intents.
        target_count: Target output count.
    
    Returns:
        Processed and ranked keyword list.
    """
    processor = KeywordProcessor()
    return processor.process(
        onboarding_keywords,
        gkp_keywords,
        gsc_keywords,
        user_intents,
        target_count
    )
