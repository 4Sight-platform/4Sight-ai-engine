
import os
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Classifies content intent using Gemini LLM.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not found. Intent classification will be disabled.")

    def classify_intent_alignment(self, keyword: str, title: str, h1: str, content_snippet: str) -> Dict[str, Any]:
        """
        Determines if the content intent aligns with the keyword intent.
        
        Returns:
            Dict with 'status' (optimal/needs_attention), 'score' (0-100), 'reason'.
        """
        if not self.model:
            return {
                "status": "needs_attention",
                "score": 50,
                "reason": "AI model not configured"
            }
            
        prompt = f"""
        Analyze the search intent alignment for the following page:
        
        Target Keyword: "{keyword}"
        Page Title: "{title}"
        H1 Tag: "{h1}"
        Content Snippet: "{content_snippet[:300]}..."
        
        Task:
        1. Determine the intent of the Keyword (Informational, Commercial, Transactional, Navigational).
        2. Determine the intent of the Page Content.
        3. Check if they align.
        
        Response Format (JSON only):
        {{
            "keyword_intent": "...",
            "content_intent": "...",
            "aligned": true/false,
            "score": <0-100 score of alignment>,
            "reason": "Brief explanation"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            import json
            data = json.loads(response.text)
            
            return {
                "status": "optimal" if data.get("aligned", False) else "needs_attention",
                "score": data.get("score", 50),
                "reason": data.get("reason", "Analysis failed"),
                "details": data
            }
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "status": "needs_attention",
                "score": 50,
                "reason": "AI analysis error"
            }
