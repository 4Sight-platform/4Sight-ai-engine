from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, CheckConstraint, ARRAY, Date, DECIMAL, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)  # Email-based UUID
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    
    password_hash = Column(String(255), nullable=True)
    google_user_id = Column(String(255), unique=True, nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    account_type = Column(String(50), default='standard')
    
    onboarding_completed = Column(Boolean, default=False)
    current_onboarding_page = Column(Integer, default=1)
    credentials_sent = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP, nullable=True)

class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=False)
    business_description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class Products(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Services(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(255), nullable=False)
    service_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    encrypted_refresh_token = Column(Text, nullable=False)
    provider = Column(String(50), default='google')
    scopes = Column(ARRAY(Text), nullable=True)
    token_created_at = Column(TIMESTAMP, server_default=func.now())
    token_expires_at = Column(TIMESTAMP, nullable=True)
    last_refreshed_at = Column(TIMESTAMP, nullable=True)

class Integrations(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # GSC
    gsc_connected = Column(Boolean, default=False)
    gsc_verified_site = Column(String(500), nullable=True)
    gsc_last_validated = Column(TIMESTAMP, nullable=True)
    
    # GA4
    ga4_connected = Column(Boolean, default=False)
    ga4_property_id = Column(String(100), nullable=True)
    ga4_property_name = Column(String(255), nullable=True)
    ga4_stream_url = Column(String(500), nullable=True)
    ga4_last_validated = Column(TIMESTAMP, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class Differentiators(Base):
    __tablename__ = "differentiators"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    differentiator = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class AudienceProfile(Base):
    __tablename__ = "audience_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    location_scope = Column(String(100), nullable=False)
    selected_locations = Column(ARRAY(Text), nullable=True)
    customer_description = Column(Text, nullable=False)
    search_intent = Column(ARRAY(Text), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class SeoGoal(Base):
    __tablename__ = "seo_goals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    goals = Column(ARRAY(Text), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class OnboardingKeyword(Base):
    __tablename__ = "onboarding_keywords"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    is_selected = Column(Boolean, default=False)
    score = Column(DECIMAL(5,2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class OnboardingCompetitor(Base):
    __tablename__ = "onboarding_competitors"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competitor_url = Column(String(500), nullable=False)
    competitor_name = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False)
    is_selected = Column(Boolean, default=False)
    keywords_matched = Column(ARRAY(Text), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class PageUrl(Base):
    __tablename__ = "page_urls"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    home_url = Column(String(500), nullable=False)
    product_url = Column(String(500), nullable=False)
    contact_url = Column(String(500), nullable=False)
    about_url = Column(String(500), nullable=False)
    blog_url = Column(String(500), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class ReportingPreference(Base):
    __tablename__ = "reporting_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    reporting_channels = Column(ARRAY(Text), nullable=False)
    report_frequency = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class KeywordUniverse(Base):
    __tablename__ = "keyword_universes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    is_locked = Column(Boolean, default=False)
    locked_until = Column(Date, nullable=True)
    selection_count = Column(Integer, default=0)
    
    gsc_excluded_keywords = Column(ARRAY(String), nullable=True)
    gsc_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class KeywordUniverseItem(Base):
    __tablename__ = "keyword_universe_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    keyword = Column(String, nullable=False)
    search_volume = Column(Integer, default=0)
    difficulty = Column(String, nullable=False)
    intent = Column(String, nullable=False)
    keyword_type = Column(String, nullable=False)
    
    source = Column(String, default='generated')
    score = Column(Float, nullable=True)
    is_selected = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'keyword', name='uix_user_keyword'),)
