"""
Keyword Generation Prompt Templates
LLM prompts for generating SEO keywords from business profiles
"""

from typing import Dict, Any, List


def build_keyword_generation_prompt(profile: Dict[str, Any]) -> str:
    """
    Build prompt for keyword generation
    
    Args:
        profile: User profile with business info
    
    Returns:
        Formatted prompt string
    """
    
    business_name = profile.get('business_name', 'Unknown Business')
    business_description = profile.get('business_description', '')
    website_url = profile.get('website_url', '')
    
    # Get location info
    location_scope = profile.get('location_scope', 'nationwide')
    selected_locations = profile.get('selected_locations', [])
    location_text = ', '.join(selected_locations) if selected_locations else 'nationwide'
    
    # Get customer description
    customer_description = profile.get('customer_description', 'general customers')
    
    # Get search intent
    search_intent = profile.get('search_intent', [])
    intent_text = ', '.join(search_intent) if search_intent else 'informational and action-focused'
    
    # Get products/services
    raw_products = profile.get('products', [])
    products = []
    for p in raw_products:
        if isinstance(p, dict):
            products.append(p.get('name', '') or p.get('product_name', ''))
        elif isinstance(p, str):
            products.append(p)
            
    raw_services = profile.get('services', [])
    services = []
    for s in raw_services:
        if isinstance(s, dict):
            services.append(s.get('name', '') or s.get('service_name', ''))
        elif isinstance(s, str):
            services.append(s)

    differentiators = profile.get('differentiators', [])
    
    products_text = '\n  - ' + '\n  - '.join([p for p in products if p]) if products else 'Not specified'
    services_text = '\n  - ' + '\n  - '.join([s for s in services if s]) if services else 'Not specified'
    differentiators_text = '\n  - ' + '\n  - '.join(differentiators) if differentiators else 'Not specified'
    
    # Get SEO goals
    seo_goals = profile.get('seo_goals', [])
    goals_text = ', '.join(seo_goals) if seo_goals else 'organic traffic growth'
    
    prompt = f"""You are an expert SEO keyword researcher. Generate 30 highly relevant, strategic keywords for the following business.

BUSINESS INFORMATION:
---------------------
Business Name: {business_name}
Website: {website_url}
Description: {business_description}

TARGET AUDIENCE:
---------------
Location: {location_text}
Customer Profile: {customer_description}
Search Intent: {intent_text}

OFFERINGS:
----------
Products: {products_text}

Services: {services_text}

Differentiators: {differentiators_text}

SEO GOALS:
----------
{goals_text}

KEYWORD GENERATION REQUIREMENTS:
-------------------------------
Generate exactly 30 keywords that:

1. RELEVANCE: Directly relate to the business offerings and target audience
2. VARIETY: Mix of different keyword types:
   - 40% Commercial intent (e.g., "buy vegan cakes Seattle", "wedding cake prices")
   - 30% Informational (e.g., "how to order custom cakes", "best bakery near me")
   - 20% Navigational (e.g., "artisan bakery downtown", brand + location)
   - 10% Long-tail specific (e.g., "gluten free birthday cake delivery")

3. SEARCH VOLUME POTENTIAL: Balance between:
   - High volume head terms (20%)
   - Medium volume terms (50%)
   - Low volume long-tail (30%)

4. LOCATION-BASED: If location is specified, include:
   - Location modifiers (e.g., "Seattle bakery", "near me")
   - Local service keywords

5. INTENT ALIGNMENT: Match the search intent preferences: {intent_text}

6. COMPETITIVE BALANCE: Mix of:
   - Easier to rank for (long-tail, specific)
   - More competitive (broader, higher volume)

OUTPUT FORMAT:
-------------
Return ONLY a JSON array of exactly 30 keyword strings. No explanations, no markdown, just the JSON array.

Example format:
["keyword 1", "keyword 2", "keyword 3", ...]

Generate the keywords now:"""
    
    return prompt


def build_keyword_refinement_prompt(keywords: List[str], profile: Dict[str, Any]) -> str:
    """
    Build prompt for refining existing keywords
    
    Args:
        keywords: Existing keyword list
        profile: User profile
    
    Returns:
        Formatted prompt string
    """
    
    business_name = profile.get('business_name', 'Unknown Business')
    business_description = profile.get('business_description', '')
    
    keywords_text = '\n  - ' + '\n  - '.join(keywords)
    
    prompt = f"""You are an expert SEO strategist. Refine and improve the following keyword list for this business.

BUSINESS:
---------
{business_name}
{business_description}

CURRENT KEYWORDS ({len(keywords)}):
{keywords_text}

REFINEMENT TASKS:
----------------
1. REMOVE keywords that are:
   - Too broad or generic
   - Not relevant to the business
   - Duplicate or too similar
   - Extremely low search volume potential

2. ADD keywords that are missing:
   - Important product/service keywords
   - Local intent keywords (if applicable)
   - Question-based keywords
   - Comparison keywords

3. IMPROVE keywords by:
   - Adding location modifiers where relevant
   - Making them more specific
   - Including action words (buy, get, find, hire, etc.)

OUTPUT FORMAT:
-------------
Return a JSON object with:
{{
  "refined_keywords": ["keyword 1", "keyword 2", ...],
  "removed": ["removed keyword 1", ...],
  "added": ["new keyword 1", ...],
  "notes": "Brief explanation of changes"
}}

Provide the refined keyword list now:"""
    
    return prompt


def build_keyword_expansion_prompt(seed_keywords: List[str], profile: Dict[str, Any], count: int = 20) -> str:
    """
    Build prompt for expanding seed keywords
    
    Args:
        seed_keywords: Initial keywords to expand from
        profile: User profile
        count: Number of additional keywords to generate
    
    Returns:
        Formatted prompt string
    """
    
    business_name = profile.get('business_name', 'Unknown Business')
    seeds_text = ', '.join(seed_keywords)
    
    prompt = f"""You are an SEO keyword expansion expert. Generate {count} additional related keywords based on these seed keywords.

BUSINESS: {business_name}

SEED KEYWORDS:
{seeds_text}

EXPANSION REQUIREMENTS:
----------------------
Generate {count} new keywords that are:
1. Related to but different from the seed keywords
2. Include synonyms and variations
3. Include question-based keywords
4. Include comparison keywords (vs, versus, alternative, best)
5. Include problem-solution keywords

OUTPUT FORMAT:
-------------
Return ONLY a JSON array of exactly {count} new keyword strings.

["new keyword 1", "new keyword 2", ...]

Generate the expanded keywords now:"""
    
    return prompt


def build_keyword_intent_analysis_prompt(keywords: List[str]) -> str:
    """
    Build prompt for analyzing keyword search intent
    
    Args:
        keywords: Keywords to analyze
    
    Returns:
        Formatted prompt string
    """
    
    keywords_text = '\n  - ' + '\n  - '.join(keywords)
    
    prompt = f"""You are an SEO search intent expert. Analyze the search intent for each of these keywords.

KEYWORDS:
{keywords_text}

INTENT CATEGORIES:
-----------------
- INFORMATIONAL: User wants to learn or find information
- NAVIGATIONAL: User wants to find a specific website or page
- COMMERCIAL: User is researching before purchase
- TRANSACTIONAL: User is ready to buy or take action

OUTPUT FORMAT:
-------------
Return a JSON object mapping each keyword to its intent:
{{
  "keyword 1": "INFORMATIONAL",
  "keyword 2": "TRANSACTIONAL",
  ...
}}

Analyze the intent now:"""
    
    return prompt


def build_keyword_difficulty_prompt(keywords: List[str], profile: Dict[str, Any]) -> str:
    """
    Build prompt for estimating keyword difficulty
    
    Args:
        keywords: Keywords to analyze
        profile: User profile
    
    Returns:
        Formatted prompt string
    """
    
    business_description = profile.get('business_description', '')
    website_url = profile.get('website_url', '')
    
    keywords_text = '\n  - ' + '\n  - '.join(keywords)
    
    prompt = f"""You are an SEO difficulty assessment expert. Estimate the ranking difficulty for each keyword given this business context.

BUSINESS CONTEXT:
----------------
Website: {website_url}
Description: {business_description}

KEYWORDS:
{keywords_text}

DIFFICULTY LEVELS:
-----------------
- EASY: Long-tail, specific, low competition
- MEDIUM: Some competition, achievable with good content
- HARD: High competition, requires strong authority
- VERY_HARD: Dominated by major brands, extremely difficult

OUTPUT FORMAT:
-------------
Return a JSON object mapping each keyword to difficulty:
{{
  "keyword 1": "EASY",
  "keyword 2": "MEDIUM",
  ...
}}

Assess the difficulty now:"""
    
    return prompt


# System prompt for keyword generation
KEYWORD_GENERATION_SYSTEM_PROMPT = """You are an expert SEO keyword researcher with deep knowledge of:
- Search intent and user behavior
- Keyword competition and difficulty
- Long-tail vs. head term strategy
- Local SEO optimization
- Commercial vs. informational keywords
- Semantic keyword relationships

Your goal is to generate highly relevant, strategic keywords that will help businesses rank in search engines and attract qualified traffic.

Always consider:
1. Business relevance
2. Search volume potential
3. Ranking difficulty
4. User intent
5. Conversion potential

Provide keyword suggestions that are specific, actionable, and aligned with the business goals."""


# Temperature settings for different tasks
TEMPERATURE_SETTINGS = {
    "generation": 0.8,      # Higher creativity for generating new keywords
    "refinement": 0.5,      # Balanced for refining existing keywords
    "analysis": 0.3,        # Lower for consistent intent/difficulty analysis
    "expansion": 0.7        # Creative but focused for expanding keywords
}