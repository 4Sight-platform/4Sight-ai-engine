import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException, status
import logging

from base_requests import (
    Page1BusinessInfoRequest,
    Page2GSCRequest,
    Page3AudienceRequest,
    Page4PortfolioRequest,
    Page5GoalsRequest,
    Page7ContentFilterRequest,
    Page8ReportingRequest,
    StandardResponse,
    KeywordsResponse,
    ErrorResponse
)
from onboarding.fetch_profile_data import get_profile_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API router for incremental onboarding
api_router = APIRouter(tags=["Platform Services"])


@api_router.post(
    "/onboarding/page1/business-info",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 1: Submit Business Information",
    description="Submit business information and create/update user profile"
)
async def save_business_info(request: Page1BusinessInfoRequest) -> StandardResponse:
    """
    Save business information (Page 1).
    Creates a new user_id if not provided.
    """
    try:
        logger.info("Saving business information")
        
        pm = get_profile_manager()
        
        # Create or update profile
        if request.user_id and pm.profile_exists(request.user_id):
            user_id = request.user_id
        else:
            user_id = pm.create_profile()
        
        # Prepare data (Pydantic already validated the inputs)
        business_data = {
            'business_name': request.business_name.strip(),
            'website_url': str(request.website_url),  # Convert HttpUrl to string
            'business_description': request.business_description.strip()
        }
        
        pm.update_profile(user_id, business_data)
        logger.info(f"Saved business information for user: {user_id}")
        
        return StandardResponse(
            status="success",
            message="Business information saved successfully",
            user_id=user_id,
            data=business_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving business info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving business information: {str(e)}"
        )


@api_router.post(
    "/onboarding/page2/gsc",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 2: Submit GSC Connection Status",
    description="Save Google Search Console connection status"
)
async def save_gsc_connection(request: Page2GSCRequest) -> StandardResponse:
    """Save GSC connection status (Page 2)."""
    try:
        logger.info(f"Saving GSC connection for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        gsc_data = {'gsc_connected': request.gsc_connected}
        pm.update_profile(request.user_id, gsc_data)
        
        return StandardResponse(
            status="success",
            message="GSC connection status saved successfully",
            user_id=request.user_id,
            data=gsc_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving GSC connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving GSC connection: {str(e)}"
        )


@api_router.post(
    "/onboarding/page3/audience",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 3: Submit Audience Information",
    description="Save audience and search intent information"
)
async def save_audience_info(request: Page3AudienceRequest) -> StandardResponse:
    """Save audience information (Page 3)."""
    try:
        logger.info(f"Saving audience information for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Validate location scope
        valid_scopes = ["local", "regional", "nationwide", "international"]
        if request.location_scope.lower() not in valid_scopes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid location scope. Must be one of: {', '.join(valid_scopes)}"
            )
        
        # Validate search intent count (1-2 intents required)
        if len(request.search_intent) < 1 or len(request.search_intent) > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search intent must have 1 or 2 selections"
            )
        
        # Normalize and validate search intent values
        # Map common variations to standard values
        intent_mapping = {
            "information": "information",
            "info": "information",
            "comparison": "comparison",
            "compare": "comparison",
            "deal": "deal",
            "deals": "deal",
            "action-focused": "action-focused",
            "action": "action-focused",  # Normalize 'action' to 'action-focused'
            "action_focused": "action-focused"
        }
        
        normalized_intents = []
        for intent in request.search_intent:
            normalized = intent_mapping.get(intent.lower().strip())
            if not normalized:
                valid_keys = list(set(intent_mapping.values()))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid search intent '{intent}'. Must be one of: {', '.join(valid_keys)}"
                )
            normalized_intents.append(normalized)
        
        audience_data = {
            'location_scope': request.location_scope.lower(),
            'selected_locations': request.selected_locations,
            'customer_description': request.customer_description,
            'search_intent': normalized_intents  # Use normalized values
        }
        
        pm.update_profile(request.user_id, audience_data)
        
        return StandardResponse(
            status="success",
            message="Audience information saved successfully",
            user_id=request.user_id,
            data=audience_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving audience info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving audience information: {str(e)}"
        )


@api_router.post(
    "/onboarding/page4/portfolio",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 4: Submit Business Portfolio",
    description="Save products, services, and differentiators"
)
async def save_portfolio(request: Page4PortfolioRequest) -> StandardResponse:
    """Save business portfolio (Page 4)."""
    try:
        logger.info(f"Saving portfolio for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        portfolio_data = {
            'products': request.products,
            'services': request.services,
            'differentiators': request.differentiators
        }
        
        pm.update_profile(request.user_id, portfolio_data)
        
        return StandardResponse(
            status="success",
            message="Business portfolio saved successfully",
            user_id=request.user_id,
            data=portfolio_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving portfolio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving portfolio: {str(e)}"
        )


@api_router.post(
    "/onboarding/page5/goals",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 5: Submit SEO Goals",
    description="Save SEO goals and trigger keyword generation"
)
async def save_seo_goals(request: Page5GoalsRequest) -> StandardResponse:
    """
    Save SEO goals (Page 5).
    This endpoint prepares the profile for keyword generation in the next step.
    """
    try:
        logger.info(f"Saving SEO goals for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Validate SEO goals
        valid_goals = ["organic_traffic", "search_visibility", "local_visibility", "top_rankings"]
        for goal in request.seo_goals:
            if goal.lower() not in valid_goals:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid SEO goal. Must be one of: {', '.join(valid_goals)}"
                )
        
        goals_data = {'seo_goals': [goal.lower() for goal in request.seo_goals]}
        pm.update_profile(request.user_id, goals_data)
        
        return StandardResponse(
            status="success",
            message="SEO goals saved successfully. Ready for keyword generation.",
            user_id=request.user_id,
            data=goals_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving SEO goals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving SEO goals: {str(e)}"
        )


@api_router.get(
    "/onboarding/page6/keywords/{user_id}",
    response_model=KeywordsResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 6: Generate and Retrieve Keywords",
    description="Generate keywords based on user profile and return ranked suggestions"
)
async def generate_keywords(user_id: str) -> KeywordsResponse:
    """
    Generate keywords (Page 6).
    This endpoint generates keywords based on all the information collected so far.
    """
    try:
        logger.info(f"Generating keywords for user: {user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {user_id}"
            )
        
        # Load profile
        profile = pm.load_profile(user_id)
        
        # Check if required data is present
        required_fields = ['business_name', 'business_description', 'customer_description']
        missing_fields = [field for field in required_fields if field not in profile]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields for keyword generation: {', '.join(missing_fields)}"
            )
        
        try:
            # Import keyword generation functions
            from onboarding.keyword_generation import generate_keywords_for_user, rank_keywords
            
            # Generate keywords (30 suggestions)
            keywords = generate_keywords_for_user(profile, count=30)
            
            # Rank keywords and select top 15
            ranked_keywords = rank_keywords(keywords, profile)[:15]
            
            # Save generated keywords
            pm.save_keywords_generated(user_id, keywords)
            
            # Extract keyword strings for selected keywords
            selected_keyword_strings = [kw['keyword'] for kw in ranked_keywords]
            
            # Save selected keywords
            pm.save_keywords_selected(user_id, selected_keyword_strings)
            
            logger.info(f"Generated {len(keywords)} keywords, selected top {len(selected_keyword_strings)} for user: {user_id}")
            
            return KeywordsResponse(
                status="success",
                message=f"Generated {len(keywords)} keywords successfully",
                user_id=user_id,
                data={
                    "generated_keywords": ranked_keywords,
                    "selected_keywords": selected_keyword_strings,
                    "total_generated": len(keywords),
                    "total_selected": len(selected_keyword_strings)
                }
            )
        
        except ImportError as e:
            logger.warning(f"Keyword generation not available: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Keyword generation service is not available"
            )
        except Exception as e:
            logger.error(f"Error generating keywords: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating keywords: {str(e)}"
            )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in keyword generation endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating keywords: {str(e)}"
        )


@api_router.post(
    "/onboarding/page7/content-filter",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 7: Submit Content Filter",
    description="Save page URLs for content filtering"
)
async def save_content_filter(request: Page7ContentFilterRequest) -> StandardResponse:
    """Save content filter (Page 7)."""
    try:
        logger.info(f"Saving content filter for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        page_urls_data = {
            'page_urls': {
                'home': request.page_urls.home,
                'product': request.page_urls.product,
                'contact': request.page_urls.contact,
                'about': request.page_urls.about,
                'blog': request.page_urls.blog
            }
        }
        
        pm.update_profile(request.user_id, page_urls_data)
        
        return StandardResponse(
            status="success",
            message="Content filter saved successfully",
            user_id=request.user_id,
            data=page_urls_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving content filter: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving content filter: {str(e)}"
        )


@api_router.post(
    "/onboarding/page8/reporting",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 8: Submit Reporting Settings",
    description="Save reporting settings and mark onboarding as complete"
)
async def save_reporting(request: Page8ReportingRequest) -> StandardResponse:
    """
    Save reporting settings (Page 8).
    This endpoint also marks the onboarding as complete.
    """
    try:
        logger.info(f"Saving reporting settings for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Validate reporting channels
        valid_channels = ["email", "dashboard"]
        for channel in request.reporting_channels:
            if channel.lower() not in valid_channels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid reporting channel. Must be one of: {', '.join(valid_channels)}"
                )
        
        # Validate report frequency
        valid_frequencies = ["daily", "weekly", "monthly"]
        if request.report_frequency.lower() not in valid_frequencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report frequency. Must be one of: {', '.join(valid_frequencies)}"
            )
        
        # Validate email addresses
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in request.email_addresses:
            if not re.match(email_pattern, email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid email format: {email}"
                )
        
        reporting_data = {
            'reporting_channels': [channel.lower() for channel in request.reporting_channels],
            'email_addresses': request.email_addresses,
            'report_frequency': request.report_frequency.lower()
        }
        
        pm.update_profile(request.user_id, reporting_data)
        
        # Mark onboarding as complete
        pm.mark_onboarding_complete(request.user_id)
        
        logger.info(f"Onboarding completed for user: {request.user_id}")
        
        return StandardResponse(
            status="success",
            message="Reporting settings saved and onboarding completed successfully",
            user_id=request.user_id,
            data=reporting_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving reporting settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving reporting settings: {str(e)}"
        )
