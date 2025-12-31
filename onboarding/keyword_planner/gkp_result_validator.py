"""
GKP Result Validator - Validate Keywords Returned by Google Keyword Planner

This module validates that keywords returned by GKP are:
1. Relevant to the business
2. Natural search queries
3. Not garbage/spam keywords

If validation rate < 70%, triggers re-query with refined seed.
Maximum 2 retries per seed.
"""

import os
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 2000  # Increased for larger responses
VALIDATION_THRESHOLD = 0.70  # 70% must pass
MAX_RETRIES = 2
BATCH_SIZE = 20  # Smaller batches = more reliable LLM responses

# Rate limiting for free tier (5 requests/minute = 1 per 12 seconds)
# Adding buffer: 15 seconds between calls
RATE_LIMIT_DELAY_SECONDS = 15

# Set to True to skip LLM validation
SKIP_LLM_VALIDATION = True  # Disabled - free tier too slow and responses unreliable


@dataclass
class ValidationResult:
    """Result of keyword validation."""
    valid_keywords: List[Dict[str, Any]]
    invalid_keywords: List[Dict[str, Any]]
    pass_rate: float
    needs_retry: bool
    feedback: str


class GKPResultValidator:
    """
    Validates keywords returned by GKP using Gemini.
    
    Ensures keywords are relevant and natural before including in universe.
    """
    
    def __init__(self):
        """Initialize validator with Gemini client."""
        self.model = self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini model."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set - validation will be lenient")
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
        keywords: List[Dict[str, Any]],
        profile: Dict[str, Any],
        original_seed: str,
        retry_count: int = 0
    ) -> ValidationResult:
        """
        Validate GKP keywords for relevance.
        
        Args:
            keywords: List of keyword dictionaries from GKP.
            profile: User profile for context.
            original_seed: The seed that generated these keywords.
            retry_count: Current retry attempt (for tracking).
        
        Returns:
            ValidationResult with valid/invalid lists and retry flag.
        """
        if not keywords:
            return ValidationResult(
                valid_keywords=[],
                invalid_keywords=[],
                pass_rate=1.0,
                needs_retry=False,
                feedback=""
            )
        
        # Skip LLM validation if configured (for free tier rate limits)
        if SKIP_LLM_VALIDATION:
            logger.info("LLM validation skipped (SKIP_LLM_VALIDATION=True) - accepting all keywords")
            return ValidationResult(
                valid_keywords=keywords,
                invalid_keywords=[],
                pass_rate=1.0,
                needs_retry=False,
                feedback=""
            )
        
        if not self.model:
            # No LLM - return all as valid (lenient mode)
            logger.warning("LLM not available - accepting all keywords")
            return ValidationResult(
                valid_keywords=keywords,
                invalid_keywords=[],
                pass_rate=1.0,
                needs_retry=False,
                feedback=""
            )
        
        # Build profile summary
        profile_summary = self._build_profile_summary(profile)
        
        # Validate in batches
        all_valid = []
        all_invalid = []
        all_feedback = []
        
        for i in range(0, len(keywords), BATCH_SIZE):
            batch = keywords[i:i + BATCH_SIZE]
            valid, invalid, feedback = self._validate_batch(
                batch, profile_summary, original_seed
            )
            all_valid.extend(valid)
            all_invalid.extend(invalid)
            if feedback:
                all_feedback.append(feedback)
        
        # Calculate pass rate
        total = len(all_valid) + len(all_invalid)
        pass_rate = len(all_valid) / total if total > 0 else 1.0
        
        # Determine if retry needed
        needs_retry = pass_rate < VALIDATION_THRESHOLD and retry_count < MAX_RETRIES
        
        combined_feedback = " | ".join(all_feedback) if all_feedback else ""
        
        logger.info(
            f"Validation complete: {len(all_valid)} valid, {len(all_invalid)} invalid, "
            f"pass rate: {pass_rate:.1%}, needs_retry: {needs_retry}"
        )
        
        return ValidationResult(
            valid_keywords=all_valid,
            invalid_keywords=all_invalid,
            pass_rate=pass_rate,
            needs_retry=needs_retry,
            feedback=combined_feedback
        )
    
    def _validate_batch(
        self,
        keywords: List[Dict[str, Any]],
        profile_summary: str,
        original_seed: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        """
        Validate a batch of keywords with rate limiting.
        
        Returns:
            Tuple of (valid_keywords, invalid_keywords, feedback)
        """
        import time
        
        # Extract just the keyword texts for validation
        keyword_texts = [kw.get('keyword', '') for kw in keywords]
        
        prompt = self._build_validation_prompt(keyword_texts, profile_summary, original_seed)
        
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
                
                # Log raw response for debugging
                logger.debug(f"Raw LLM response: {response.text[:500]}")
                
                valid_indices, invalid_indices, feedback = self._parse_response(
                    response.text, len(keywords)
                )
                
                # Map back to full keyword objects
                valid_keywords = [keywords[i-1] for i in valid_indices if 0 < i <= len(keywords)]
                invalid_keywords = [keywords[i-1] for i in invalid_indices if 0 < i <= len(keywords)]
                
                # Rate limit: wait before next call
                logger.info(f"Rate limiting: waiting {RATE_LIMIT_DELAY_SECONDS}s before next LLM call")
                time.sleep(RATE_LIMIT_DELAY_SECONDS)
                
                return valid_keywords, invalid_keywords, feedback
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    # Rate limit hit - exponential backoff
                    wait_time = RATE_LIMIT_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_attempts}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Batch validation failed: {e}")
                    # Fail open - return all as valid
                    return keywords, [], ""
        
        # All retries exhausted
        logger.error("Rate limit retries exhausted - accepting all keywords")
        return keywords, [], ""
    
    def _build_profile_summary(self, profile: Dict[str, Any]) -> str:
        """Build concise profile summary."""
        parts = []
        
        if profile.get('business_name'):
            parts.append(f"Business: {profile['business_name']}")
        
        products = profile.get('products', [])
        services = profile.get('services', [])
        offerings = []
        
        for p in products[:2]:
            name = p.get('name', p) if isinstance(p, dict) else p
            offerings.append(str(name))
        for s in services[:2]:
            name = s.get('name', s) if isinstance(s, dict) else s
            offerings.append(str(name))
        
        if offerings:
            parts.append(f"Offerings: {', '.join(offerings)}")
        
        if profile.get('customer_description'):
            parts.append(f"Target: {profile['customer_description'][:100]}")
        
        return " | ".join(parts) if parts else "Business"
    
    def _build_validation_prompt(
        self,
        keywords: List[str],
        profile_summary: str,
        original_seed: str
    ) -> str:
        """Build the validation prompt."""
        keywords_formatted = "\n".join([f"{i+1}. {kw}" for i, kw in enumerate(keywords)])
        
        prompt = f"""You are a keyword research expert validating keywords for relevance.

BUSINESS CONTEXT:
{profile_summary}

ORIGINAL SEED USED: "{original_seed}"

KEYWORDS TO VALIDATE:
{keywords_formatted}

For each keyword, determine if it is RELEVANT to this business.

A keyword is RELEVANT if:
- It relates to what the business offers
- A potential customer of this business might search for it
- It makes sense as a search query

A keyword is IRRELEVANT if:
- It's about a completely different industry/topic
- It mentions competitor brands inappropriately
- It's spam or nonsensical
- It's too generic to be useful (e.g., just "business" or "company")

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "valid": [1, 2, 5, 7],
  "invalid": [3, 4, 6],
  "feedback": "Brief explanation of why some were invalid - what was wrong with the seed?"
}}

Where numbers are keyword numbers from the list.
Return ONLY the JSON, no other text."""

        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        total_keywords: int
    ) -> Tuple[List[int], List[int], str]:
        """Parse LLM response."""
        import re
        
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # Fix common JSON issues from LLM
            text = re.sub(r"'(\w+)':", r'"\1":', text)  # Fix keys
            text = text.replace("'", '"')  # Replace remaining singles
            text = re.sub(r',\s*}', '}', text)  # Remove trailing commas
            text = re.sub(r',\s*]', ']', text)
            
            result = json.loads(text)
            
            valid_indices = result.get('valid', [])
            invalid_indices = result.get('invalid', [])
            feedback = result.get('feedback', '')
            
            # Ensure all indices are accounted for
            all_indices = set(valid_indices) | set(invalid_indices)
            for i in range(1, total_keywords + 1):
                if i not in all_indices:
                    # If not explicitly categorized, assume valid
                    valid_indices.append(i)
            
            return valid_indices, invalid_indices, feedback
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse response: {e}")
            logger.debug(f"Raw response: {response_text[:200]}")
            # Return all as valid
            return list(range(1, total_keywords + 1)), [], ""
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return list(range(1, total_keywords + 1)), [], ""
    
    def generate_refined_seed(
        self,
        original_seed: str,
        feedback: str,
        profile: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a refined seed based on validation feedback.
        
        Used when retry is needed.
        
        Args:
            original_seed: The seed that produced bad results.
            feedback: Feedback explaining what was wrong.
            profile: User profile.
        
        Returns:
            Refined seed string, or None if generation fails.
        """
        if not self.model:
            return None
        
        profile_summary = self._build_profile_summary(profile)
        
        prompt = f"""You are refining a search seed for keyword research.

BUSINESS: {profile_summary}

ORIGINAL SEED: "{original_seed}"

PROBLEM: {feedback}

Generate a BETTER seed that:
1. Is more specific to this business
2. Avoids the problems mentioned above
3. Will produce more relevant keyword ideas

Return ONLY the new seed phrase (no quotes, no explanation).
Example good seeds:
- "affordable SEO services for small business"
- "enterprise project management software pricing"
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 100,
                }
            )
            
            refined = response.text.strip().strip('"').strip("'")
            logger.info(f"Refined seed: '{original_seed}' -> '{refined}'")
            return refined
            
        except Exception as e:
            logger.error(f"Failed to generate refined seed: {e}")
            return None


def validate_gkp_results(
    keywords: List[Dict[str, Any]],
    profile: Dict[str, Any],
    original_seed: str,
    retry_count: int = 0
) -> ValidationResult:
    """
    Convenience function to validate GKP results.
    
    Args:
        keywords: Keywords from GKP.
        profile: User profile.
        original_seed: Seed used to generate keywords.
        retry_count: Current retry attempt.
    
    Returns:
        ValidationResult.
    """
    validator = GKPResultValidator()
    return validator.validate(keywords, profile, original_seed, retry_count)
