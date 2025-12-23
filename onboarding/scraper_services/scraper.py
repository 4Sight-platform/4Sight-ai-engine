"""
Web Scraper for Business Descriptions using Tavily API (Direct HTTP)
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

def scrape_business_description(url: str, timeout: int = 20) -> str:
    """
    Uses Tavily REST API directly to get a summary/description of the business URL.
    
    Args:
        url: The website URL to analyze
        timeout: Request timeout in seconds
        
    Returns:
        String containing the business description, or None if failed/empty.
        
    Raises:
        Exception on API failure
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment")
        raise ValueError("Server configuration error: Missing TAVILY_API_KEY")
    
    # Clean URL if needed
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        # Tavily Search API Endpoint
        endpoint = "https://api.tavily.com/search"
        
        # Explicit prompt for 500 characters
        query = (
            f"Write a verbose and comprehensive business profile for {url}. "
            "Do NOT be concise. You MUST include specific details about their services, "
            "products, target audience, and unique value proposition. "
            "Write at least 4-5 full sentences."
        )
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5
        }
        
        logger.info(f"Scraping business description for: {url}")
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        
        result_text = None
        
        # Strategy 1: Direct 'answer' from Tavily
        if data.get("answer"):
            result_text = data["answer"]
        
        # Strategy 2: Concatenate results if answer is empty
        elif data.get("results"):
            content = " ".join([r.get("content", "") for r in data["results"][:2]])
            result_text = content
            
        return truncate_text(result_text)
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid Tavily API Key")
        logger.error(f"Tavily API error: {str(e)}")
        raise Exception(f"External API error: {str(e)}")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise Exception(f"Scraping failed: {str(e)}")

def truncate_text(text: str, limit: int = 500) -> str:
    """Ensures text doesn't exceed the limit"""
    if not text:
        return None
        
    text = text.strip()
    if len(text) > limit:
        # Try to cut at the last sentence ending to make it look cleaner
        truncated = text[:limit]
        last_dot = truncated.rfind('.')
        if last_dot > limit * 0.8: # If dot is near the end, cut there
            return truncated[:last_dot+1]
        return truncated + "..."
    return text
