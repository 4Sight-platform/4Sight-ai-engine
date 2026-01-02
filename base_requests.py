from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional, Dict, Any


# ==================== Request Models ====================

class PageUrlsModel(BaseModel):
    """Page URLs for content filtering"""
    home: str = Field(..., description="Home page URL")
    product: str = Field(..., description="Product page URL")
    contact: str = Field(..., description="Contact page URL")
    about: str = Field(..., description="About page URL")
    blog: str = Field(..., description="Blog URL")


class KeywordData(BaseModel):
    """Keyword information with ranking score"""
    keyword: str = Field(..., description="Keyword phrase")
    score: float = Field(..., description="Keyword ranking score")


# ==================== Incremental Onboarding Request Models ====================

class Page1BusinessInfoRequest(BaseModel):
    """Page 1: Business Information"""
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    business_name: str = Field(..., min_length=2, max_length=100, description="Business name")
    website_url: HttpUrl = Field(..., description="Website URL")
    business_description: str = Field(..., max_length=500, description="Business description")
    user_id: Optional[str] = Field(None, description="User ID (generated from email if None)")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError("Invalid email format")
        return value.lower().strip()
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return value.strip()
    
    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Business name cannot be empty")
        return value.strip()
    
    @field_validator("website_url")
    @classmethod
    def validate_website_url(cls, value: HttpUrl) -> HttpUrl:
        if not value:
            raise ValueError("Website URL cannot be empty")
        return value


class Page2GSCRequest(BaseModel):
    """Page 2: GSC/GA4 Connection and Validation"""
    user_id: str = Field(..., description="User ID from Page 1")
    access_token: str = Field(..., description="OAuth access token for GSC/GA4")
    target_url: str = Field(..., description="Website URL to validate GSC ownership")
    validate_gsc: bool = Field(default=True, description="Whether to validate GSC")
    validate_ga4: bool = Field(default=True, description="Whether to validate GA4")


class Page3AudienceRequest(BaseModel):
    """Page 3: Audience & Search Intent"""
    user_id: str = Field(..., description="User ID")
    location_scope: str = Field(..., description="Location scope")
    selected_locations: List[str] = Field(default_factory=list, max_length=5, description="Selected locations")
    customer_description: str = Field(..., description="Target customer description")
    search_intent: List[str] = Field(..., min_length=1, max_length=2, description="Primary search intent types (1-2 selections)")


class ProductItem(BaseModel):
    """Product with name and URL"""
    product_name: str = Field(..., min_length=1, max_length=255, description="Product name")
    product_url: Optional[str] = Field(None, max_length=500, description="Product page URL")


class ServiceItem(BaseModel):
    """Service with name and URL"""
    service_name: str = Field(..., min_length=1, max_length=255, description="Service name")
    service_url: Optional[str] = Field(None, max_length=500, description="Service page URL")


class Page4PortfolioRequest(BaseModel):
    """Page 4: Business Portfolio"""
    user_id: str = Field(..., description="User ID")
    products: List[ProductItem] = Field(default_factory=list, max_length=10, description="Products with names and URLs")
    services: List[ServiceItem] = Field(default_factory=list, max_length=10, description="Services with names and URLs")
    differentiators: List[str] = Field(default_factory=list, max_length=5, description="Brand differentiators")


class Page5GoalsRequest(BaseModel):
    """Page 5: SEO Goals"""
    user_id: str = Field(..., description="User ID")
    seo_goals: List[str] = Field(..., min_length=1, description="SEO goals")


class Page7ContentFilterRequest(BaseModel):
    """Page 7: Content Filter (Page URLs)"""
    user_id: str = Field(..., description="User ID")
    page_urls: PageUrlsModel = Field(..., description="Key page URLs")


class Page8ReportingRequest(BaseModel):
    """Page 8: Reporting & Notifications"""
    user_id: str = Field(..., description="User ID")
    reporting_channels: List[str] = Field(..., min_length=1, description="Reporting channels")
    email_addresses: List[str] = Field(default_factory=list, max_length=5, description="Email addresses")
    report_frequency: str = Field(..., description="Report frequency")

class Page6KeywordsRequest(BaseModel):
    """Page 6 Step 1: Submit Keywords"""
    user_id: str = Field(..., description="User ID")
    selected_keywords: List[str] = Field(..., min_length=1, max_length=50, description="Selected keywords from suggested list")
    custom_keywords: List[str] = Field(default_factory=list, max_length=20, description="Custom keywords added by user")


class ManualCompetitor(BaseModel):
    """Manual competitor input"""
    name: str = Field(..., min_length=1, max_length=100, description="Competitor name")
    website: str = Field(..., description="Competitor website URL")


class Page6CompetitorsRequest(BaseModel):
    """Page 6 Step 2: Submit Competitors"""
    user_id: str = Field(..., description="User ID")
    selected_competitors: List[str] = Field(default_factory=list, max_length=10, description="Selected competitor domains from suggested list")
    manual_competitors: List[ManualCompetitor] = Field(default_factory=list, max_length=5, description="Manual competitors added by user")


# ==================== Response Models ====================

class StandardResponse(BaseModel):
    """Standard API response for onboarding pages"""
    status: str = Field(..., description="Status of the request: success or error")
    message: str = Field(..., description="Human-readable message")
    user_id: Optional[str] = Field(None, description="User ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class Page2ValidationResponse(BaseModel):
    """Response model for Page 2 GSC/GA4 validation"""
    status: str = Field(..., description="Status of the validation")
    message: str = Field(..., description="Human-readable message")
    user_id: str = Field(..., description="User ID")
    data: Dict[str, Any] = Field(..., description="Validation results including owned sites/properties")


class KeywordsResponse(BaseModel):
    """Response model for keyword generation (Page 6)"""
    status: str = Field(..., description="Status of keyword generation")
    message: str = Field(..., description="Human-readable message")
    user_id: str = Field(..., description="User ID")
    data: Dict[str, Any] = Field(..., description="Keywords data with generated and selected keywords")


class ErrorResponse(BaseModel):
    """Error response model for all endpoints"""
    status: str = Field(default="error", description="Status (always 'error')")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class CompetitorSuggestion(BaseModel):
    """Model for a suggested competitor from analysis"""
    domain: str = Field(..., description="Competitor domain")
    importance: int = Field(..., description="Relevance score based on keyword intersection")
    priority: str = Field(..., description="Priority bucket: HIGH/MEDIUM/LOW")
    keywords_matched: List[str] = Field(..., description="Keywords where this competitor appeared")


class Page6KeywordsResponseData(BaseModel):
    final_keywords: List[str]
    total_keywords: int
    suggested_competitors: List[CompetitorSuggestion]
    next_step: str


class Page6KeywordsResponse(BaseModel):
    """Response model for submitting keywords and receiving competitor suggestions"""
    status: str = Field(..., description="Status")
    message: str = Field(..., description="Message")
    user_id: str = Field(..., description="User ID")
    data: Page6KeywordsResponseData = Field(..., description="Response data containing suggested competitors")


class ScrapeBusinessRequest(BaseModel):
    """Request to scrape business description from URL"""
    url: str = Field(..., description="Website URL to scrape")


class ScrapeBusinessResponse(BaseModel):
    """Response for business scraping"""
    status: str = Field(..., description="Status (success/error)")
    description: Optional[str] = Field(None, description="Scraped business description")
    url: str = Field(..., description="Normalized URL")
    error: Optional[str] = Field(None, description="Error message if failed")

# ==================== Strategy / Keyword Planner Models ====================

class KeywordUniverseInitRequest(BaseModel):
    """Initialize Keyword Universe request"""
    user_id: str = Field(..., description="User ID")

class KeywordSelectionRequest(BaseModel):
    """Finalize Keyword Selection request"""
    # Must select 10-15 keywords
    selected_keyword_ids: List[int] = Field(..., min_length=10, max_length=15, description="List of 10-15 selected keyword IDs")
    lock_until: Optional[str] = Field(None, description="Optional lock expiry date")


# ==================== AS-IS State Models ====================

class AsIsSummaryRequest(BaseModel):
    """Request for AS-IS summary data"""
    user_id: str = Field(..., description="User ID")
    site_url: str = Field(..., description="User's website URL")
    tracked_keywords: Optional[List[str]] = Field(default=None, description="Tracked keywords")
    competitors: Optional[List[str]] = Field(default=None, description="Competitor domains")


class AsIsParametersRequest(BaseModel):
    """Request for AS-IS parameters"""
    user_id: str = Field(..., description="User ID")
    site_url: str = Field(..., description="User's website URL")
    tab: str = Field(default="onpage", description="Tab: onpage, offpage, or technical")
    status_filter: Optional[str] = Field(default=None, description="Filter: optimal or needs_attention")
    priority_urls: Optional[List[str]] = Field(default=None, description="Priority URLs to crawl")


class AsIsRefreshRequest(BaseModel):
    """Request to refresh AS-IS data"""
    user_id: str = Field(..., description="User ID")
    site_url: str = Field(..., description="User's website URL")
    priority_urls: Optional[List[str]] = Field(default=None, description="Priority URLs")
    tracked_keywords: Optional[List[str]] = Field(default=None, description="Tracked keywords")
    competitors: Optional[List[str]] = Field(default=None, description="Competitors")


class AsIsCompetitorsRequest(BaseModel):
    """Request for AS-IS competitor data"""
    user_id: str = Field(..., description="User ID")
    site_url: str = Field(..., description="User's website URL")
    competitors: List[str] = Field(..., description="Competitor domains")


class TrafficCardData(BaseModel):
    """Organic traffic card data"""
    total_clicks: int = 0
    clicks_change: float = 0
    clicks_change_direction: str = "neutral"
    total_impressions: int = 0
    impressions_change: float = 0
    impressions_change_direction: str = "neutral"
    avg_ctr: float = 0
    data_available: bool = False


class KeywordsCardData(BaseModel):
    """Keywords performance card data"""
    avg_position: float = 0
    position_change: float = 0
    position_change_direction: str = "neutral"
    top10_keywords: int = 0
    top10_change: int = 0
    total_keywords: int = 0
    tracked_keywords_count: int = 0
    ranked_keywords: List[Dict[str, Any]] = []
    data_available: bool = False


class SERPCardData(BaseModel):
    """SERP features card data"""
    features_count: int = 0
    features_present: List[str] = []
    domain_in_features: int = 0
    data_available: bool = False
    message: Optional[str] = None


class CompetitorRankCardData(BaseModel):
    """Competitor rank card data"""
    your_rank: Optional[int] = None
    total_competitors: int = 0
    your_visibility_score: float = 0
    empty_state: bool = False
    message: Optional[str] = None


class AsIsSummaryResponse(BaseModel):
    """Response for AS-IS summary"""
    status: str
    message: str
    user_id: str
    data: Dict[str, Any]


class ParameterItem(BaseModel):
    """Single parameter item"""
    group_id: str
    name: str
    score: float
    status: str
    tab: str
    details: Optional[Dict[str, Any]] = None


class AsIsParametersResponse(BaseModel):
    """Response for AS-IS parameters"""
    status: str
    message: str
    user_id: str
    data: Dict[str, Any]


class AsIsCompetitorsResponse(BaseModel):
    """Response for AS-IS competitors"""
    status: str
    message: str
    user_id: str
    data: Dict[str, Any]


class AsIsRefreshResponse(BaseModel):
    """Response for AS-IS refresh"""
    status: str
    message: str
    user_id: str
    data: Dict[str, Any]


# ==================== ACTION PLAN Models ====================

class ActionPlanGenerateRequest(BaseModel):
    """Request to generate action plan"""
    user_id: str = Field(..., description="User ID")


class ActionPlanTasksRequest(BaseModel):
    """Request to get action plan tasks with filters"""
    user_id: str = Field(..., description="User ID")
    category: Optional[str] = Field(default=None, description="Filter by category: 'onpage', 'offpage', 'technical'")
    priority: Optional[str] = Field(default=None, description="Filter by priority: 'high', 'medium', 'low'")
    status: Optional[str] = Field(default=None, description="Filter by status: 'not_started', 'in_progress', 'completed'")


class ActionPlanUpdateStatusRequest(BaseModel):
    """Request to update task status"""
    user_id: str = Field(..., description="User ID")
    new_status: str = Field(..., description="New status: 'not_started', 'in_progress', or 'completed'")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes for status change")
