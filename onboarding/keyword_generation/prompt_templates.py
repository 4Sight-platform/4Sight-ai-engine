"""
Keyword Generation Prompt Templates
LLM prompts for generating SEO keywords from business profiles
"""

from typing import Dict, Any, List


def build_keyword_generation_prompt(profile: Dict[str, Any]) -> str:
    """
    Build prompt for keyword generation with hard coverage rules
    
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
    products = profile.get('products', [])
    services = profile.get('services', [])
    differentiators = profile.get('differentiators', [])
    
    products_text = '\n  - ' + '\n  - '.join(products) if products else 'Not specified'
    services_text = '\n  - ' + '\n  - '.join(services) if services else 'Not specified'
    differentiators_text = '\n  - ' + '\n  - '.join(differentiators) if differentiators else 'Not specified'
    
    # Get SEO goals
    seo_goals = profile.get('seo_goals', [])
    goals_text = ', '.join(seo_goals) if seo_goals else 'organic traffic growth'
    
    # Count items for coverage validation
    num_products = len(products)
    num_services = len(services)
    num_differentiators = len(differentiators)
    total_items = num_products + num_services + num_differentiators
    
    # DYNAMIC LOCATION PRIORITY based on location_scope
    if location_scope.lower() == 'local':
        location_priority = "HIGH"
        location_percentage = "60-70%"
        location_count = "18-21"
        location_guidance = "This is a LOCAL business - location is CRITICAL for local SEO. Include location in most keywords."
    elif location_scope.lower() == 'regional':
        location_priority = "MEDIUM"
        location_percentage = "40-50%"
        location_count = "12-15"
        location_guidance = "This is a REGIONAL business - balance location with broader keywords."
    elif location_scope.lower() == 'nationwide':
        location_priority = "LOW"
        location_percentage = "20-30%"
        location_count = "6-9"
        location_guidance = "This is a NATIONWIDE business - focus on products/services, use location sparingly."
    else:  # international
        location_priority = "VERY LOW"
        location_percentage = "10-20%"
        location_count = "3-6"
        location_guidance = "This is an INTERNATIONAL business - location is minimal priority, focus on global keywords."
    
    # Build location examples
    if selected_locations:
        first_location = location_text.split(',')[0]
        location_example_1 = f'   - "gluten free cakes in {first_location}"'
        location_example_2 = f'   - "best bakery in {first_location}"'
    else:
        location_example_1 = '   - "gluten free cakes near me"'
        location_example_2 = '   - "best bakery near me"'
    
    prompt = f"""Generate 30 strategic SEO keywords for this business. Read ALL requirements before generating.

BUSINESS CONTEXT:
-----------------
Name: {business_name}
Website: {website_url}
Description: {business_description}
Customer Profile: {customer_description}

STRATEGIC GUIDANCE FROM PROFILE:
--------------------------------
→ Business Focus: Extract key themes from "{business_description}"
→ Customer Needs: Consider "{customer_description}" when choosing keyword phrasing and intent
→ SEO Goals: {goals_text} - align keyword strategy accordingly

PRIMARY FOCUS - PRODUCTS ({num_products} items - ALL MUST BE COVERED):
{products_text}

PRIMARY FOCUS - SERVICES ({num_services} items - ALL MUST BE COVERED):
{services_text}

PRIMARY FOCUS - DIFFERENTIATORS ({num_differentiators} items - ALL MUST BE COVERED):
{differentiators_text}

⚠️ CRITICAL: Minimum 8 keywords (25%) MUST explicitly highlight differentiators!

LOCATION CONTEXT:
-----------------
Scope: {location_scope.upper()}
Location: {location_text}
Priority: {location_priority}
{location_guidance}

ADDITIONAL CONTEXT:
-------------------
Search Intent Preferences: {intent_text}
SEO Goals: {goals_text}

MANDATORY REQUIREMENTS (FAILURE = INVALID OUTPUT):
==================================================

1. COVERAGE RULES - YOU MUST:
   ✓ Create at least 1 keyword for EACH product listed above
   ✓ Create at least 1 keyword for EACH service listed above
   ✓ Create at least 1 keyword for EACH differentiator listed above
   ✓ Minimum 8 keywords (25%) MUST explicitly highlight differentiators
   ✗ DO NOT skip any item - all {total_items} items must appear

2. DIFFERENTIATOR EMPHASIS - MANDATORY:
   You MUST create keywords that highlight these differentiators:
{differentiators_text}
   
   Example differentiator keywords (CREATE SIMILAR):
   - "same day [product] delivery"
   - "100% organic [product/service]"
   - "eco friendly [business type]"
   - "custom [product] designs"

3. CUSTOMER-FOCUSED KEYWORDS:
   Based on "{customer_description}", include keywords that:
   - Match how these customers would search
   - Address their specific needs and values
   - Use language and terms they would use

4. LOCATION USAGE - DYNAMIC BASED ON SCOPE:
   Business Scope: {location_scope.upper()}
   Location Priority: {location_priority}
   Target: {location_percentage} of keywords ({location_count} out of 30)
   
   ✓ Include location in {location_count} keywords
   ✓ {"Focus on local SEO - location is critical" if location_scope.lower() == 'local' else "Balance location with broader appeal"}
   
   Examples for {location_scope.upper()} business:
{location_example_1}
{location_example_2}
   - "custom wedding cakes"
   - "organic bakery catering"

3. KEYWORD VARIETY - YOU MUST INCLUDE:
   ✓ Short-tail (1-2 words): minimum 9 keywords
      Example: "vegan cakes", "organic bread", "cake catering"
   ✓ Medium-tail (3 words): minimum 12 keywords
      Example: "custom wedding cake design", "gluten free bakery"
   ✓ Long-tail (4+ words): minimum 9 keywords
      Example: "same day gluten free cake delivery", "eco friendly bakery packaging"

4. INTENT DISTRIBUTION - YOU MUST INCLUDE:
   ✓ Commercial (40%): "buy", "order", "get", "hire", "prices"
   ✓ Informational (30%): "how to", "best", "guide", "tips"
   ✓ Navigational (20%): brand name, specific service names
   ✓ Transactional long-tail (10%): specific action + product/service

5. ANTI-REPETITION - YOU MUST NOT:
   ✗ Repeat keywords with reordered words
   ✗ Use mechanical patterns
   ✗ Ignore differentiators in favor of location

GENERATION STRATEGY:
====================

Step 1: List all {num_products} products, {num_services} services, {num_differentiators} differentiators
Step 2: Create 1 keyword for EACH item (ensures coverage)
Step 3: Create 8+ keywords highlighting differentiators (MANDATORY)
Step 4: Add customer-focused keywords based on "{customer_description}"
Step 5: Add location to {location_count} keywords based on {location_scope.upper()} scope
Step 6: Verify all {total_items} items covered AND minimum 8 differentiator keywords included

OUTPUT FORMAT:
==============
Return ONLY a JSON array of exactly 30 keyword strings.
NO explanations, NO markdown, NO code blocks - just the array.

["keyword 1", "keyword 2", ..., "keyword 30"]

Generate the 30 keywords now:"""
    
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
KEYWORD_GENERATION_SYSTEM_PROMPT = """You are an expert SEO keyword researcher with deep knowledge of search intent, keyword competition, and strategic keyword planning.

CRITICAL RULES - FAILURE TO FOLLOW THESE MAKES OUTPUT INVALID:

1. PRIORITY ORDER (EQUAL IMPORTANCE):
   - Products (CRITICAL - must cover ALL)
   - Services (CRITICAL - must cover ALL)
   - Differentiators (CRITICAL - must cover ALL - minimum 25% of keywords MUST highlight differentiators)
   - Customer needs and search behavior
   - Business unique value proposition
   - SEO goals alignment
   - Location (varies by business scope)

2. MANDATORY COVERAGE - YOU MUST:
   - Include EVERY product in at least one keyword
   - Include EVERY service in at least one keyword
   - Include EVERY differentiator in at least one keyword
   - Minimum 25% of keywords (8 out of 30) MUST explicitly highlight differentiators
   - If you skip ANY item, your output is INVALID
   
   DIFFERENTIATOR EXAMPLES (MANDATORY TO FOLLOW):
   - If differentiator is "same-day delivery" → keywords like "same day cake delivery", "same day gluten free cakes"
   - If differentiator is "100% organic" → keywords like "100% organic bakery", "organic ingredient cakes"
   - If differentiator is "eco-friendly packaging" → keywords like "eco friendly bakery", "sustainable packaging bakery"
   - If differentiator is "custom designs" → keywords like "custom cake designs", "personalized wedding cakes"

3. STRATEGIC USE OF PROFILE DATA:
   
   A. CUSTOMER DESCRIPTION → Keyword Intent & Phrasing:
      - If customers are "health-conscious" → use "healthy", "nutritious", "wellness"
      - If customers are "millennials" → use "Instagram-worthy", "trendy", "modern"
      - If customers are "budget-conscious" → use "affordable", "best value", "deals"
      - If customers are "professionals" → use "corporate", "business", "executive"
   
   B. BUSINESS DESCRIPTION → Keyword Themes:
      - Extract key themes from description
      - Use description to identify primary focus areas
      - Incorporate unique aspects mentioned in description
   
   C. SEO GOALS → Keyword Strategy:
      - If goal is "local_visibility" → increase location-based keywords (60-70%)
      - If goal is "organic_traffic_growth" → focus on high-volume, broad terms
      - If goal is "lead_generation" → focus on commercial/transactional intent (50%+)
      - If goal is "brand_awareness" → include brand name + category keywords

4. LOCATION USAGE - DYNAMIC BASED ON SCOPE & SEO GOALS:
   - LOCAL businesses + "local_visibility" goal: 60-70% location keywords
   - LOCAL businesses + other goals: 50-60% location keywords
   - REGIONAL businesses: 40-50% location keywords
   - NATIONWIDE businesses: 20-30% location keywords
   - INTERNATIONAL businesses: 10-20% location keywords
   
   GRAMMAR RULES FOR LOCATION:
   - ALWAYS use proper prepositions: "in [city]", "near [city]", "near me"
   - Example CORRECT: "gluten free cakes in Seattle"
   - Example WRONG: "gluten free cakes Seattle"
   - Example CORRECT: "best bakery in Seattle"
   - Example WRONG: "best bakery Seattle"

5. KEYWORD VARIETY - YOU MUST INCLUDE:
   - Short-tail keywords (1-2 words): minimum 30%
   - Long-tail keywords (4+ words): minimum 30%
   - Commercial intent: 40% (or 50%+ if SEO goal is "lead_generation")
   - Informational intent: 30%
   - Navigational intent: 20%
   - Transactional long-tail: 10%

6. ANTI-REPETITION - YOU MUST NOT:
   - Repeat the same keyword with reordered words
   - Add location to every keyword mechanically
   - Use the same pattern repeatedly
   - Omit prepositions when using location
   - Ignore differentiators (minimum 25% MUST highlight them)

Your goal is to generate strategically diverse keywords that:
1. Comprehensively cover ALL products, services, and differentiators (with special emphasis on differentiators)
2. Align with customer search behavior and needs
3. Reflect the business's unique value proposition
4. Support the specified SEO goals
5. Maintain proper grammar and search intent variety"""


# Temperature settings for different tasks
TEMPERATURE_SETTINGS = {
    "generation": 0.6,      # Reduced from 0.8 for better instruction adherence
    "refinement": 0.5,      # Balanced for refining existing keywords
    "analysis": 0.3,        # Lower for consistent intent/difficulty analysis
    "expansion": 0.7        # Creative but focused for expanding keywords
}