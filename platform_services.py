import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException, status
from starlette.responses import HTMLResponse
import logging

from base_requests import (
    Page1BusinessInfoRequest,
    Page2GSCRequest,
    Page3AudienceRequest,
    Page4PortfolioRequest,
    Page5GoalsRequest,
    Page6KeywordsRequest,
    Page6CompetitorsRequest,
    Page7ContentFilterRequest,
    Page8ReportingRequest,
    StandardResponse,
    KeywordsResponse,
    ErrorResponse,
    Page6KeywordsResponse,
    ScrapeBusinessRequest,
    ScrapeBusinessResponse,
    KeywordUniverseInitRequest,
    KeywordSelectionRequest
)
from onboarding.scraper_services.scraper import scrape_business_description
from onboarding.fetch_profile_data import get_profile_manager
from onboarding.keyword_planner.planner_service import KeywordPlannerService
from onboarding.oauth_manager import OAuthManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OAuth Manager
oauth_manager = OAuthManager(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/callback"),
    encryption_key=os.getenv("ENCRYPTION_KEY")
)

# Create API router for incremental onboarding
api_router = APIRouter(tags=["Platform Services"])


@api_router.get(
    "/profile/{user_id}",
    summary="Get User Profile",
    description="Returns current profile data for the user"
)
async def get_user_profile(user_id: str):
    try:
        profile_manager = get_profile_manager()
        profile_data = profile_manager.get_profile(user_id)
        
        if not profile_data:
            # User profile not found in DB (e.g. ghost session).
            # Return partial to prevent frontend crash, but with no URL.
            return {"user_id": user_id, "website_url": None, "business_name": "Guest User"}
            
        return profile_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Page 1: Business Info ====================

# ==================== OAuth Endpoints ====================

@api_router.get(
    "/oauth/authorize",
    summary="Step 1: Get Google OAuth URL",
    description="Returns the Google authorization URL to redirect the user to"
)
async def get_oauth_url(user_id: str = None):
    """
    Generate Google OAuth authorization URL.
    Frontend should redirect user to this URL.
    
    Args:
        user_id: Optional user ID to include in state for callback
    """
    try:
        # Pass user_id as state parameter so we can retrieve it in callback
        auth_url = oauth_manager.get_authorization_url(state=user_id)
        
        return {
            "status": "success",
            "authorization_url": auth_url,
            "message": "Redirect user to this URL to authorize"
        }
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}"
        )


@api_router.get(
    "/oauth/callback",
    summary="Step 2: OAuth Callback",
    description="Receives authorization code from Google and exchanges for tokens"
)
async def oauth_callback(code: str, state: str = None):
    """
    Handle OAuth callback from Google.
    
    Query params:
        code: Authorization code from Google
        state: Contains user_id passed during authorization
    
    This endpoint:
    1. Exchanges code for access_token + refresh_token
    2. Stores encrypted refresh_token
    3. Returns HTML page that sends data to parent window
    """
    try:
        # Extract user_id from state parameter
        user_id = state
        
        if not user_id:
            logger.error("[OAuth] No user_id in state parameter")
            return HTMLResponse(content="""
            <html>
            <body>
                <script>
                    window.opener.postMessage({type: 'OAUTH_ERROR', error: 'Missing user ID'}, '*');
                    window.close();
                </script>
                <p>Error: Missing user ID. This window will close.</p>
            </body>
            </html>
            """)
        
        logger.info(f"[OAuth] Received callback for user: {user_id}")
        
        if not code:
            return HTMLResponse(content="""
            <html>
            <body>
                <script>
                    window.opener.postMessage({type: 'OAUTH_ERROR', error: 'Missing authorization code'}, '*');
                    window.close();
                </script>
                <p>Error: Missing authorization code. This window will close.</p>
            </body>
            </html>
            """)
        
        # Exchange code for tokens
        token_data = await oauth_manager.exchange_code_for_tokens(code)
        
        # Store refresh token (encrypted)
        oauth_manager.store_tokens(user_id, token_data)
        
        access_token = token_data.get("access_token", "")
        expires_in = token_data.get("expires_in", 3600)
        
        # Return HTML that sends data to parent window via postMessage
        return HTMLResponse(content=f"""
        <html>
        <body>
            <script>
                window.opener.postMessage({{
                    type: 'OAUTH_SUCCESS',
                    user_id: '{user_id}',
                    access_token: '{access_token}',
                    expires_in: {expires_in}
                }}, '*');
                setTimeout(() => window.close(), 500);
            </script>
            <div style="font-family: Arial; text-align: center; padding: 50px;">
                <h2 style="color: #10b981;">✓ Authentication Successful!</h2>
                <p>This window will close automatically...</p>
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        error_message = str(e).replace("'", "\\'")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <script>
                window.opener.postMessage({{type: 'OAUTH_ERROR', error: '{error_message}'}}, '*');
                setTimeout(() => window.close(), 2000);
            </script>
            <div style="font-family: Arial; text-align: center; padding: 50px;">
                <h2 style="color: #ef4444;">✗ Authentication Failed</h2>
                <p>{error_message}</p>
                <p>This window will close automatically...</p>
            </div>
        </body>
        </html>
        """)


@api_router.get(
    "/oauth/status/{user_id}",
    summary="Check OAuth Status",
    description="Check if user has valid stored credentials"
)
async def check_oauth_status(user_id: str):
    """
    Check if user has stored OAuth credentials.
    
    Returns:
        - has_credentials: Boolean
        - can_refresh: Boolean (if they have stored refresh token)
    """
    try:
        has_creds = oauth_manager.has_valid_credentials(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "has_credentials": has_creds,
            "can_refresh_token": has_creds
        }
        
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check OAuth status: {str(e)}"
        )


@api_router.get(
    "/oauth/refresh/{user_id}",
    summary="Refresh Access Token",
    description="Get a fresh access token using stored refresh token"
)
async def refresh_access_token(user_id: str):
    """
    Use stored refresh token to get a new access token.
    
    Returns:
        - access_token: Fresh access token for API calls
    """
    try:
        if not oauth_manager.has_valid_credentials(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stored credentials for this user. Please authenticate first."
            )
        
        access_token = await oauth_manager.refresh_access_token(user_id)
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token. Please re-authenticate."
            )
        
        return {
            "status": "success",
            "user_id": user_id,
            "access_token": access_token
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh access token: {str(e)}"
        )


# ==================== Onboarding Endpoints ====================

@api_router.post(
    "/onboarding/scrape-url",
    response_model=ScrapeBusinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape Business Description",
    description="Helper endpoint to scrape business description from a URL using Tavily."
)
async def scrape_url(request: ScrapeBusinessRequest) -> ScrapeBusinessResponse:
    """
    Scrape business description from URL.
    This is used in Page 1 to auto-fill the description.
    """
    try:
        url = request.url.strip()
        logger.info(f"Scraping URL: {url}")
        
        description = scrape_business_description(url)
        
        if description:
            return ScrapeBusinessResponse(
                status="success",
                description=description,
                url=url
            )
        else:
            return ScrapeBusinessResponse(
                status="error",
                error="Could not extract description from website",
                url=url
            )
            
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return ScrapeBusinessResponse(
            status="error",
            error=str(e),
            url=url
        )


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
    Generates user_id from email address if not provided.
    """
    try:
        from utils.user_id import generate_user_id_from_email
        
        logger.info(f"Saving business information for email: {request.email}")
        
        pm = get_profile_manager()
        
        # Generate user_id from email (deterministic)
        if request.user_id:
            user_id = request.user_id
        else:
            user_id = generate_user_id_from_email(request.email)
        
        # Prepare complete data (Pydantic already validated the inputs)
        profile_data = {
            # User identity
            'full_name': request.full_name.strip(),
            'email': request.email.lower().strip(),
            'username': request.username.strip(),
            # Business info
            'business_name': request.business_name.strip(),
            'website_url': str(request.website_url),  # Convert HttpUrl to string
            'business_description': request.business_description.strip()
        }
        
        # Create or update profile
        if pm.profile_exists(user_id):
            pm.update_profile(user_id, profile_data)
            logger.info(f"Updated profile for user: {user_id}")
        else:
            pm.create_profile_with_id(user_id, profile_data)
            logger.info(f"Created new profile for user: {user_id}")
        
        return StandardResponse(
            status="success",
            message="Business information saved successfully",
            user_id=user_id,
            data=profile_data
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
    "/onboarding/page2/validate-connections",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 2: Validate GSC and GA4 Access",
    description="Validate Google Search Console and GA4 access using OAuth tokens"
)
async def validate_gsc_ga4_connection(request: Page2GSCRequest) -> StandardResponse:
    """
    Validate GSC and GA4 connection (Page 2).
    
    This endpoint:
    1. Refreshes access token using stored refresh token (prevents expiry issues)
    2. Uses fresh access_token to validate ownership/access
    3. Stores validation results (NO heavy data fetching)
    """
    try:
        logger.info(f"Validating GSC/GA4 for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Always refresh access token to ensure it's valid
        # This uses the stored refresh_token + client credentials from .env
        try:
            if oauth_manager.has_valid_credentials(request.user_id):
                fresh_access_token = await oauth_manager.refresh_access_token(request.user_id)
                logger.info(f"[OAuth] Refreshed access token for user: {request.user_id}")
            else:
                # Fallback to provided token if no stored credentials
                fresh_access_token = request.access_token
                logger.warning(f"[OAuth] No stored credentials, using provided token for: {request.user_id}")
        except Exception as refresh_error:
            logger.error(f"[OAuth] Token refresh failed: {refresh_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed. Please re-authenticate with Google."
            )
        
        validation_results = {
            "gsc_validated": False,
            "ga4_validated": False,
            "gsc_sites": [],
            "ga4_properties": [],
            "matched_gsc_site": None,
            "errors": []
        }
        
        # GSC Validation
        if request.validate_gsc:
            try:
                from onboarding.ga_gsc_connection.gsc_connect import GSCConnector
                
                connector = GSCConnector(fresh_access_token)
                
                # List all owned sites
                sites = await connector.list_sites()
                validation_results["gsc_sites"] = sites
                
                # Validate ownership of target URL
                is_owner, matched_site = await connector.validate_ownership(request.target_url)
                
                if is_owner:
                    validation_results["gsc_validated"] = True
                    validation_results["matched_gsc_site"] = matched_site
                    logger.info(f"✓ GSC validated for {matched_site}")
                else:
                    validation_results["errors"].append(
                        f"GSC: User does not own {request.target_url}"
                    )
                    logger.warning(f"✗ GSC validation failed for {request.target_url}")
                    
            except Exception as e:
                validation_results["errors"].append(f"GSC Error: {str(e)}")
                logger.error(f"GSC validation error: {e}", exc_info=True)
        
        # GA4 Validation
        if request.validate_ga4:
            try:
                from onboarding.ga_gsc_connection.ga_connect import GA4Connector
                
                connector = GA4Connector(fresh_access_token)
                
                # List all accessible properties
                properties = connector.list_properties()
                validation_results["ga4_properties"] = properties
                
                if not properties:
                    validation_results["errors"].append("GA4: No properties found")
                    logger.warning("✗ GA4 validation: No properties accessible")
                else:
                    # Strict Validation: Check if any property has a data stream matching the target URL
                    matched_stream = None
                    target_clean = request.target_url.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
                    
                    for prop in properties:
                        streams = connector.list_data_streams(prop['resource_name'])
                        for stream in streams:
                            stream_uri = stream.get('default_uri', '')
                            if stream_uri:
                                stream_clean = stream_uri.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
                                if target_clean == stream_clean:
                                    matched_stream = stream
                                    break
                        if matched_stream:
                            break
                    
                    if matched_stream:
                        validation_results["ga4_validated"] = True
                        logger.info(f"✓ GA4 validated: Found matching stream {matched_stream['default_uri']}")
                    else:
                        validation_results["errors"].append(f"GA4: No property found for {request.target_url}")
                        logger.warning(f"✗ GA4 validation: No matching stream for {request.target_url}")
                    
            except Exception as e:
                validation_results["errors"].append(f"GA4 Error: {str(e)}")
                logger.error(f"GA4 validation error: {e}", exc_info=True)
        
        # Save validation status to profile
        connection_data = {
            'gsc_connected': validation_results["gsc_validated"],
            'ga4_connected': validation_results["ga4_validated"],
            'gsc_matched_site': validation_results["matched_gsc_site"]
        }
        pm.update_profile(request.user_id, connection_data)
        
        # Determine overall status
        overall_success = (
            (not request.validate_gsc or validation_results["gsc_validated"]) and
            (not request.validate_ga4 or validation_results["ga4_validated"])
        )
        
        return StandardResponse(
            status="success" if overall_success else "partial",
            message="Validation complete" if overall_success else "Validation completed with warnings",
            user_id=request.user_id,
            data=validation_results
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error validating connections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating connections: {str(e)}"
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
            'products': [p.dict() for p in request.products],
            'services': [s.dict() for s in request.services],
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
        profile = pm.get_profile(user_id)
        
        # Check if required data is present
        required_fields = ['business_name', 'business_description', 'customer_description']
        missing_fields = [field for field in required_fields if field not in profile or not profile[field]]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields for keyword generation: {', '.join(missing_fields)}"
            )
        
        # Check Portfolio (At least one product OR service required)
        products = profile.get('products', [])
        services = profile.get('services', [])
        if not products and not services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Portfolio data: At least one Product or Service is required for keyword generation."
            )
        
        try:
            # Import keyword generation functions
            from onboarding.keyword_generation import generate_keywords_for_user, rank_keywords
            
            # Generate keywords (30 suggestions)
            keywords = generate_keywords_for_user(profile, count=30)
            
            # Rank ALL keywords
            all_ranked_keywords = rank_keywords(keywords, profile)
            
            # Save generated keywords (using full ranked list with scores)
            pm.save_keywords_generated(user_id, all_ranked_keywords)
            
            # Select top 15 for response
            ranked_keywords = all_ranked_keywords[:15]
            
            # Extract keyword strings for selected keywords (default selection)
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

@api_router.post(
    "/onboarding/page6/submit-keywords",
    response_model=Page6KeywordsResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 6 Step 1: Submit Keywords and Get Suggested Competitors",
    description="User submits selected + custom keywords. Backend runs competitor analysis and returns suggested competitors."
)
async def submit_keywords_get_competitors(request: Page6KeywordsRequest) -> Page6KeywordsResponse:
    """
    Page 6 Step 1: Submit keywords and trigger competitor discovery.
    
    Flow:
    1. User submits selected keywords + custom keywords
    2. Backend combines and saves keywords
    3. Backend runs competitor analysis on these keywords
    4. Backend returns suggested competitors from SERP data
    5. User can then select/add competitors in Step 2
    """
    try:
        logger.info(f"[Page 6 Step 1] Submitting keywords for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Combine and deduplicate keywords
        final_keywords = list(set(request.selected_keywords + request.custom_keywords))
        
        # Validate
        if len(final_keywords) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 1 keyword is required"
            )
        
        if len(final_keywords) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 keywords allowed"
            )
        
        # Save keywords to profile
        pm.save_keywords_selected(request.user_id, final_keywords)
        
        logger.info(f"[Page 6 Step 1] Saved {len(final_keywords)} keywords. Running competitor analysis...")
        
        # Run competitor analysis to get suggested competitors
        from onboarding.competitor_analysis.competitor_analysis import analyze_competitors
        
        # Get Google CSE credentials
        google_cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
        google_cse_cx = os.getenv("GOOGLE_CSE_CX")
        
        if not google_cse_api_key or not google_cse_cx:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Custom Search not configured"
            )
        
        # Load profile for location
        profile = pm.get_profile(request.user_id)
        
        # Run competitor analysis
        competitor_result = await analyze_competitors(
            keywords=final_keywords,
            google_cse_api_key=google_cse_api_key,
            google_cse_cx=google_cse_cx,
            top_results_per_keyword=10,
            final_top_competitors=10,
            location=profile.get("location_scope", "India"),
            language="en"
        )
        
        # Save suggested competitors to profile (not final, just suggestions)
        pm.update_profile(request.user_id, {
            "suggested_competitors": competitor_result["top_competitors"]
        })
        
        logger.info(f"[Page 6 Step 1] Found {len(competitor_result['top_competitors'])} suggested competitors")
        
        return Page6KeywordsResponse(
            status="success",
            message=f"Keywords saved and competitor analysis complete",
            user_id=request.user_id,
            data={
                "final_keywords": final_keywords,
                "total_keywords": len(final_keywords),
                "suggested_competitors": competitor_result["top_competitors"],
                "next_step": "Select competitors from suggestions or add manual competitors"
            }
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[Page 6 Step 1] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing keywords: {str(e)}"
        )

@api_router.post(
    "/onboarding/page6/submit-competitors",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Page 6 Step 2: Submit Final Competitors",
    description="User submits selected competitors from suggested list + manual competitors"
)
async def submit_final_competitors(request: Page6CompetitorsRequest) -> StandardResponse:
    """
    Page 6 Step 2: Submit final competitor selection.
    
    Flow:
    1. User has received suggested competitors from Step 1
    2. User selects competitors from suggestions
    3. User optionally adds manual competitors
    4. Backend saves final competitor list
    """
    try:
        logger.info(f"[Page 6 Step 2] Submitting competitors for user: {request.user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {request.user_id}"
            )
        
        # Load profile to get suggested competitors
        profile = pm.get_profile(request.user_id)
        suggested_competitors = profile.get("suggested_competitors", [])
        
        # Prepare final competitor list
        final_competitors = []
        
        # Add selected competitors from suggestions
        for domain in request.selected_competitors:
            # Find in suggested list
            matched = next((c for c in suggested_competitors if c["domain"] == domain), None)
            if matched:
                final_competitors.append({
                    "domain": matched["domain"],
                    "source": "DISCOVERED",
                    "importance": matched.get("importance"),
                    "priority": matched.get("priority"),
                    "keywords_matched": matched.get("keywords_matched", [])
                })
        
        # Add manual competitors
        for comp in request.manual_competitors:
            final_competitors.append({
                "domain": comp.website,
                "name": comp.name,
                "source": "MANUAL",
                "importance": None,
                "priority": None,
                "keywords_matched": []
            })
        
        # Save final competitors
        pm.update_profile(request.user_id, {
            "final_competitors": final_competitors,
            "competitor_selection_complete": True
        })
        
        logger.info(f"[Page 6 Step 2] Saved {len(final_competitors)} final competitors (Selected: {len(request.selected_competitors)}, Manual: {len(request.manual_competitors)})")
        
        return StandardResponse(
            status="success",
            message=f"Competitors saved successfully",
            user_id=request.user_id,
            data={
                "total_competitors": len(final_competitors),
                "selected_from_suggested": len(request.selected_competitors),
                "manual_added": len(request.manual_competitors),
                "final_competitors": final_competitors
            }
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[Page 6 Step 2] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving competitors: {str(e)}"
        )
        
        
        
        
@api_router.post(
    "/onboarding/competitor-analysis/{user_id}",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Competitor Analysis: Analyze Competitors from Page 6 Keywords",
    description="Fetches Page 6 finalized keywords and discovers competitors using Google SERP data"
)
async def analyze_competitors_endpoint(user_id: str) -> StandardResponse:
    """
    Analyze competitors based on Page 6 selected keywords.
    
    This endpoint:
    1. Fetches the user's selected keywords from Page 6
    2. Runs competitor analysis using Google Custom Search
    3. Returns ranked competitors with priority buckets
    """
    try:
        logger.info(f"[Competitor Analysis] Starting analysis for user: {user_id}")
        
        pm = get_profile_manager()
        
        if not pm.profile_exists(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found: {user_id}"
            )
        
        # Load user profile
        profile = pm.get_profile(user_id)
        
        # Get selected keywords from Page 6
        selected_keywords = profile.get("selected_keywords", [])
        
        if not selected_keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No keywords found. Please complete Page 6 first."
            )
        
        # Import competitor analysis function
        from onboarding.competitor_analysis.competitor_analysis import analyze_competitors
        
        # Get Google CSE credentials from config
        google_cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
        google_cse_cx = os.getenv("GOOGLE_CSE_CX")
        
        if not google_cse_api_key or not google_cse_cx:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Custom Search not configured"
            )
        
        # Run competitor analysis
        result = await analyze_competitors(
            keywords=selected_keywords,
            google_cse_api_key=google_cse_api_key,
            google_cse_cx=google_cse_cx,
            top_results_per_keyword=10,
            final_top_competitors=10,
            location=profile.get("location_scope", "India"),
            language="en"
        )
        
        # Save competitor analysis results to profile
        pm.update_profile(user_id, {
            "competitor_analysis": result["top_competitors"],
            "competitor_analysis_date": "2025-12-20"
        })
        
        logger.info(f"[Competitor Analysis] Found {len(result['top_competitors'])} competitors")
        
        return StandardResponse(
            status="success",
            message=f"Competitor analysis complete. Found {result['keywords_analyzed']} keywords, {len(result['top_competitors'])} competitors.",
            user_id=user_id,
            data=result
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[Competitor Analysis] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Competitor analysis failed: {str(e)}"
        )

# ==================== Strategy / Keyword Planner API ====================

@api_router.post("/strategy/keywords/initialize", tags=["Strategy"], response_model=StandardResponse)
async def initialize_keyword_universe(request: KeywordUniverseInitRequest):
    """Initialize Keyword Universe (Phase 1-4)"""
    service = KeywordPlannerService()
    try:
        result = await service.initialize_universe(request.user_id)
        return StandardResponse(
            status="success",  
            message="Keyword Universe initialized successfully", 
            user_id=request.user_id, 
            data=result
        )
    except Exception as e:
        logger.error(f"Error initializing universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.cleanup()

@api_router.get("/strategy/keywords/{user_id}", tags=["Strategy"], response_model=StandardResponse)
async def get_keyword_universe(user_id: str):
    """Get current Keyword Universe state"""
    service = KeywordPlannerService()
    try:
        result = service.get_universe(user_id)
        return StandardResponse(
            status="success", 
            message="Keyword Universe fetched", 
            user_id=user_id, 
            data=result
        )
    except Exception as e:
        logger.error(f"Error fetching universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.cleanup()

@api_router.post("/strategy/keywords/{user_id}/finalize", tags=["Strategy"], response_model=StandardResponse)
async def finalize_keyword_selection(user_id: str, request: KeywordSelectionRequest):
    """Finalize selection and Lock Universe (Phase 5)"""
    service = KeywordPlannerService()
    try:
        result = service.finalize_selection(user_id, request.selected_keyword_ids)
        return StandardResponse(
            status="success", 
            message="Keyword selection finalized and locked", 
            user_id=user_id, 
            data=result
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error finalizing selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.cleanup()


# ==================== AS-IS State API ====================

from base_requests import (
    AsIsSummaryRequest, AsIsParametersRequest, AsIsRefreshRequest, AsIsCompetitorsRequest,
    AsIsSummaryResponse, AsIsParametersResponse, AsIsCompetitorsResponse, AsIsRefreshResponse
)
from asis.asis_service import AsIsStateService

# Initialize AS-IS service with SERP API key
asis_service = AsIsStateService(serp_api_key=os.getenv("SERP_API_KEY"))


@api_router.post(
    "/as-is/summary",
    response_model=AsIsSummaryResponse,
    status_code=status.HTTP_200_OK,
    tags=["AS-IS State"],
    summary="Get AS-IS Summary",
    description="Get summary data for the four top cards (Traffic, Keywords, SERP Features, Competitors)"
)
async def get_asis_summary(request: AsIsSummaryRequest) -> AsIsSummaryResponse:
    """
    Get AS-IS summary data for the dashboard cards.
    Requires an access token which should be refreshed before calling.
    """
    try:
        # Get fresh access token
        access_token_result = await oauth_manager.get_fresh_access_token(request.user_id)
        if not access_token_result.get("access_token"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid access token. Please reconnect Google account."
            )
        
        access_token = access_token_result["access_token"]
        
        # Fetch competitors from profile if not provided
        competitors = request.competitors
        if not competitors:
            try:
                pm = get_profile_manager()
                profile = pm.get_profile(request.user_id)
                final_comps = profile.get("final_competitors", [])
                competitors = [c["domain"] for c in final_comps if c.get("domain")]
            except Exception as e:
                logger.warning(f"Could not fetch competitors from profile: {e}")
                competitors = []

        # Get summary data
        summary = await asis_service.get_summary(
            user_id=request.user_id,
            access_token=access_token,
            site_url=request.site_url,
            tracked_keywords=request.tracked_keywords,
            competitors=competitors
        )
        
        return AsIsSummaryResponse(
            status="success",
            message="AS-IS summary retrieved successfully",
            user_id=request.user_id,
            data=summary
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[AS-IS] Error getting summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving AS-IS summary: {str(e)}"
        )


@api_router.post(
    "/as-is/parameters",
    response_model=AsIsParametersResponse,
    status_code=status.HTTP_200_OK,
    tags=["AS-IS State"],
    summary="Get AS-IS Parameters",
    description="Get parameter scores for a specific tab (onpage, offpage, technical)"
)
async def get_asis_parameters(request: AsIsParametersRequest) -> AsIsParametersResponse:
    """
    Get AS-IS parameter scores for the specified tab.
    Supports filtering by status (optimal, needs_attention).
    """
    try:
        # Validate tab
        valid_tabs = ["onpage", "offpage", "technical"]
        if request.tab not in valid_tabs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tab. Must be one of: {', '.join(valid_tabs)}"
            )
        
        # Validate filter
        if request.status_filter and request.status_filter not in ["optimal", "needs_attention"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filter. Must be 'optimal' or 'needs_attention'"
            )
        
        # Get fresh access token
        access_token_result = await oauth_manager.get_fresh_access_token(request.user_id)
        access_token = access_token_result.get("access_token", "")
        
        # Get parameters
        parameters = await asis_service.get_parameters(
            user_id=request.user_id,
            access_token=access_token,
            site_url=request.site_url,
            priority_urls=request.priority_urls,
            tab=request.tab,
            status_filter=request.status_filter
        )
        
        return AsIsParametersResponse(
            status="success",
            message=f"AS-IS {request.tab} parameters retrieved",
            user_id=request.user_id,
            data=parameters
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[AS-IS] Error getting parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving parameters: {str(e)}"
        )


@api_router.get(
    "/as-is/parameters/{tab}/{group_id}/details",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    tags=["AS-IS State"],
    summary="Get Parameter Details",
    description="Get detailed information about a specific parameter group"
)
async def get_asis_parameter_details(
    tab: str,
    group_id: str,
    user_id: str
) -> StandardResponse:
    """
    Get detailed sub-parameters, explanations, and recommendations for a parameter group.
    """
    try:
        # Validate tab
        if tab not in ["onpage", "offpage", "technical"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tab"
            )
        
        details = await asis_service.get_parameter_details(
            user_id=user_id,
            tab=tab,
            group_id=group_id
        )
        
        return StandardResponse(
            status="success",
            message="Parameter details retrieved",
            user_id=user_id,
            data=details
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[AS-IS] Error getting details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving details: {str(e)}"
        )


@api_router.post(
    "/as-is/competitors",
    response_model=AsIsCompetitorsResponse,
    status_code=status.HTTP_200_OK,
    tags=["AS-IS State"],
    summary="Get AS-IS Competitors",
    description="Get competitor visibility scores and rankings"
)
async def get_asis_competitors(request: AsIsCompetitorsRequest) -> AsIsCompetitorsResponse:
    """
    Get competitor visibility scores and ranking.
    Returns empty state if no competitors configured.
    """
    try:
        # Get fresh access token
        access_token_result = await oauth_manager.get_fresh_access_token(request.user_id)
        access_token = access_token_result.get("access_token", "")
        
        competitors_data = await asis_service.get_competitors(
            user_id=request.user_id,
            access_token=access_token,
            site_url=request.site_url,
            competitors=request.competitors
        )
        
        return AsIsCompetitorsResponse(
            status="success",
            message="Competitor data retrieved",
            user_id=request.user_id,
            data=competitors_data
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[AS-IS] Error getting competitors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving competitors: {str(e)}"
        )


@api_router.post(
    "/as-is/refresh",
    response_model=AsIsRefreshResponse,
    status_code=status.HTTP_200_OK,
    tags=["AS-IS State"],
    summary="Refresh AS-IS Data",
    description="Trigger a full data refresh for AS-IS State"
)
async def refresh_asis_data(request: AsIsRefreshRequest) -> AsIsRefreshResponse:
    """
    Trigger a full refresh of AS-IS data.
    This will:
    - Fetch latest GSC data
    - Crawl priority URLs
    - Update SERP features
    - Recompute all scores
    """
    try:
        # Get fresh access token
        access_token_result = await oauth_manager.get_fresh_access_token(request.user_id)
        access_token = access_token_result.get("access_token", "")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid access token. Please reconnect Google account."
            )
        
        refresh_result = await asis_service.refresh_data(
            user_id=request.user_id,
            access_token=access_token,
            site_url=request.site_url,
            priority_urls=request.priority_urls,
            tracked_keywords=request.tracked_keywords,
            competitors=request.competitors
        )
        
        return AsIsRefreshResponse(
            status="success",
            message="AS-IS data refreshed",
            user_id=request.user_id,
            data=refresh_result
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[AS-IS] Error refreshing data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing data: {str(e)}"
        )

