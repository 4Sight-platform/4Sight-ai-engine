"""
Seed Generator - Generate Search Query Seeds from User Profile

This module generates raw seed phrases from user profile data.
Seeds are used to query Google Keyword Planner for keyword ideas.

IMPORTANT:
- Seeds are NOT keywords themselves - they are inputs to GKP.
- This module generates raw seeds; validation is done by seed_validator.py.
- NO domain-specific hardcoding - all seeds derived from profile data only.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeedCategory:
    """Represents a category of seeds with its purpose."""
    name: str
    seeds: List[str]
    intent: str  # transactional, informational, comparison


class SeedGenerator:
    """
    Generates search query seeds from user profile.
    
    Seeds are categorized by intent type to ensure diverse keyword coverage.
    """
    
    def __init__(self):
        """Initialize seed generator."""
        pass
    
    def generate(
        self,
        profile: Dict[str, Any],
        feedback: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        """
        Generate categorized seed phrases from user profile.
        
        Args:
            profile: User profile dictionary containing:
                - business_name: Company/brand name
                - business_description: What the business does
                - products: List of products (dicts with 'name' key)
                - services: List of services (dicts with 'name' key)
                - differentiators: List of unique selling points
                - location_scope: Geographic focus
                - selected_locations: Specific locations
                - customer_description: Target customer description
                - search_intent: User-selected intents (action, comparison, deal)
            feedback: Optional feedback from validator for refinement.
        
        Returns:
            Dictionary of seeds by category:
            {
                "transactional": [...],
                "informational": [...],
                "comparison": [...],
                "branded": [...],
                "long_tail": [...]
            }
        """
        # Extract profile components
        business_name = profile.get('business_name', '').strip()
        description = profile.get('business_description', '').strip()
        products = self._extract_names(profile.get('products', []))
        services = self._extract_names(profile.get('services', []))
        differentiators = profile.get('differentiators', [])
        location = self._get_location(profile)
        customer = profile.get('customer_description', '').strip()
        intents = profile.get('search_intent', [])
        
        # Combine products and services as "offerings"
        offerings = products + services
        
        if not offerings:
            logger.warning("No products or services found in profile")
            # Fall back to extracting from description
            offerings = self._extract_offerings_from_description(description)
        
        # Generate seeds by category
        seeds = {
            "transactional": self._generate_transactional_seeds(
                offerings, location, feedback
            ),
            "informational": self._generate_informational_seeds(
                offerings, differentiators, customer, feedback
            ),
            "comparison": self._generate_comparison_seeds(
                offerings, feedback
            ),
            "branded": self._generate_branded_seeds(
                business_name, offerings, feedback
            ),
            "long_tail": self._generate_long_tail_seeds(
                offerings, location, customer, differentiators, feedback
            )
        }
        
        # Filter based on user's stated intents
        if intents:
            seeds = self._prioritize_by_intent(seeds, intents)
        
        # Remove empty categories
        seeds = {k: v for k, v in seeds.items() if v}
        
        total_seeds = sum(len(v) for v in seeds.values())
        logger.info(f"Generated {total_seeds} seeds across {len(seeds)} categories")
        
        return seeds
    
    def _extract_names(self, items: List[Any]) -> List[str]:
        """Extract names from product/service list."""
        names = []
        for item in items:
            if isinstance(item, dict):
                name = item.get('name') or item.get('product_name') or item.get('service_name', '')
            elif isinstance(item, str):
                name = item
            else:
                continue
            
            if name and name.strip():
                names.append(name.strip())
        
        return names
    
    def _get_location(self, profile: Dict[str, Any]) -> str:
        """Get primary location from profile."""
        locations = profile.get('selected_locations', [])
        if locations:
            return locations[0] if isinstance(locations[0], str) else str(locations[0])
        
        scope = profile.get('location_scope', '')
        if scope and scope.lower() not in ['global', 'international', 'nationwide']:
            return scope
        
        return ""
    
    def _extract_offerings_from_description(self, description: str) -> List[str]:
        """Extract potential offerings from business description as fallback."""
        # Simple extraction: look for noun phrases
        # This is a basic fallback - ideally profile should have products/services
        words = description.split()
        
        # Extract 2-3 word phrases as potential offerings
        offerings = []
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5 and len(phrase) < 30:
                offerings.append(phrase.lower())
        
        return offerings[:3]  # Maximum 3 fallback offerings
    
    def _generate_transactional_seeds(
        self,
        offerings: List[str],
        location: str,
        feedback: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate transactional intent seeds.
        
        Transactional = User ready to take action (buy, hire, book, etc.)
        """
        seeds = []
        
        for offering in offerings[:5]:  # Limit to top 5 offerings
            # Base transactional patterns
            seeds.append(f"{offering} services")
            seeds.append(f"{offering} agency")
            seeds.append(f"{offering} company")
            seeds.append(f"{offering} pricing")
            seeds.append(f"{offering} cost")
            
            # Location-based if available
            if location:
                seeds.append(f"{offering} in {location}")
                seeds.append(f"{offering} {location}")
                seeds.append(f"{offering} near me")
        
        # Apply feedback refinement if provided
        if feedback and feedback.get('transactional'):
            seeds = self._refine_seeds(seeds, feedback['transactional'])
        
        return list(set(seeds))  # Remove duplicates
    
    def _generate_informational_seeds(
        self,
        offerings: List[str],
        differentiators: List[str],
        customer: str,
        feedback: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate informational intent seeds.
        
        Informational = User researching, learning, comparing options.
        """
        seeds = []
        
        for offering in offerings[:5]:
            # Question-based patterns
            seeds.append(f"what is {offering}")
            seeds.append(f"how does {offering} work")
            seeds.append(f"{offering} benefits")
            seeds.append(f"{offering} guide")
            seeds.append(f"{offering} tips")
            seeds.append(f"why {offering}")
        
        # Differentiator-based seeds
        for diff in differentiators[:3]:
            if isinstance(diff, str) and len(diff) > 3:
                seeds.append(f"{diff} for business")
        
        if feedback and feedback.get('informational'):
            seeds = self._refine_seeds(seeds, feedback['informational'])
        
        return list(set(seeds))
    
    def _generate_comparison_seeds(
        self,
        offerings: List[str],
        feedback: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate comparison intent seeds.
        
        Comparison = User evaluating options, looking for best choice.
        """
        seeds = []
        
        for offering in offerings[:5]:
            seeds.append(f"best {offering}")
            seeds.append(f"top {offering}")
            seeds.append(f"{offering} reviews")
            seeds.append(f"{offering} comparison")
            seeds.append(f"{offering} vs")  # GKP will expand this
        
        if feedback and feedback.get('comparison'):
            seeds = self._refine_seeds(seeds, feedback['comparison'])
        
        return list(set(seeds))
    
    def _generate_branded_seeds(
        self,
        business_name: str,
        offerings: List[str],
        feedback: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate branded seeds (for brand awareness keywords).
        """
        seeds = []
        
        if business_name and len(business_name) > 2:
            seeds.append(f"{business_name} reviews")
            seeds.append(f"{business_name} services")
            
            for offering in offerings[:3]:
                seeds.append(f"{business_name} {offering}")
        
        if feedback and feedback.get('branded'):
            seeds = self._refine_seeds(seeds, feedback['branded'])
        
        return list(set(seeds))
    
    def _generate_long_tail_seeds(
        self,
        offerings: List[str],
        location: str,
        customer: str,
        differentiators: List[str],
        feedback: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate long-tail seeds (specific, lower competition).
        
        Long-tail = 4+ word specific queries.
        """
        seeds = []
        
        # Extract customer type if available
        customer_type = self._extract_customer_type(customer)
        
        for offering in offerings[:4]:
            # Combine offering with location and audience
            if location:
                seeds.append(f"{offering} for {customer_type} in {location}")
                seeds.append(f"affordable {offering} in {location}")
            
            if customer_type:
                seeds.append(f"{offering} for {customer_type}")
                seeds.append(f"best {offering} for {customer_type}")
            
            # Use differentiators
            for diff in differentiators[:2]:
                if isinstance(diff, str) and len(diff) > 3:
                    seeds.append(f"{diff} {offering}")
        
        if feedback and feedback.get('long_tail'):
            seeds = self._refine_seeds(seeds, feedback['long_tail'])
        
        return list(set(seeds))
    
    def _extract_customer_type(self, customer_description: str) -> str:
        """Extract a short customer type label from description."""
        if not customer_description:
            return "businesses"
        
        # Simple extraction: look for common customer type words
        customer_lower = customer_description.lower()
        
        if 'startup' in customer_lower:
            return 'startups'
        elif 'small business' in customer_lower or 'smb' in customer_lower:
            return 'small businesses'
        elif 'enterprise' in customer_lower:
            return 'enterprises'
        elif 'b2b' in customer_lower:
            return 'B2B companies'
        elif 'e-commerce' in customer_lower or 'ecommerce' in customer_lower:
            return 'ecommerce businesses'
        else:
            # Return first few words as fallback
            words = customer_description.split()[:3]
            return ' '.join(words) if words else 'businesses'
    
    def _prioritize_by_intent(
        self,
        seeds: Dict[str, List[str]],
        user_intents: List[str]
    ) -> Dict[str, List[str]]:
        """
        Prioritize seed categories based on user's stated intents.
        
        Maps onboarding intents to seed categories:
        - action/action-focused -> transactional
        - comparison -> comparison
        - deal -> transactional (price-focused)
        - information -> informational
        """
        intent_mapping = {
            'action': 'transactional',
            'action-focused': 'transactional',
            'comparison': 'comparison',
            'deal': 'transactional',  # Deal seekers also transactional
            'information': 'informational',
            'informational': 'informational'
        }
        
        # Map user intents to categories
        priority_categories = set()
        for intent in user_intents:
            mapped = intent_mapping.get(intent.lower())
            if mapped:
                priority_categories.add(mapped)
        
        # Always include long_tail and branded
        priority_categories.add('long_tail')
        priority_categories.add('branded')
        
        # If no specific priorities, return all
        if not priority_categories:
            return seeds
        
        # Return only priority categories (but keep all if user selected all)
        if len(priority_categories) >= 3:
            return seeds
        
        return {k: v for k, v in seeds.items() if k in priority_categories}
    
    def _refine_seeds(self, seeds: List[str], feedback: str) -> List[str]:
        """
        Refine seeds based on validator feedback.
        
        Simple implementation - just filters based on feedback keywords.
        Complex refinement happens in the feedback loop with validator.
        """
        # For now, just return original seeds
        # The validator will send specific rejected seeds for regeneration
        return seeds


def generate_seeds(profile: Dict[str, Any], feedback: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
    """
    Convenience function to generate seeds from profile.
    
    Args:
        profile: User profile dictionary.
        feedback: Optional validator feedback.
    
    Returns:
        Dictionary of categorized seeds.
    """
    generator = SeedGenerator()
    return generator.generate(profile, feedback)
