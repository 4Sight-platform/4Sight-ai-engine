"""
Seed Validator - LLM-Powered Seed Validation

This module validates seed phrases using Gemini 2.5 Flash.
It ensures seeds are natural search queries that humans would actually type.

If a seed is invalid:
1. It can be rewritten by the LLM
2. OR sent back to seed_generator with feedback for regeneration

Maximum 2 retries per seed category.
"""

import os
import logging
import json
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 500

# Rate limiting for free tier (5 requests/minute = 1 per 12 seconds)
RATE_LIMIT_DELAY_SECONDS = 15

# Set to True to skip LLM validation
SKIP_LLM_VALIDATION = True  # Disabled - free tier too slow and responses unreliable


class SeedValidator:
    """
    Validates seed phrases using Gemini LLM.
    
    Ensures seeds are natural, grammatically correct search queries.
    """
    
    def __init__(self):
        """Initialize validator with Gemini client."""
        self.model = self._init_gemini()
        self.max_retries = 2
    
    def _init_gemini(self):
        """Initialize Gemini model."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set - validation will be skipped")
            return None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(LLM_MODEL)
        except ImportError:
            logger.error("google-generativeai not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    def validate(
        self,
        seeds: Dict[str, List[str]],
        profile: Dict[str, Any],
        seed_generator_callback=None
    ) -> Dict[str, List[str]]:
        """
        Validate all seed phrases.
        
        Args:
            seeds: Dictionary of seeds by category.
            profile: User profile for context.
            seed_generator_callback: Optional callback to regenerate seeds.
        
        Returns:
            Dictionary of validated seeds by category.
        """
        # Skip LLM validation if configured (for free tier rate limits)
        if SKIP_LLM_VALIDATION:
            logger.info("LLM seed validation skipped (SKIP_LLM_VALIDATION=True)")
            return seeds
        
        if not self.model:
            logger.warning("LLM not available - returning seeds unvalidated")
            return seeds
        
        # Build profile summary for context
        profile_summary = self._build_profile_summary(profile)
        
        validated_seeds = {}
        
        for category, seed_list in seeds.items():
            logger.info(f"Validating {len(seed_list)} seeds in category: {category}")
            
            valid, invalid, feedback = self._validate_category(
                seed_list, profile_summary, category
            )
            
            # If too many invalid and we have a callback, try to regenerate
            if len(invalid) > len(valid) and seed_generator_callback:
                logger.info(f"Category {category} has too many invalid seeds, requesting regeneration")
                
                # Request regeneration with feedback
                regenerated = seed_generator_callback(
                    profile,
                    feedback={category: feedback}
                )
                
                if category in regenerated:
                    # Validate regenerated seeds (but don't recurse infinitely)
                    new_valid, _, _ = self._validate_category(
                        regenerated[category], profile_summary, category
                    )
                    valid.extend(new_valid)
            
            if valid:
                validated_seeds[category] = valid
            
            logger.info(f"Category {category}: {len(valid)} valid, {len(invalid)} invalid")
        
        return validated_seeds
    
    def _validate_category(
        self,
        seeds: List[str],
        profile_summary: str,
        category: str
    ) -> Tuple[List[str], List[str], str]:
        """
        Validate a category of seeds with rate limiting.
        
        Returns:
            Tuple of (valid_seeds, invalid_seeds, feedback_string)
        """
        import time
        
        if not seeds:
            return [], [], ""
        
        # Batch validate for efficiency
        prompt = self._build_validation_prompt(seeds, profile_summary, category)
        
        # Retry with exponential backoff for rate limits
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': LLM_TEMPERATURE,
                        'max_output_tokens': LLM_MAX_TOKENS,
                    }
                )
                
                result = self._parse_validation_response(response.text, seeds)
                
                # Rate limit: wait before next call
                logger.info(f"Rate limiting: waiting {RATE_LIMIT_DELAY_SECONDS}s before next LLM call")
                time.sleep(RATE_LIMIT_DELAY_SECONDS)
                
                return result
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    wait_time = RATE_LIMIT_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_attempts}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Validation failed for category {category}: {e}")
                    return seeds, [], ""
        
        logger.error("Rate limit retries exhausted - accepting all seeds")
        return seeds, [], ""
    
    def _build_profile_summary(self, profile: Dict[str, Any]) -> str:
        """Build a concise profile summary for LLM context."""
        parts = []
        
        if profile.get('business_name'):
            parts.append(f"Business: {profile['business_name']}")
        
        if profile.get('business_description'):
            desc = profile['business_description'][:200]
            parts.append(f"Description: {desc}")
        
        products = profile.get('products', [])
        if products:
            names = [p.get('name', p) if isinstance(p, dict) else p for p in products[:3]]
            parts.append(f"Products: {', '.join(str(n) for n in names)}")
        
        services = profile.get('services', [])
        if services:
            names = [s.get('name', s) if isinstance(s, dict) else s for s in services[:3]]
            parts.append(f"Services: {', '.join(str(n) for n in names)}")
        
        return " | ".join(parts) if parts else "Business profile"
    
    def _build_validation_prompt(
        self,
        seeds: List[str],
        profile_summary: str,
        category: str
    ) -> str:
        """Build the validation prompt for batch processing."""
        seeds_formatted = "\n".join([f"{i+1}. {s}" for i, s in enumerate(seeds)])
        
        prompt = f"""You are validating search query seeds for a keyword research tool.

BUSINESS CONTEXT:
{profile_summary}

SEED CATEGORY: {category}

SEEDS TO VALIDATE:
{seeds_formatted}

For each seed, determine if it's a NATURAL search query that a real person would type into Google.

RULES:
1. A seed is VALID if it reads like something a human would actually search for.
2. A seed is INVALID if it:
   - Is grammatically awkward (e.g., "buy digital marketing" instead of "digital marketing pricing")
   - Contains brand names in unnatural positions (e.g., "buy CompanyName")
   - Is too generic to be useful (e.g., just "marketing")
   - Makes no logical sense

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "valid": [1, 3, 5],
  "invalid": [2, 4],
  "feedback": "Brief explanation of why some seeds were invalid"
}}

Where the numbers are the seed numbers from the list above.
Return ONLY the JSON, no other text."""

        return prompt
    
    def _parse_validation_response(
        self,
        response_text: str,
        original_seeds: List[str]
    ) -> Tuple[List[str], List[str], str]:
        """Parse LLM response and categorize seeds."""
        import re
        
        try:
            # Clean response text
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # Fix common JSON issues from LLM
            # Replace single quotes with double quotes
            text = re.sub(r"'(\w+)':", r'"\1":', text)  # Fix keys
            text = text.replace("'", '"')  # Replace remaining singles
            # Remove trailing commas before ] or }
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            
            result = json.loads(text)
            
            valid_indices = result.get('valid', [])
            invalid_indices = result.get('invalid', [])
            feedback = result.get('feedback', '')
            
            # Convert indices to actual seeds (1-indexed in prompt)
            valid_seeds = []
            invalid_seeds = []
            
            for i, seed in enumerate(original_seeds, 1):
                if i in valid_indices:
                    valid_seeds.append(seed)
                elif i in invalid_indices:
                    invalid_seeds.append(seed)
                else:
                    # If not explicitly categorized, assume valid
                    valid_seeds.append(seed)
            
            return valid_seeds, invalid_seeds, feedback
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse validation response: {e}")
            logger.debug(f"Raw response: {response_text[:200]}")
            # Fail open - return all as valid
            return original_seeds, [], ""
        except Exception as e:
            logger.error(f"Error parsing validation: {e}")
            return original_seeds, [], ""
    
    def validate_single(self, seed: str, profile_summary: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single seed and optionally rewrite it.
        
        Args:
            seed: The seed to validate.
            profile_summary: Business context.
        
        Returns:
            Tuple of (is_valid, rewritten_seed_or_none)
        """
        if not self.model:
            return True, None
        
        prompt = f"""You are validating a search query seed.

BUSINESS: {profile_summary}
SEED: "{seed}"

Is this a natural Google search query that a potential customer would type?

If YES, respond: VALID
If NO, respond: INVALID | <rewritten version>

Examples:
- "buy digital marketing" -> INVALID | digital marketing pricing
- "SEO services near me" -> VALID
- "buy CompanyName" -> INVALID | CompanyName reviews

Respond with ONLY "VALID" or "INVALID | <rewrite>"."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 100,
                }
            )
            
            text = response.text.strip()
            
            if text.upper().startswith('VALID'):
                return True, None
            elif text.upper().startswith('INVALID'):
                parts = text.split('|', 1)
                if len(parts) > 1:
                    return False, parts[1].strip()
                return False, None
            else:
                # Unclear response, assume valid
                return True, None
                
        except Exception as e:
            logger.error(f"Single validation failed: {e}")
            return True, None


def validate_seeds(
    seeds: Dict[str, List[str]],
    profile: Dict[str, Any],
    seed_generator_callback=None
) -> Dict[str, List[str]]:
    """
    Convenience function to validate seeds.
    
    Args:
        seeds: Dictionary of seeds by category.
        profile: User profile.
        seed_generator_callback: Optional callback for regeneration.
    
    Returns:
        Validated seeds dictionary.
    """
    validator = SeedValidator()
    return validator.validate(seeds, profile, seed_generator_callback)
