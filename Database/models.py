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


class StrategyGoal(Base):
    """Strategy goals tracking with 90-day cycles"""
    __tablename__ = "strategy_goals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Goal Identification
    goal_type = Column(String(50), nullable=False)  # 'organic-traffic', 'keyword-rankings', etc.
    goal_category = Column(String(20), nullable=False)  # 'priority' or 'additional'
    
    # Cycle Management
    cycle_start_date = Column(Date, nullable=False)
    cycle_end_date = Column(Date, nullable=False)  # 90 days from start
    is_locked = Column(Boolean, default=True)
    
    # Status (for governance tracking)
    status = Column(String(20), default='on_track')  # 'on_track', 'paused', 'completed', 'at_risk'
    
    # Metrics
    baseline_value = Column(String(100), nullable=True)  # Current value at cycle start
    current_value = Column(String(100), nullable=True)   # Updated monthly
    target_value = Column(String(100), nullable=False)  # Target for this cycle
    
    # Metadata
    unit = Column(String(50), nullable=False)  # 'visitors/month', 'DA points', etc.
    target_type = Column(String(20), nullable=False)  # 'growth', 'range', 'slabs', 'paused'
    
    # For keyword-rankings goal (slab distribution)
    from sqlalchemy.dialects.postgresql import JSONB
    slab_data = Column(JSONB, nullable=True)
    
    # Progress Tracking
    progress_percentage = Column(Float, default=0.0)
    last_calculated_at = Column(TIMESTAMP, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'goal_type', 'cycle_start_date', name='uix_user_goal_cycle'),
        CheckConstraint("goal_type IN ('organic-traffic', 'keyword-rankings', 'serp-features', 'avg-position', 'impressions', 'domain-authority')", name='chk_goal_type'),
        CheckConstraint("goal_category IN ('priority', 'additional')", name='chk_goal_category'),
        CheckConstraint("target_type IN ('growth', 'range', 'slabs', 'paused')", name='chk_target_type'),
        CheckConstraint("status IN ('on_track', 'paused', 'completed', 'at_risk')", name='chk_goal_status'),
    )


class GoalMilestone(Base):
    """Monthly milestones for goal tracking"""
    __tablename__ = "goal_milestones"
    
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("strategy_goals.id", ondelete="CASCADE"), nullable=False)
    
    month_number = Column(Integer, nullable=False)  # 1, 2, or 3
    target_value = Column(String(100), nullable=False)
    actual_value = Column(String(100), nullable=True)
    achieved = Column(Boolean, default=False)
    recorded_at = Column(TIMESTAMP, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('goal_id', 'month_number', name='uix_goal_milestone'),
        CheckConstraint("month_number IN (1, 2, 3)", name='chk_month_number'),
    )


class GoalProgressSnapshot(Base):
    """Daily/weekly snapshots for goal trend tracking"""
    __tablename__ = "goal_progress_snapshots"
    
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("strategy_goals.id", ondelete="CASCADE"), nullable=False)
    
    snapshot_date = Column(Date, nullable=False)
    current_value = Column(String(100), nullable=False)
    progress_percentage = Column(Float, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('goal_id', 'snapshot_date', name='uix_goal_snapshot'),
    )




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
    baseline_score = Column(Float, nullable=True)  # Initial baseline score
    is_baseline = Column(Boolean, default=False)   # Flag for baseline snapshots
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
    
    # Baseline Metrics
    baseline_total_clicks = Column(Integer, nullable=True)
    baseline_total_impressions = Column(Integer, nullable=True)
    baseline_avg_position = Column(Float, nullable=True)
    baseline_top10_keywords = Column(Integer, nullable=True)
    baseline_features_count = Column(Integer, nullable=True)
    baseline_your_rank = Column(Integer, nullable=True)
    baseline_visibility_score = Column(Float, nullable=True)
    baseline_captured_at = Column(TIMESTAMP, nullable=True)
    
    # JSONB columns for complete data storage
    from sqlalchemy.dialects.postgresql import JSONB
    full_summary = Column(JSONB, nullable=True)          # Complete summary as JSONB
    ranked_keywords = Column(JSONB, nullable=True)       # Keyword list with positions
    top_pages = Column(JSONB, nullable=True)             # Top performing pages
    competitor_rankings = Column(JSONB, nullable=True)   # Competitor list with scores
    serp_features_detail = Column(JSONB, nullable=True)  # SERP features detail
    
    # Domain Authority (for Goal Setting)
    domain_authority = Column(Integer, default=0)
    baseline_domain_authority = Column(Integer, nullable=True)
    
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())


class AsIsProgressTimeline(Base):
    """Timeline of performance changes and improvements"""
    __tablename__ = "asis_progress_timeline"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Event Information
    event_type = Column(String(50), nullable=False)  # 'score_improvement', 'metric_change', 'milestone'
    event_title = Column(String(500), nullable=False)
    event_description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(20), nullable=True)  # 'onpage', 'offpage', 'technical', 'overall'
    parameter_group = Column(String(100), nullable=True)
    
    # Metrics
    metric_name = Column(String(100), nullable=True)
    old_value = Column(Float, nullable=True)
    new_value = Column(Float, nullable=True)
    change_delta = Column(Float, nullable=True)
    
    # Timestamp
    event_timestamp = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("event_type IN ('score_improvement', 'score_decline', 'metric_change', 'milestone', 'baseline_captured')", name='chk_event_type'),
    )




# ==================== ACTION PLAN Models ====================

class ActionPlanTask(Base):
    """SEO action plan tasks"""
    __tablename__ = "action_plan_tasks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Task Information
    task_title = Column(String(500), nullable=False)
    task_description = Column(Text, nullable=True)
    category = Column(String(20), nullable=False)  # 'onpage', 'offpage', 'technical'
    
    # Priority & Effort
    priority = Column(String(20), nullable=False)  # 'high', 'medium', 'low'
    impact_score = Column(Float, default=0.0)
    effort_score = Column(Float, default=0.0)
    
    # Status Tracking
    status = Column(String(20), nullable=False, default='not_started')
    
    # Categorization
    parameter_group = Column(String(100), nullable=True)
    sub_parameter = Column(String(100), nullable=True)
    
    # Goal Alignment
    related_goal = Column(String(255), nullable=True)
    
    # Metrics
    affected_pages_count = Column(Integer, default=0)
    
    # Metadata
    impact_description = Column(Text, nullable=True)
    effort_description = Column(String(50), nullable=True)  # 'Low', 'Medium', 'High'
    recommendation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
    
    __table_args__ = (
        CheckConstraint("category IN ('onpage', 'offpage', 'technical')", name='chk_category'),
        CheckConstraint("priority IN ('high', 'medium', 'low')", name='chk_priority'),
        CheckConstraint("status IN ('not_started', 'in_progress', 'completed')", name='chk_status'),
        CheckConstraint("effort_description IN ('Low', 'Medium', 'High')", name='chk_effort'),
    )


class ActionPlanTaskPage(Base):
    """Junction table for task-page relationships"""
    __tablename__ = "action_plan_task_pages"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("action_plan_tasks.id", ondelete="CASCADE"), nullable=False)
    page_url = Column(String(500), nullable=False)
    
    # Issue Details
    issue_description = Column(Text, nullable=True)
    current_value = Column(Text, nullable=True)
    recommended_value = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())


class ActionPlanTaskHistory(Base):
    """Audit trail for task status changes"""
    __tablename__ = "action_plan_task_history"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("action_plan_tasks.id", ondelete="CASCADE"), nullable=False)
    
    # Status Change
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamp
    changed_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("old_status IN ('not_started', 'in_progress', 'completed')", name='chk_old_status'),
        CheckConstraint("new_status IN ('not_started', 'in_progress', 'completed')", name='chk_new_status'),
    )


class ActionPlanProgressSnapshot(Base):
    """Historical tracking for action plan governance"""
    __tablename__ = "action_plan_progress_snapshots"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot Date
    snapshot_date = Column(Date, nullable=False)
    cycle_start_date = Column(Date, nullable=False)  # Links to 90-day cycle
    
    # Overall Metrics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    in_progress_tasks = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    
    # Category Breakdown - On-Page
    onpage_total = Column(Integer, default=0)
    onpage_completed = Column(Integer, default=0)
    onpage_percentage = Column(Float, default=0.0)
    
    # Category Breakdown - Off-Page
    offpage_total = Column(Integer, default=0)
    offpage_completed = Column(Integer, default=0)
    offpage_percentage = Column(Float, default=0.0)
    
    # Category Breakdown - Technical
    technical_total = Column(Integer, default=0)
    technical_completed = Column(Integer, default=0)
    technical_percentage = Column(Float, default=0.0)
    
    # Baseline Flag
    is_baseline = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'snapshot_date', name='uix_user_snapshot_date'),
    )
