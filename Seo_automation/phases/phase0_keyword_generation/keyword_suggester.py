"""
Keyword Suggester
Generates keyword suggestions using Google Gemini 2.5 Flash API
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phases.phase0_keyword_generation.prompt_templates import (
    build_keyword_generation_prompt,
    build_keyword_refinement_prompt,
    build_keyword_expansion_prompt,
    build_keyword_intent_analysis_prompt,
    KEYWORD_GENERATION_SYSTEM_PROMPT,
    TEMPERATURE_SETTINGS
)


class KeywordSuggester:
    """
    Generate keyword suggestions using Google Gemini API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize keyword suggester
        
        Args:
            api_key: Google Gemini API key (optional, reads from config if not provided)
        """
        self.api_key = api_key or self._load_api_key()
        self.client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-2.5-flash')
            except ImportError:
                print("Warning: google-generativeai package not installed. Run: pip install google-generativeai")
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from config"""
        try:
            config_path = Path("config/credentials.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get("gemini", {}).get("api_key")
        except Exception as e:
            print(f"Warning: Could not load API key: {e}")
        
        return None
    
    def generate_keywords(self, profile: Dict[str, Any], count: int = 30) -> List[str]:
        """
        Generate keyword suggestions from business profile
        
        Args:
            profile: User profile with business information
            count: Number of keywords to generate (default: 30)
        
        Returns:
            List of keyword strings
        """
        if not self.client:
            print("Warning: API client not initialized, returning mock keywords")
            return self._generate_mock_keywords(profile, count)
        
        try:
            print(f"→ Generating {count} keywords using Gemini API...")
            
            # Build prompt
            prompt = build_keyword_generation_prompt(profile)
            full_prompt = f"{KEYWORD_GENERATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Call Gemini API
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    'temperature': TEMPERATURE_SETTINGS["generation"],
                    'max_output_tokens': 2000,
                }
            )
            
            # Extract keywords from response
            keywords = self._parse_keyword_response(response.text)
            
            print(f"✓ Generated {len(keywords)} keywords")
            
            return keywords[:count]  # Ensure we return exactly the requested count
        
        except Exception as e:
            print(f"Error generating keywords: {e}")
            return self._generate_mock_keywords(profile, count)
    
    def refine_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine existing keywords
        
        Args:
            keywords: Current keyword list
            profile: User profile
        
        Returns:
            Dictionary with refined_keywords, removed, added, notes
        """
        if not self.client:
            print("Warning: API client not initialized, returning original keywords")
            return {
                "refined_keywords": keywords,
                "removed": [],
                "added": [],
                "notes": "API not available"
            }
        
        try:
            print(f"→ Refining {len(keywords)} keywords...")
            
            # Build prompt
            prompt = build_keyword_refinement_prompt(keywords, profile)
            full_prompt = f"{KEYWORD_GENERATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Call Gemini API
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    'temperature': TEMPERATURE_SETTINGS["refinement"],
                    'max_output_tokens': 2000,
                }
            )
            
            # Parse response
            result = self._parse_json_response(response.text)
            
            print(f"✓ Refinement complete")
            print(f"  - Removed: {len(result.get('removed', []))}")
            print(f"  - Added: {len(result.get('added', []))}")
            
            return result
        
        except Exception as e:
            print(f"Error refining keywords: {e}")
            return {
                "refined_keywords": keywords,
                "removed": [],
                "added": [],
                "notes": f"Error: {str(e)}"
            }
    
    def expand_keywords(self, seed_keywords: List[str], profile: Dict[str, Any], count: int = 20) -> List[str]:
        """
        Expand seed keywords into more variations
        
        Args:
            seed_keywords: Initial keywords
            profile: User profile
            count: Number of additional keywords to generate
        
        Returns:
            List of new keyword strings
        """
        if not self.client:
            return self._generate_mock_keywords(profile, count)
        
        try:
            print(f"→ Expanding {len(seed_keywords)} seed keywords...")
            
            # Build prompt
            prompt = build_keyword_expansion_prompt(seed_keywords, profile, count)
            full_prompt = f"{KEYWORD_GENERATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Call Gemini API
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    'temperature': TEMPERATURE_SETTINGS["expansion"],
                    'max_output_tokens': 1500,
                }
            )
            
            # Extract keywords
            keywords = self._parse_keyword_response(response.text)
            
            print(f"✓ Expanded to {len(keywords)} new keywords")
            
            return keywords[:count]
        
        except Exception as e:
            print(f"Error expanding keywords: {e}")
            return []
    
    def analyze_intent(self, keywords: List[str]) -> Dict[str, str]:
        """
        Analyze search intent for keywords
        
        Args:
            keywords: Keywords to analyze
        
        Returns:
            Dictionary mapping keyword to intent category
        """
        if not self.client:
            # Return default intents
            return {kw: "INFORMATIONAL" for kw in keywords}
        
        try:
            print(f"→ Analyzing intent for {len(keywords)} keywords...")
            
            # Build prompt
            prompt = build_keyword_intent_analysis_prompt(keywords)
            full_prompt = f"{KEYWORD_GENERATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Call Gemini API
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    'temperature': TEMPERATURE_SETTINGS["analysis"],
                    'max_output_tokens': 1500,
                }
            )
            
            # Parse response
            intent_map = self._parse_json_response(response.text)
            
            print(f"✓ Intent analysis complete")
            
            return intent_map
        
        except Exception as e:
            print(f"Error analyzing intent: {e}")
            return {kw: "INFORMATIONAL" for kw in keywords}
    
    def _parse_keyword_response(self, response_text: str) -> List[str]:
        """
        Parse keyword list from Gemini response
        
        Args:
            response_text: Raw response text
        
        Returns:
            List of keywords
        """
        try:
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*|\s*```', '', response_text)
            text = text.strip()
            
            # Parse JSON array
            keywords = json.loads(text)
            
            # Validate it's a list of strings
            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                return keywords
            else:
                raise ValueError("Response is not a list of strings")
        
        except Exception as e:
            print(f"Warning: Could not parse keyword response: {e}")
            print(f"Response text: {response_text[:200]}")
            
            # Fallback: try to extract any quoted strings
            matches = re.findall(r'"([^"]+)"', response_text)
            if matches:
                return matches
            
            return []
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON object from Gemini response
        
        Args:
            response_text: Raw response text
        
        Returns:
            Parsed dictionary
        """
        try:
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*|\s*```', '', response_text)
            text = text.strip()
            
            # Parse JSON
            result = json.loads(text)
            
            return result
        
        except Exception as e:
            print(f"Warning: Could not parse JSON response: {e}")
            return {}
    
    def _generate_mock_keywords(self, profile: Dict[str, Any], count: int) -> List[str]:
        """
        Generate mock keywords when API is not available
        
        Args:
            profile: User profile
            count: Number of keywords
        
        Returns:
            List of mock keywords
        """
        business_name = profile.get('business_name', 'business')
        business_description = profile.get('business_description', '')
        
        # Extract key terms from description
        words = re.findall(r'\b\w+\b', business_description.lower())
        key_terms = [w for w in words if len(w) > 4][:5]
        
        base_keywords = key_terms if key_terms else ['service', 'product', 'solution']
        
        mock_keywords = []
        
        # Generate variations
        for base in base_keywords:
            mock_keywords.extend([
                f"{base}",
                f"{base} online",
                f"best {base}",
                f"{base} near me",
                f"buy {base}",
                f"{base} service"
            ])
        
        # Fill remaining with generic keywords
        while len(mock_keywords) < count:
            mock_keywords.append(f"keyword {len(mock_keywords) + 1}")
        
        return mock_keywords[:count]


def generate_keywords_for_user(profile: Dict[str, Any], count: int = 30) -> List[str]:
    """
    Main function to generate keywords for a user profile
    
    Args:
        profile: User profile dictionary
        count: Number of keywords to generate
    
    Returns:
        List of keyword strings
    """
    suggester = KeywordSuggester()
    return suggester.generate_keywords(profile, count)


def refine_user_keywords(keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to refine user's keywords
    
    Args:
        keywords: Current keywords
        profile: User profile
    
    Returns:
        Refinement results dictionary
    """
    suggester = KeywordSuggester()
    return suggester.refine_keywords(keywords, profile)


# For testing
if __name__ == "__main__":
    # Test keyword generation
    test_profile = {
        "business_name": "Artisan Bakery Co.",
        "website_url": "https://artisanbakery.com",
        "business_description": "Local artisan bakery specializing in gluten-free cakes for health-conscious customers in downtown Seattle.",
        "location_scope": "local",
        "selected_locations": ["Seattle, WA"],
        "customer_description": "Health-conscious millennials who value organic ingredients",
        "search_intent": ["information", "action-focused"],
        "products": ["Gluten-free cakes", "Vegan pastries", "Custom wedding cakes"],
        "services": ["Cake delivery", "Custom cake design", "Catering"],
        "differentiators": ["100% organic ingredients", "Same-day delivery", "Custom designs"],
        "seo_goals": ["organic_traffic_growth", "local_visibility"]
    }
    
    print("Testing Keyword Generation")
    print("="*60)
    
    suggester = KeywordSuggester()
    
    # Test generation
    keywords = suggester.generate_keywords(test_profile, count=30)
    
    print(f"\nGenerated {len(keywords)} keywords:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")
    
    # Test refinement
    if len(keywords) > 10:
        print(f"\n{'='*60}")
        print("Testing Keyword Refinement")
        print("="*60)
        
        refinement = suggester.refine_keywords(keywords[:15], test_profile)
        
        print(f"\nRefined keywords: {len(refinement.get('refined_keywords', []))}")
        print(f"Removed: {refinement.get('removed', [])}")
        print(f"Added: {refinement.get('added', [])}")
        print(f"Notes: {refinement.get('notes', '')}")