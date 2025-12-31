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


# ==================== AS-IS State Models ====================

class GSCDailyMetrics(Base):
    """GSC data snapshots - query and page level metrics"""
    __tablename__ = "gsc_daily_metrics"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)  # 'current' or 'previous'
    metric_type = Column(String(20), nullable=False)  # 'query' or 'page'
    query_or_page = Column(Text, nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    position = Column(Float, default=0.0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'snapshot_date', 'period_type', 'metric_type', 'query_or_page', 
                        name='uix_gsc_metrics'),
    )


class TrackedKeyword(Base):
    """User's tracked keywords for AS-IS monitoring"""
    __tablename__ = "tracked_keywords"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    is_tracked = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'keyword', name='uix_tracked_keyword'),
    )


class KeywordPositionSnapshot(Base):
    """Keyword position history for tracking changes"""
    __tablename__ = "keyword_position_snapshots"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)
    position = Column(Float, nullable=True)
    position_change = Column(Float, nullable=True)
    in_top10 = Column(Boolean, default=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())


class SERPFeaturePresence(Base):
    """SERP features detected for keywords"""
    __tablename__ = "serp_feature_presence"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    feature_type = Column(String(50), nullable=False)
    domain_present = Column(Boolean, default=False)
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class CompetitorVisibilityScore(Base):
    """Competitor SEO visibility scores"""
    __tablename__ = "competitor_visibility_scores"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competitor_domain = Column(String(255), nullable=False)
    visibility_score = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    score_factors = Column(Text, nullable=True)  # JSON stored as text
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class CrawlPage(Base):
    """Crawled page metadata"""
    __tablename__ = "crawl_pages"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    page_url = Column(String(500), nullable=False)
    last_crawled = Column(TIMESTAMP, nullable=True)
    crawl_status = Column(String(50), default='pending')
    http_status = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'page_url', name='uix_crawl_page'),
    )


class OnPageSignal(Base):
    """On-page SEO signals extracted from crawled pages"""
    __tablename__ = "onpage_signals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    page_url = Column(String(500), nullable=False)
    title_tag = Column(Text, nullable=True)
    title_length = Column(Integer, default=0)
    meta_description = Column(Text, nullable=True)
    meta_description_length = Column(Integer, default=0)
    h1_count = Column(Integer, default=0)
    h1_text = Column(Text, nullable=True)
    h2_count = Column(Integer, default=0)
    h3_count = Column(Integer, default=0)
    h4_count = Column(Integer, default=0)
    h5_count = Column(Integer, default=0)
    h6_count = Column(Integer, default=0)
    canonical_url = Column(String(500), nullable=True)
    canonical_self_referencing = Column(Boolean, default=False)
    first_100_words = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    internal_link_count = Column(Integer, default=0)
    external_link_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    images_with_alt = Column(Integer, default=0)
    images_without_alt = Column(Integer, default=0)
    url_length = Column(Integer, default=0)
    url_has_parameters = Column(Boolean, default=False)
    url_depth = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'page_url', name='uix_onpage_signal'),
    )


class BacklinkSignal(Base):
    """Backlink data from GSC and analysis"""
    __tablename__ = "backlink_signals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    referring_domains = Column(Integer, default=0)
    total_backlinks = Column(Integer, default=0)
    dofollow_ratio = Column(Float, default=0.0)
    anchor_text_distribution = Column(Text, nullable=True)  # JSON as text
    top_linking_sites = Column(Text, nullable=True)  # JSON as text
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class TechnicalSignal(Base):
    """Technical SEO signals"""
    __tablename__ = "technical_signals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    indexed_pages = Column(Integer, default=0)
    submitted_pages = Column(Integer, default=0)
    index_coverage_ratio = Column(Float, default=0.0)
    robots_txt_exists = Column(Boolean, default=False)
    robots_txt_valid = Column(Boolean, default=False)
    sitemap_exists = Column(Boolean, default=False)
    sitemap_valid = Column(Boolean, default=False)
    canonical_issues_count = Column(Integer, default=0)
    duplicate_title_count = Column(Integer, default=0)
    duplicate_description_count = Column(Integer, default=0)
    https_enabled = Column(Boolean, default=False)
    mixed_content_issues = Column(Integer, default=0)
    trailing_slash_consistent = Column(Boolean, default=True)
    www_consistent = Column(Boolean, default=True)
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class CWVSignal(Base):
    """Core Web Vitals signals from GSC"""
    __tablename__ = "cwv_signals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url_group = Column(String(500), default='site-wide')
    device_type = Column(String(20), default='mobile')
    lcp_score = Column(Float, nullable=True)
    lcp_status = Column(String(20), nullable=True)
    inp_score = Column(Float, nullable=True)
    inp_status = Column(String(20), nullable=True)
    cls_score = Column(Float, nullable=True)
    cls_status = Column(String(20), nullable=True)
    overall_status = Column(String(20), nullable=True)
    good_urls_count = Column(Integer, default=0)
    needs_improvement_urls_count = Column(Integer, default=0)
    poor_urls_count = Column(Integer, default=0)
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class AICrawlGovernance(Base):
    """AI/LLM crawl governance settings"""
    __tablename__ = "ai_crawl_governance"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    robots_ai_rules = Column(Text, nullable=True)  # JSON as text
    llm_txt_detected = Column(Boolean, default=False)
    llm_txt_content = Column(Text, nullable=True)
    ai_crawlers_blocked = Column(Text, nullable=True)  # JSON as text
    ai_crawlers_allowed = Column(Text, nullable=True)  # JSON as text
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AsIsScore(Base):
    """Composite scores and status for AS-IS parameters"""
    __tablename__ = "as_is_scores"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parameter_tab = Column(String(20), nullable=False)
    parameter_group = Column(String(100), nullable=False)
    sub_parameter = Column(String(100), nullable=True)
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    status = Column(String(20), nullable=False)
    details = Column(Text, nullable=True)  # JSON as text
    recommendation = Column(Text, nullable=True)
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'parameter_tab', 'parameter_group', 'sub_parameter', 'snapshot_date',
                        name='uix_asis_score'),
    )


class AsIsSummaryCache(Base):
    """Cached summary data for the four top cards"""
    __tablename__ = "as_is_summary_cache"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_clicks = Column(Integer, default=0)
    clicks_change = Column(Float, default=0.0)
    total_impressions = Column(Integer, default=0)
    impressions_change = Column(Float, default=0.0)
    avg_position = Column(Float, default=0.0)
    position_change = Column(Float, default=0.0)
    top10_keywords = Column(Integer, default=0)
    top10_change = Column(Integer, default=0)
    features_present = Column(Text, nullable=True)  # JSON as text
    features_count = Column(Integer, default=0)
    your_rank = Column(Integer, nullable=True)
    total_competitors = Column(Integer, default=0)
    your_visibility_score = Column(Float, default=0.0)
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())

