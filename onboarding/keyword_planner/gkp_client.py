"""
GKP Client - Google Keyword Planner API Interface

This module handles all interactions with the Google Ads Keyword Planner API.
It provides methods to:
1. Generate keyword ideas from seed phrases
2. Get historical metrics for existing keywords
3. Handle geo-targeting and language settings

NO simulation or fallback - all data must come from the real API.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Volume thresholds
VOLUME_PRIMARY_THRESHOLD = 1000
VOLUME_FALLBACK_THRESHOLD = 500

# Location mapping (common locations to Google Geo Target IDs)
LOCATION_GEO_TARGETS = {
    "india": "2356",
    "united states": "2840",
    "usa": "2840",
    "uk": "2826",
    "united kingdom": "2826",
    "canada": "2124",
    "australia": "2036",
    "germany": "2276",
    "france": "2250",
    "global": None,
    "international": None,
    "nationwide": None,
}


@dataclass
class KeywordMetrics:
    """Data class for keyword metrics from GKP."""
    keyword: str
    volume: int
    competition: str
    competition_index: int
    low_bid: float
    high_bid: float
    source: str = "generated"  # DB valid: verified, generated, custom


class GKPClient:
    """
    Client for Google Keyword Planner API.
    
    Handles authentication, query building, and response parsing.
    """
    
    def __init__(self):
        """Initialize GKP client with credentials from environment."""
        self._validate_credentials()
        self.client = self._get_client()
        self.customer_id = self._get_customer_id()
    
    def _validate_credentials(self):
        """Validate all required Google Ads API credentials are present."""
        required_vars = [
            "GOOGLE_ADS_DEVELOPER_TOKEN",
            "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_REFRESH_TOKEN",
            "GOOGLE_ADS_CUSTOMER_ID"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(
                f"Missing Google Ads API credentials: {', '.join(missing)}. "
                f"Configure them in .env file."
            )
    
    def _get_client(self):
        """Get configured Google Ads client."""
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            raise ImportError(
                "google-ads library not installed. Run: pip install google-ads"
            )
        
        config = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "use_proto_plus": True
        }
        return GoogleAdsClient.load_from_dict(config)
    
    def _get_customer_id(self) -> str:
        """Get customer ID without dashes."""
        return os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
    
    def _get_geo_target(self, location_scope: Optional[str]) -> Optional[str]:
        """Convert location scope to Google Geo Target ID."""
        if not location_scope:
            return None
        location_lower = location_scope.lower().strip()
        return LOCATION_GEO_TARGETS.get(location_lower)
    
    def generate_keyword_ideas(
        self,
        seeds: List[str],
        location_scope: Optional[str] = None,
        language_code: str = "1000",  # English
        page_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate keyword ideas from seed phrases using GKP.
        
        Args:
            seeds: List of seed phrases to generate ideas from.
            location_scope: Geographic targeting (e.g., "india", "usa").
            language_code: Language constant ID (default: 1000 = English).
            page_url: Optional website URL for additional context.
        
        Returns:
            List of keyword dictionaries with metrics.
        """
        if not seeds:
            logger.warning("No seeds provided for keyword generation")
            return []
        
        try:
            service = self.client.get_service("KeywordPlanIdeaService")
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            
            request.customer_id = self.customer_id
            request.language = f"languageConstants/{language_code}"
            request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            # Add geo target if available
            geo_target = self._get_geo_target(location_scope)
            if geo_target:
                request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
            
            # Add keyword seeds
            for seed in seeds:
                request.keyword_seed.keywords.append(seed)
            
            # Add URL seed if provided
            if page_url:
                request.url_seed.url = page_url
            
            logger.info(f"Querying GKP with {len(seeds)} seeds...")
            response = service.generate_keyword_ideas(request=request)
            
            keywords = []
            for idea in response.results:
                metrics = idea.keyword_idea_metrics
                if not metrics:
                    continue
                
                volume = metrics.avg_monthly_searches or 0
                competition_index = metrics.competition_index or 50
                competition = metrics.competition.name if metrics.competition else "UNKNOWN"
                
                # Only include keywords meeting volume threshold
                if volume >= VOLUME_FALLBACK_THRESHOLD:
                    keywords.append({
                        "keyword": idea.text,
                        "volume": volume,
                        "competition": competition,
                        "competition_index": competition_index,
                        "low_bid": float(metrics.low_top_of_page_bid_micros or 0) / 1_000_000,
                        "high_bid": float(metrics.high_top_of_page_bid_micros or 0) / 1_000_000,
                        "source": "generated",  # DB valid: verified, generated, custom
                        "meets_primary_threshold": volume >= VOLUME_PRIMARY_THRESHOLD
                    })
            
            logger.info(f"GKP returned {len(keywords)} keywords (above {VOLUME_FALLBACK_THRESHOLD} volume)")
            return keywords
            
        except Exception as e:
            logger.error(f"GKP API Error: {e}")
            raise RuntimeError(f"Failed to query Google Keyword Planner: {str(e)}")
    
    def get_keyword_metrics(
        self,
        keywords: List[str],
        location_scope: Optional[str] = None,
        language_code: str = "1000"
    ) -> List[Dict[str, Any]]:
        """
        Get historical metrics for specific keywords.
        
        Used to validate onboarding keywords against real volume data.
        
        Args:
            keywords: List of keywords to get metrics for.
            location_scope: Geographic targeting.
            language_code: Language constant ID.
        
        Returns:
            List of keyword dictionaries with metrics.
        """
        if not keywords:
            return []
        
        try:
            service = self.client.get_service("KeywordPlanIdeaService")
            request = self.client.get_type("GenerateKeywordHistoricalMetricsRequest")
            
            request.customer_id = self.customer_id
            request.keywords = keywords
            request.language = f"languageConstants/{language_code}"
            request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            # Add geo target if available
            geo_target = self._get_geo_target(location_scope)
            if geo_target:
                request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
            
            logger.info(f"Getting metrics for {len(keywords)} keywords...")
            response = service.generate_keyword_historical_metrics(request=request)
            
            results = []
            for result in response.results:
                metrics = result.keyword_metrics
                if not metrics:
                    continue
                
                volume = metrics.avg_monthly_searches or 0
                competition_index = metrics.competition_index or 50
                competition = metrics.competition.name if metrics.competition else "UNKNOWN"
                
                results.append({
                    "keyword": result.text,
                    "volume": volume,
                    "competition": competition,
                    "competition_index": competition_index,
                    "source": "custom",  # DB valid: verified, generated, custom
                    "meets_threshold": volume >= VOLUME_FALLBACK_THRESHOLD
                })
            
            logger.info(f"Got metrics for {len(results)} keywords")
            return results
            
        except Exception as e:
            logger.error(f"GKP Metrics API Error: {e}")
            raise RuntimeError(f"Failed to get keyword metrics: {str(e)}")


# Singleton instance for convenience
_client_instance = None

def get_gkp_client() -> GKPClient:
    """Get or create GKP client singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GKPClient()
    return _client_instance
