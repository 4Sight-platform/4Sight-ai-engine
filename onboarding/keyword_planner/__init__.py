"""
Keyword Planner Module

Modular keyword planning pipeline with LLM-powered validation.

Modules:
- seed_generator: Generate search query seeds from profile
- seed_validator: LLM validation of seeds
- gkp_client: Google Keyword Planner API client
- gkp_result_validator: LLM validation of GKP results
- gsc_client: Google Search Console client for low-hanging fruit
- keyword_processor: Merge, proportion, score, and rank keywords
- planner_service: Main orchestrator

Usage:
    from onboarding.keyword_planner import KeywordPlannerService
    
    service = KeywordPlannerService()
    result = await service.initialize_universe(user_id)
"""

# Main Service
from onboarding.keyword_planner.planner_service import KeywordPlannerService

# Individual modules for direct use
from onboarding.keyword_planner.seed_generator import generate_seeds, SeedGenerator
from onboarding.keyword_planner.seed_validator import validate_seeds, SeedValidator
from onboarding.keyword_planner.gkp_client import get_gkp_client, GKPClient
from onboarding.keyword_planner.gkp_result_validator import validate_gkp_results, GKPResultValidator
from onboarding.keyword_planner.gsc_client import get_low_hanging_fruit, GSCKeywordClient
from onboarding.keyword_planner.keyword_processor import process_keywords, KeywordProcessor

__all__ = [
    # Main Service
    'KeywordPlannerService',
    
    # Individual modules
    'generate_seeds',
    'SeedGenerator',
    'validate_seeds',
    'SeedValidator',
    'get_gkp_client',
    'GKPClient',
    'validate_gkp_results',
    'GKPResultValidator',
    'get_low_hanging_fruit',
    'GSCKeywordClient',
    'process_keywords',
    'KeywordProcessor',
]
