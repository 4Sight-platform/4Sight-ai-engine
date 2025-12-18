"""
Complete Data Models
Based on OnboardingData TypeScript interface
"""

from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional, List
from enum import Enum

class LocationScope(str, Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    NATIONWIDE = "nationwide"
    INTERNATIONAL = "international"

class SearchIntent(str, Enum):
    INFORMATION = "information"
    COMPARISON = "comparison"
    DEAL = "deal"
    ACTION = "action-focused"

class SEOGoal(str, Enum):
    ORGANIC_TRAFFIC = "organic_traffic_growth"
    SEARCH_VISIBILITY = "search_visibility"
    LOCAL_VISIBILITY = "local_visibility"
    TOP_RANKINGS = "top_rankings"

class VoiceTone(str, Enum):
    AUTHORITATIVE = "authoritative_expert"
    CONVERSATIONAL = "conversational_casual"
    INSPIRATIONAL = "inspirational_motivating"
    EDUCATIONAL = "educational_informative"

class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Competitor(BaseModel):
    name: str
    url: HttpUrl

class BlogAuthor(BaseModel):
    name: str
    profile_url: Optional[HttpUrl] = None

class TopicAuthor(BaseModel):
    topic: str
    author_name: str

class OnboardingData(BaseModel):
    # Page 1: Business Info
    business_name: str
    website_url: HttpUrl
    business_description: str
    
    # Page 2: GSC Integration
    gsc_connected: bool = False
    gsc_validation_status: str = "pending"
    gsc_site_url: Optional[str] = None
    
    # Page 3: Audience
    location_scope: LocationScope
    selected_locations: List[str]
    customer_description: str
    search_intent: List[SearchIntent]
    
    # Page 4: Portfolio
    products: List[str] = []
    services: List[str] = []
    differentiators: List[str] = []
    
    # Page 5: SEO Goals
    seo_goals: List[SEOGoal]
    
    # Page 6: Keywords
    keywords_generated: List[str] = []  # LLM suggestions
    keywords_selected: List[str] = []   # User selections
    custom_keywords: List[str] = []     # User additions
    competitors: List[Competitor] = []
    
    # Page 7: Content Filter
    home_page_url: Optional[HttpUrl] = None
    product_page_url: Optional[HttpUrl] = None
    contact_page_url: Optional[HttpUrl] = None
    about_page_url: Optional[HttpUrl] = None
    blog_page_url: Optional[HttpUrl] = None
    
    # Visual elements (API only, text descriptions for terminal)
    primary_color: Optional[str] = "#14B8A6"
    secondary_color: Optional[str] = "#0D9488"
    primary_font: Optional[str] = None
    secondary_font: Optional[str] = None
    voice_tone: Optional[VoiceTone] = None
    content_graphic_style: Optional[str] = None
    logo_url: Optional[str] = None
    typography: Optional[str] = None
    
    blog_authors: List[BlogAuthor] = []
    topic_authors: Optional[List[TopicAuthor]] = []
    
    # Page 8: Reporting
    reporting_channels: List[str] = []
    emails: List[EmailStr] = []
    phones: List[str] = []
    report_frequency: ReportFrequency
    
    # Metadata
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
