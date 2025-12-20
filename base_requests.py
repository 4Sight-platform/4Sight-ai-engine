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
    business_name: str = Field(..., min_length=2, max_length=100, description="Business name")
    website_url: HttpUrl = Field(..., description="Website URL")
    business_description: str = Field(..., max_length=500, description="Business description")
    user_id: Optional[str] = Field(None, description="User ID if updating existing profile")
    
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


class Page4PortfolioRequest(BaseModel):
    """Page 4: Business Portfolio"""
    user_id: str = Field(..., description="User ID")
    products: List[str] = Field(default_factory=list, max_length=10, description="Products")
    services: List[str] = Field(default_factory=list, max_length=10, description="Services")
    differentiators: List[str] = Field(default_factory=list, max_length=5, description="Differentiators")


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

