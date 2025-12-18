#!/usr/bin/env python3
"""
SEO Automation Platform - Project Setup V2
Creates complete folder structure with onboarding-focused design
Supports both Terminal and API modes
"""

import os
import json
from pathlib import Path
from datetime import datetime


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")


def print_info(text):
    print(f"{Colors.OKBLUE}→{Colors.ENDC} {text}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠{Colors.ENDC}  {text}")


def create_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def file_exists(path):
    """Check if file exists"""
    return Path(path).exists()


def create_file(path, content="", skip_if_exists=True):
    """Create file with optional content"""
    if skip_if_exists and file_exists(path):
        return None  # Skip existing
    Path(path).write_text(content)
    return path


def create_init_file(path, skip_if_exists=True):
    """Create __init__.py file"""
    if skip_if_exists and file_exists(path):
        return None
    content = '"""Package initialization"""\n'
    return create_file(path, content, skip_if_exists=False)  # Already checked


def create_placeholder_file(path, description, skip_if_exists=True):
    """Create placeholder Python file with docstring"""
    if skip_if_exists and file_exists(path):
        return None
    content = f'''"""
{description}
TODO: Implement functionality
"""

# Placeholder - to be implemented
pass
'''
    return create_file(path, content, skip_if_exists=False)  # Already checked


class SetupStats:
    """Track setup statistics"""
    def __init__(self):
        self.created = 0
        self.skipped = 0
    
    def add_created(self):
        self.created += 1
    
    def add_skipped(self):
        self.skipped += 1
    
    def report(self, section_name):
        if self.created > 0 or self.skipped > 0:
            print_success(f"{section_name}: {self.created} created, {self.skipped} skipped")
        return self.created, self.skipped


def setup_config_files(base_path):
    """Create configuration files"""
    print_info("Setting up configuration files...")
    
    config_dir = create_directory(f"{base_path}/config")
    
    created = 0
    skipped = 0
    
    # credentials.json
    creds_path = f"{config_dir}/credentials.json"
    if file_exists(creds_path):
        print_info(f"Skipped: config/credentials.json (already exists)")
        skipped += 1
    else:
        credentials = {
            "gsc": {
                "client_id": "YOUR_GSC_CLIENT_ID",
                "client_secret": "YOUR_GSC_CLIENT_SECRET",
                "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                "oauth_scope": "https://www.googleapis.com/auth/webmasters"
            },
            "keyword_planner": {
                "developer_token": "YOUR_DEVELOPER_TOKEN",
                "client_id": "YOUR_KP_CLIENT_ID",
                "client_secret": "YOUR_KP_CLIENT_SECRET",
                "refresh_token": "YOUR_KP_REFRESH_TOKEN",
                "customer_id": "YOUR_CUSTOMER_ID"
            },
            "custom_search": {
                "api_key": "YOUR_CUSTOM_SEARCH_API_KEY",
                "cx": "YOUR_SEARCH_ENGINE_ID"
            },
            "anthropic": {
                "api_key": "YOUR_ANTHROPIC_API_KEY"
            }
        }
        create_file(creds_path, json.dumps(credentials, indent=2), skip_if_exists=False)
        print_success(f"Created: config/credentials.json")
        created += 1
    
    # llm_config.json
    llm_path = f"{config_dir}/llm_config.json"
    if file_exists(llm_path):
        print_info(f"Skipped: config/llm_config.json (already exists)")
        skipped += 1
    else:
        llm_config = {
            "model": "gemini-2.5-flash",
            "temperature": 0.3,
            "max_tokens": 2000,
            "keyword_generation": {
                "system_prompt": "You are an SEO expert specializing in keyword research and search intent analysis.",
                "max_keywords": 30,
                "min_keywords": 20
            }
        }
        create_file(llm_path, json.dumps(llm_config, indent=2), skip_if_exists=False)
        print_success(f"Created: config/llm_config.json")
        created += 1
    
    # app_config.json
    app_path = f"{config_dir}/app_config.json"
    if file_exists(app_path):
        print_info(f"Skipped: config/app_config.json (already exists)")
        skipped += 1
    else:
        app_config = {
            "mode": "cli",
            "default_date_range_days": 90,
            "max_keywords_per_batch": 25,
            "enable_logging": True,
            "log_level": "INFO",
            "onboarding": {
                "max_products": 10,
                "max_services": 10,
                "max_differentiators": 5,
                "max_competitors": 10,
                "required_pages": ["home", "product", "contact", "about", "blog"]
            }
        }
        create_file(app_path, json.dumps(app_config, indent=2), skip_if_exists=False)
        print_success(f"Created: config/app_config.json")
        created += 1
    
    if created > 0:
        print_success(f"Config: {created} created, {skipped} skipped")


def setup_phases(base_path):
    """Create phase directories and placeholder files"""
    print_info("Setting up phase modules...")
    
    phases_dir = create_directory(f"{base_path}/phases")
    if not file_exists(f"{phases_dir}/__init__.py"):
        create_init_file(f"{phases_dir}/__init__.py", skip_if_exists=False)
        print_success("Created: phases/__init__.py")
    
    created = 0
    skipped = 0
    
    # Phase 0: Keyword Generation (NEW - V2 only)
    phase0 = f"{phases_dir}/phase0_keyword_generation"
    if file_exists(phase0):
        print_info(f"Skipped: phase0_keyword_generation/ (already exists)")
        skipped += 1
    else:
        create_directory(phase0)
        create_init_file(f"{phase0}/__init__.py", skip_if_exists=False)
        create_placeholder_file(f"{phase0}/keyword_suggester.py", "Generate keyword suggestions using LLM", skip_if_exists=False)
        create_placeholder_file(f"{phase0}/prompt_templates.py", "LLM prompt templates for keyword generation", skip_if_exists=False)
        create_placeholder_file(f"{phase0}/keyword_analyzer.py", "Analyze and rank keyword suggestions", skip_if_exists=False)
        print_success("Created: phases/phase0_keyword_generation/ ⭐ NEW")
        created += 1
    
    # Phase 1: Tuning (check if exists, only create if missing)
    phase1 = f"{phases_dir}/phase1_tuning"
    if file_exists(phase1):
        print_info(f"Skipped: phase1_tuning/ (already exists)")
        skipped += 1
    else:
        create_directory(phase1)
        create_init_file(f"{phase1}/__init__.py", skip_if_exists=False)
        create_placeholder_file(f"{phase1}/keyword_refiner.py", "Refine selected keywords from onboarding", skip_if_exists=False)
        create_placeholder_file(f"{phase1}/tuning_loop.py", "User interaction for keyword refinement", skip_if_exists=False)
        print_success("Created: phases/phase1_tuning/")
        created += 1
    
    # Phase 2: Market Analysis
    phase2 = f"{phases_dir}/phase2_market"
    if file_exists(phase2):
        print_info(f"Skipped: phase2_market/ (already exists)")
        skipped += 1
    else:
        create_directory(phase2)
        create_init_file(f"{phase2}/__init__.py", skip_if_exists=False)
        create_placeholder_file(f"{phase2}/keyword_planner_client.py", "Google Keyword Planner API wrapper", skip_if_exists=False)
        create_placeholder_file(f"{phase2}/market_analyzer.py", "Process volume, CPC, competition data", skip_if_exists=False)
        print_success("Created: phases/phase2_market/")
        created += 1
    
    # Phase 3: GSC (placeholder - will be migrated, so always skip if exists)
    phase3 = f"{phases_dir}/phase3_gsc"
    if file_exists(phase3):
        print_info(f"Skipped: phase3_gsc/ (already exists - will be migrated)")
        skipped += 1
    else:
        create_directory(phase3)
        create_init_file(f"{phase3}/__init__.py", skip_if_exists=False)
        readme = """# Phase 3: GSC Integration

This directory will contain your GSC_automation files.

Run `python migrate_gsc.py` to move your existing GSC files here.

Expected files after migration:
- auth.py (OAuth 2.0 authentication)
- client.py (GSC API wrapper)
- storage.py (Token persistence)
- utils.py (Terminal utilities)
- fetch_data.py (Complete data dump)
- query_data.py (Query saved data)
"""
        create_file(f"{phase3}/README.md", readme, skip_if_exists=False)
        print_success("Created: phases/phase3_gsc/ (placeholder)")
        created += 1
    
    # Phase 4: Gap Analysis
    phase4 = f"{phases_dir}/phase4_gap_analysis"
    if file_exists(phase4):
        print_info(f"Skipped: phase4_gap_analysis/ (already exists)")
        skipped += 1
    else:
        create_directory(phase4)
        create_init_file(f"{phase4}/__init__.py", skip_if_exists=False)
        create_placeholder_file(f"{phase4}/classifier.py", "Keyword classification logic", skip_if_exists=False)
        create_placeholder_file(f"{phase4}/strategy_mapper.py", "Map keywords to strategy buckets", skip_if_exists=False)
        create_placeholder_file(f"{phase4}/rules_engine.py", "Business rules (High Vol + No Rank = Gold)", skip_if_exists=False)
        print_success("Created: phases/phase4_gap_analysis/")
        created += 1
    
    # Phase 5: Competitors
    phase5 = f"{phases_dir}/phase5_competitors"
    if file_exists(phase5):
        print_info(f"Skipped: phase5_competitors/ (already exists)")
        skipped += 1
    else:
        create_directory(phase5)
        create_init_file(f"{phase5}/__init__.py", skip_if_exists=False)
        create_placeholder_file(f"{phase5}/custom_search_client.py", "Google Custom Search API wrapper", skip_if_exists=False)
        create_placeholder_file(f"{phase5}/scraper.py", "Extract titles, descriptions, insights", skip_if_exists=False)
        create_placeholder_file(f"{phase5}/competitor_analyzer.py", "Analyze why competitors rank", skip_if_exists=False)
        print_success("Created: phases/phase5_competitors/")
        created += 1
    
    print_success(f"Phases: {created} created, {skipped} skipped")


def setup_cli_onboarding(base_path):
    """Create CLI onboarding structure"""
    print_info("Setting up CLI onboarding modules...")
    
    cli_dir = create_directory(f"{base_path}/cli")
    onboarding_dir = f"{cli_dir}/onboarding"
    
    stats = SetupStats()
    
    # Check if onboarding already exists
    if file_exists(onboarding_dir):
        print_info(f"Skipped: cli/onboarding/ (already exists)")
        stats.add_skipped()
        stats.report("CLI onboarding")
        return
    
    # Create onboarding directory
    create_directory(onboarding_dir)
    
    if not file_exists(f"{cli_dir}/__init__.py"):
        create_init_file(f"{cli_dir}/__init__.py", skip_if_exists=False)
    create_init_file(f"{onboarding_dir}/__init__.py", skip_if_exists=False)
    
    # Individual onboarding pages
    pages = [
        ("page1_business.py", "Page 1: Business Info (name, URL, description)"),
        ("page2_gsc.py", "Page 2: GSC OAuth Connection"),
        ("page3_audience.py", "Page 3: Audience & Search Intent (location, customer, intent)"),
        ("page4_portfolio.py", "Page 4: Business Portfolio (products, services, differentiators)"),
        ("page5_goals.py", "Page 5: SEO Goals (traffic, visibility, rankings)"),
        ("page6_keywords.py", "Page 6: Keyword Selection (LLM suggestions + custom)"),
        ("page7_content.py", "Page 7: Content Filter (text-based for terminal)"),
        ("page8_reporting.py", "Page 8: Reporting & Notifications"),
    ]
    
    for filename, description in pages:
        create_placeholder_file(f"{onboarding_dir}/{filename}", description, skip_if_exists=False)
    
    # Orchestrator
    orchestrator_content = '''"""
CLI Onboarding Orchestrator
Navigates between onboarding pages
"""

class OnboardingOrchestrator:
    """Manages onboarding flow"""
    
    def __init__(self):
        self.pages = [
            "page1_business",
            "page2_gsc",
            "page3_audience",
            "page4_portfolio",
            "page5_goals",
            "page6_keywords",
            "page7_content",
            "page8_reporting"
        ]
        self.current_page = 0
        self.data = {}
    
    def run(self):
        """Run complete onboarding flow"""
        print("Starting onboarding...")
        # TODO: Implement page navigation
        pass
'''
    create_file(f"{onboarding_dir}/orchestrator.py", orchestrator_content, skip_if_exists=False)
    
    # Main CLI entry point (only if doesn't exist)
    cli_main = f"{cli_dir}/main.py"
    if not file_exists(cli_main):
        main_cli = '''"""
CLI Main Entry Point
Handles terminal-based interaction
"""

from cli.onboarding.orchestrator import OnboardingOrchestrator

def run_cli():
    """Run CLI mode"""
    print("\\n" + "="*60)
    print("  SEO Automation Platform - CLI Mode")
    print("="*60 + "\\n")
    
    # Check if user has completed onboarding
    # TODO: Load user profile
    
    print("Options:")
    print("  1) Complete onboarding (first time)")
    print("  2) Run complete workflow (all 5 phases)")
    print("  3) Run individual phase")
    print("  4) View saved reports")
    print("  5) Settings")
    print("  6) Exit")
    
    choice = input("\\n→ Select option (1-6): ").strip()
    
    if choice == "1":
        orchestrator = OnboardingOrchestrator()
        orchestrator.run()
    elif choice == "2":
        print("\\n✓ Running complete workflow...")
        # TODO: Call orchestration.workflow.run()
    else:
        print("\\n✓ Exiting...")


if __name__ == "__main__":
    run_cli()
'''
        create_file(cli_main, main_cli, skip_if_exists=False)
    
    print_success("Created: cli/onboarding/ (8 pages + orchestrator) ⭐ NEW")
    stats.add_created()
    stats.report("CLI onboarding")


def setup_api_onboarding(base_path):
    """Create API onboarding structure"""
    print_info("Setting up API onboarding modules...")
    
    api_dir = create_directory(f"{base_path}/api")
    onboarding_dir = f"{api_dir}/onboarding"
    routes_dir = f"{api_dir}/routes"
    
    stats = SetupStats()
    
    # Check if already exists
    if file_exists(onboarding_dir):
        print_info(f"Skipped: api/onboarding/ (already exists)")
        stats.add_skipped()
        stats.report("API onboarding")
        return
    
    create_directory(onboarding_dir)
    create_directory(routes_dir)
    
    if not file_exists(f"{api_dir}/__init__.py"):
        create_init_file(f"{api_dir}/__init__.py", skip_if_exists=False)
    create_init_file(f"{onboarding_dir}/__init__.py", skip_if_exists=False)
    create_init_file(f"{routes_dir}/__init__.py", skip_if_exists=False)
    
    # Onboarding handlers
    handlers_content = '''"""
API Onboarding Handlers
Full-featured web onboarding with file uploads, color pickers, etc.
"""

from fastapi import UploadFile, File

async def handle_logo_upload(file: UploadFile = File(...)):
    """Handle brand logo upload"""
    # TODO: Implement logo upload
    pass

async def generate_keyword_suggestions(profile_data: dict):
    """Generate keyword suggestions from profile"""
    # TODO: Call phase0_keyword_generation
    pass
'''
    create_file(f"{onboarding_dir}/handlers.py", handlers_content, skip_if_exists=False)
    
    # Onboarding routes
    routes_content = '''"""
API Onboarding Routes
POST /onboarding/* endpoints
"""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class BusinessInfo(BaseModel):
    business_name: str
    website_url: str
    business_description: str

@router.post("/business-info")
async def save_business_info(data: BusinessInfo):
    """Save Page 1: Business Info"""
    # TODO: Implement
    return {"status": "success"}

@router.post("/gsc-connect")
async def connect_gsc():
    """Initiate GSC OAuth flow"""
    # TODO: Implement
    return {"auth_url": "https://..."}

@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload brand logo"""
    # TODO: Implement
    return {"logo_url": "/uploads/logo.png"}

# TODO: Add remaining onboarding endpoints
'''
    create_file(f"{routes_dir}/onboarding_routes.py", routes_content, skip_if_exists=False)
    
    # Keyword routes
    keyword_routes = '''"""
Keyword API Routes
"""

from fastapi import APIRouter

router = APIRouter(prefix="/keywords", tags=["keywords"])

@router.get("/suggestions")
async def get_keyword_suggestions(user_id: str):
    """Get LLM-generated keyword suggestions"""
    # TODO: Implement
    return {"keywords": []}

@router.post("/select")
async def select_keywords(user_id: str, keywords: list[str]):
    """Save user's selected keywords"""
    # TODO: Implement
    return {"status": "success"}
'''
    create_file(f"{routes_dir}/keyword_routes.py", keyword_routes, skip_if_exists=False)
    
    # Profile routes
    profile_routes = '''"""
User Profile API Routes
"""

from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    # TODO: Implement
    return {}

@router.put("/{user_id}")
async def update_profile(user_id: str, data: dict):
    """Update user profile"""
    # TODO: Implement
    return {"status": "success"}
'''
    create_file(f"{routes_dir}/profile_routes.py", profile_routes, skip_if_exists=False)
    
    # Main FastAPI app (only if doesn't exist)
    app_path = f"{api_dir}/app.py"
    if not file_exists(app_path):
        app_content = '''"""
FastAPI Application
REST API endpoints for SEO automation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import onboarding_routes, keyword_routes, profile_routes

app = FastAPI(
    title="SEO Automation API",
    description="Complete SEO automation platform with onboarding",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(onboarding_routes.router)
app.include_router(keyword_routes.router)
app.include_router(profile_routes.router)

@app.get("/")
def root():
    return {
        "message": "SEO Automation API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
'''
        create_file(app_path, app_content, skip_if_exists=False)
    
    print_success("Created: api/onboarding/ + routes/ ⭐ NEW")
    stats.add_created()
    stats.report("API onboarding")


def setup_shared(base_path):
    """Create shared utilities"""
    print_info("Creating shared utilities...")
    
    shared_dir = create_directory(f"{base_path}/shared")
    create_init_file(f"{shared_dir}/__init__.py")
    
    # Data models (complete Pydantic models)
    data_models = '''"""
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
'''
    create_file(f"{shared_dir}/data_models.py", data_models)
    
    # Validators
    create_placeholder_file(f"{shared_dir}/validators.py", "Input validation (email, URL, phone)")
    
    # Profile manager
    create_placeholder_file(f"{shared_dir}/profile_manager.py", "Load/save user profiles")
    
    # Keyword service (shared between terminal and API)
    create_placeholder_file(f"{shared_dir}/keyword_service.py", "Shared keyword generation logic")
    
    # Logger
    create_placeholder_file(f"{shared_dir}/logger.py", "Logging utilities")
    
    # Formatters
    create_placeholder_file(f"{shared_dir}/formatters.py", "Output formatting (tables, reports)")
    
    print_success("Created: shared/ (data models + utilities)")


def setup_storage(base_path):
    """Create storage directories"""
    print_info("Setting up storage structure...")
    
    storage_dir = create_directory(f"{base_path}/storage")
    stats = SetupStats()
    
    # User profiles (NEW in V2)
    profiles_dir = f"{storage_dir}/user_profiles"
    if not file_exists(profiles_dir):
        create_directory(profiles_dir)
        create_file(f"{profiles_dir}/.gitkeep", "", skip_if_exists=False)
        create_file(f"{profiles_dir}/README.md", """# User Profiles

Each user has a directory: `{user_id}/`

Contents:
- `profile.json` - Complete onboarding data
- `keywords_generated.json` - LLM-generated keyword suggestions (30)
- `keywords_selected.json` - User's final keyword selections
- `competitors.json` - Competitor analysis data
""", skip_if_exists=False)
        print_success("Created: storage/user_profiles/ ⭐ NEW")
        stats.add_created()
    else:
        print_info("Skipped: storage/user_profiles/ (already exists)")
        stats.add_skipped()
    
    # Brand assets (NEW in V2)
    assets_dir = f"{storage_dir}/brand_assets"
    if not file_exists(assets_dir):
        create_directory(assets_dir)
        create_file(f"{assets_dir}/.gitkeep", "", skip_if_exists=False)
        create_file(f"{assets_dir}/README.md", """# Brand Assets

Each user has a directory: `{user_id}/`

Contents:
- `logo.png` - Brand logo
- `brand_config.json` - Colors, fonts, visual preferences
""", skip_if_exists=False)
        print_success("Created: storage/brand_assets/ ⭐ NEW")
        stats.add_created()
    else:
        print_info("Skipped: storage/brand_assets/ (already exists)")
        stats.add_skipped()
    
    # Credentials (skip if exists)
    creds_dir = f"{storage_dir}/credentials"
    if not file_exists(creds_dir):
        create_directory(creds_dir)
        create_directory(f"{creds_dir}/gsc_tokens")
        create_directory(f"{creds_dir}/gsc_properties")
        create_directory(f"{creds_dir}/keyword_planner_tokens")
        create_file(f"{creds_dir}/.gitkeep", "", skip_if_exists=False)
        print_success("Created: storage/credentials/")
        stats.add_created()
    else:
        print_info("Skipped: storage/credentials/ (already exists)")
        stats.add_skipped()
    
    # Raw data
    raw_dir = f"{storage_dir}/raw_data"
    if not file_exists(raw_dir):
        create_directory(raw_dir)
        create_directory(f"{raw_dir}/gsc")
        create_directory(f"{raw_dir}/keyword_planner")
        create_directory(f"{raw_dir}/competitors")
        create_file(f"{raw_dir}/.gitkeep", "", skip_if_exists=False)
        print_success("Created: storage/raw_data/")
        stats.add_created()
    else:
        print_info("Skipped: storage/raw_data/ (already exists)")
        stats.add_skipped()
    
    # Processed data (add keyword_analysis if missing)
    proc_dir = f"{storage_dir}/processed_data"
    keyword_analysis_dir = f"{proc_dir}/keyword_analysis"
    if not file_exists(keyword_analysis_dir):
        create_directory(keyword_analysis_dir)
        print_success("Created: storage/processed_data/keyword_analysis/ ⭐ NEW")
        stats.add_created()
    
    if not file_exists(proc_dir):
        create_directory(proc_dir)
        create_directory(f"{proc_dir}/gap_analysis")
        create_directory(f"{proc_dir}/reports")
        create_file(f"{proc_dir}/.gitkeep", "", skip_if_exists=False)
        print_success("Created: storage/processed_data/")
        stats.add_created()
    else:
        print_info("Skipped: storage/processed_data/ (already exists)")
        stats.add_skipped()
    
    # Sessions
    sess_dir = f"{storage_dir}/sessions"
    if not file_exists(sess_dir):
        create_directory(sess_dir)
        create_file(f"{sess_dir}/.gitkeep", "", skip_if_exists=False)
        print_success("Created: storage/sessions/")
        stats.add_created()
    else:
        print_info("Skipped: storage/sessions/ (already exists)")
        stats.add_skipped()
    
    stats.report("Storage")


def setup_orchestration(base_path):
    """Create orchestration layer"""
    print_info("Creating orchestration layer...")
    
    orch_dir = create_directory(f"{base_path}/orchestration")
    create_init_file(f"{orch_dir}/__init__.py")
    create_placeholder_file(f"{orch_dir}/workflow.py", "Main LangChain orchestration")
    create_placeholder_file(f"{orch_dir}/nodes.py", "LangChain node definitions")
    create_placeholder_file(f"{orch_dir}/chains.py", "Custom chains for each phase")
    create_placeholder_file(f"{orch_dir}/state_manager.py", "Track workflow state between phases")
    print_success("Created: orchestration/")


def setup_tests(base_path):
    """Create test structure"""
    print_info("Creating test structure...")
    
    test_dir = create_directory(f"{base_path}/tests")
    create_init_file(f"{test_dir}/__init__.py")
    create_placeholder_file(f"{test_dir}/test_onboarding.py", "Onboarding tests")
    create_placeholder_file(f"{test_dir}/test_phase0.py", "Keyword generation tests")
    create_placeholder_file(f"{test_dir}/test_phase1.py", "Phase 1 tests")
    create_placeholder_file(f"{test_dir}/test_phase2.py", "Phase 2 tests")
    create_placeholder_file(f"{test_dir}/test_phase3_gsc.py", "Phase 3 GSC tests")
    create_placeholder_file(f"{test_dir}/test_phase4.py", "Phase 4 tests")
    create_placeholder_file(f"{test_dir}/test_phase5.py", "Phase 5 tests")
    print_success("Created: tests/")


def create_main_entry_point(base_path):
    """Create main.py entry point"""
    print_info("Creating main entry point...")
    
    main_content = '''#!/usr/bin/env python3
"""
SEO Automation Platform - Main Entry Point V2

Usage:
    Terminal Mode: python main.py
    API Mode:      python main.py --api
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def run_terminal_mode():
    """Run in CLI/terminal mode"""
    from cli.main import run_cli
    run_cli()


def run_api_mode():
    """Run in API mode"""
    import uvicorn
    from api.app import app
    
    print("\\n" + "="*60)
    print("  SEO Automation Platform - API Mode V2")
    print("="*60 + "\\n")
    print("→ Starting API server...")
    print("→ Docs: http://localhost:8000/docs")
    print("="*60 + "\\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    parser = argparse.ArgumentParser(description="SEO Automation Platform V2")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run in API mode (default: terminal mode)"
    )
    
    args = parser.parse_args()
    
    if args.api:
        run_api_mode()
    else:
        run_terminal_mode()


if __name__ == "__main__":
    main()
'''
    create_file(f"{base_path}/main.py", main_content)
    print_success("Created: main.py")


def create_requirements(base_path):
    """Create requirements.txt"""
    print_info("Creating requirements.txt...")
    
    requirements = '''# Core dependencies
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.2.0
oauth2client==4.1.3
httplib2==0.22.0

# LangChain & LLM
langchain==0.1.0
google-generativeai==0.8.3


# Data processing & validation
pandas==2.1.4
pydantic==2.5.3
pydantic[email]==2.5.3

# API (FastAPI)
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6  # For file uploads

# CLI
rich==13.7.0
click==8.1.7

# Utilities
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.2

# Image processing (for logo uploads)
Pillow==10.1.0
'''
    create_file(f"{base_path}/requirements.txt", requirements)
    print_success("Created: requirements.txt")


def create_gitignore(base_path):
    """Create .gitignore"""
    print_info("Creating .gitignore...")
    
    gitignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# Credentials & Tokens
config/credentials.json
storage/credentials/
storage/user_profiles/
storage/brand_assets/
*.json
!config/llm_config.json
!config/app_config.json

# Data files
storage/raw_data/
storage/processed_data/
storage/sessions/
*.csv
*.xlsx

# Uploads
uploads/
*.png
*.jpg
*.jpeg
*.svg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
'''
    create_file(f"{base_path}/.gitignore", gitignore)
    print_success("Created: .gitignore")


def create_readme(base_path):
    """Create README.md"""
    print_info("Creating README.md...")
    
    readme = f'''# SEO Automation Platform V2

Complete 5-phase SEO automation workflow with comprehensive onboarding.

## 🎯 Key Features

- **8-Page Onboarding**: Capture complete business profile
- **Dual Mode**: Terminal (testing) + API (production)
- **LLM Keyword Generation**: AI-powered keyword suggestions
- **Complete Data Model**: Based on full onboarding spec
- **OAuth GSC Integration**: Automated Google Search Console connection

## 📋 Onboarding Pages

1. **Business Info**: Name, URL, description
2. **GSC Connection**: OAuth authentication
3. **Audience & Intent**: Location, customer profile, search intent
4. **Portfolio**: Products, services, differentiators
5. **SEO Goals**: Traffic, visibility, rankings, local
6. **Keywords**: LLM suggestions + custom additions + competitors
7. **Content Filter**: Page URLs + brand preferences (text for terminal, full UI for API)
8. **Reporting**: Channels, emails, frequency

## 📁 Project Structure

```
SEO_Automation_Platform/
├── phases/
│   ├── phase0_keyword_generation/   # NEW - LLM keyword suggester
│   ├── phase1_tuning/               # Keyword refinement
│   ├── phase2_market/               # Keyword Planner
│   ├── phase3_gsc/                  # GSC data fetching
│   ├── phase4_gap_analysis/         # Strategy classification
│   └── phase5_competitors/          # Competitor intel
│
├── cli/
│   └── onboarding/                  # 8 terminal pages
│       ├── page1_business.py
│       ├── page2_gsc.py
│       ├── page3_audience.py
│       ├── page4_portfolio.py
│       ├── page5_goals.py
│       ├── page6_keywords.py
│       ├── page7_content.py
│       ├── page8_reporting.py
│       └── orchestrator.py
│
├── api/
│   ├── onboarding/                  # Full web UI handlers
│   └── routes/                      # REST API endpoints
│
├── shared/
│   ├── data_models.py               # Complete Pydantic models
│   ├── keyword_service.py           # Shared keyword logic
│   └── profile_manager.py           # User profile management
│
└── storage/
    ├── user_profiles/               # Complete user data
    ├── brand_assets/                # Logos, colors, fonts
    └── credentials/                 # API tokens
```

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Edit `config/credentials.json`:
- GSC OAuth credentials
- Google Gemini API key (for LLM keyword generation)
- Google Keyword Planner credentials
- Custom Search API key

### 3. Migrate GSC Module
```bash
python migrate_gsc.py
```

### 4. Run Platform

**Terminal Mode** (for testing):
```bash
python main.py
```

**API Mode** (for production):
```bash
python main.py --api
# Access: http://localhost:8000/docs
```

## 📊 Workflow

```
User runs: python main.py
    ↓
Check for existing profile
    ├─ NO → Start onboarding (8 pages)
    └─ YES → Show main menu
    ↓
Onboarding captures:
    ├─ Business info
    ├─ GSC OAuth connection
    ├─ Audience & intent
    ├─ Products/services
    ├─ SEO goals
    ├─ Keywords (LLM generates 30 suggestions)
    ├─ Content preferences
    └─ Reporting settings
    ↓
Save to: storage/user_profiles/{{user_id}}/profile.json
    ↓
Phase 0: Generate keywords from profile
    ↓
Phase 1: User refines keywords
    ↓
Phases 2-5: Market → GSC → Gap Analysis → Competitors
```

## 🎨 Terminal vs API

| Feature | Terminal | API |
|---------|----------|-----|
| Business info | ✅ Text input | ✅ Web form |
| GSC OAuth | ✅ Click link | ✅ OAuth popup |
| Keywords | ✅ LLM + selection | ✅ LLM + selection |
| Logo upload | ❌ Text description | ✅ File upload |
| Color picker | ❌ Hex code input | ✅ Color picker UI |
| Font selection | ❌ Font name | ✅ Dropdown + preview |

## 📝 Development

Run tests:
```bash
pytest tests/
```

Test individual phase:
```bash
python -m phases.phase0_keyword_generation.keyword_suggester
```

## Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
    create_file(f"{base_path}/README.md", readme)
    print_success("Created: README.md")


def create_env_file(base_path):
    """Create .env template"""
    print_info("Creating .env template...")
    
    env_content = '''# Environment Variables Template

# Mode
APP_MODE=cli

# Logging
LOG_LEVEL=INFO

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# LLM
GOOGLE_API_KEY=your_gemini_api_key_here

# File Uploads (API mode)
MAX_UPLOAD_SIZE_MB=5
ALLOWED_EXTENSIONS=png,jpg,jpeg,svg

# Onboarding
MAX_KEYWORDS_GENERATED=30
MIN_KEYWORDS_SELECTED=5
'''
    create_file(f"{base_path}/.env.template", env_content)
    print_success("Created: .env.template")


def main():
    print_header("SEO Automation Platform V2 - Setup with Onboarding")
    
    # Get project name
    project_name = input(f"{Colors.OKBLUE}→{Colors.ENDC} Project directory name [SEO_Automation_Platform]: ").strip()
    if not project_name:
        project_name = "SEO_Automation_Platform"
    
    base_path = Path.cwd() / project_name
    
    # Create or update project
    if base_path.exists():
        print_info(f"Directory '{project_name}' exists - will add V2 components")
    else:
        print_info(f"Creating new project: {project_name}")
    
    print_info(f"Working directory: {base_path}")
    
    try:
        # Create base directory
        create_directory(base_path)
        
        # Setup all components
        setup_config_files(base_path)
        setup_phases(base_path)
        setup_cli_onboarding(base_path)
        setup_api_onboarding(base_path)
        setup_shared(base_path)
        setup_storage(base_path)
        setup_orchestration(base_path)
        setup_tests(base_path)
        
        # Create project files
        create_main_entry_point(base_path)
        create_requirements(base_path)
        create_gitignore(base_path)
        create_readme(base_path)
        create_env_file(base_path)
        
        print_header("Setup Complete!")
        print_success(f"Project at: {base_path}")
        print()
        
        print_info("✨ V2 Components Added:")
        print("  • Phase 0: Keyword generation (phases/phase0_keyword_generation/)")
        print("  • CLI Onboarding: 8-page terminal flow (cli/onboarding/)")
        print("  • API Onboarding: Web UI with uploads (api/onboarding/)")
        print("  • User Profiles: storage/user_profiles/")
        print("  • Brand Assets: storage/brand_assets/")
        print("  • Complete Data Models: shared/data_models.py")
        print()
        
        print_info("Next steps:")
        print(f"  1. cd {project_name}")
        if not (base_path / "venv").exists():
            print(f"  2. python -m venv venv")
            print(f"  3. source venv/bin/activate")
            print(f"  4. pip install -r requirements.txt")
        else:
            print(f"  2. source venv/bin/activate  (venv exists)")
            print(f"  3. pip install -r requirements.txt  (update deps)")
        print(f"  5. Edit config/credentials.json (add Google Gemini API key)")
        if not (base_path / "phases" / "phase3_gsc" / "auth.py").exists():
            print(f"  6. python migrate_gsc.py  (migrate GSC files)")
        else:
            print(f"  6. GSC already migrated ✓")
        print(f"  7. python main.py  (run terminal mode)")
        print()
        print_warning("📝 Important:")
        print("  - Onboarding runs on first launch")
        print("  - Keywords generated in Page 6 (LLM-powered)")
        print("  - Terminal mode uses text, API mode has full UI")
        
    except Exception as e:
        print(f"{Colors.FAIL}✗{Colors.ENDC} Error during setup: {str(e)}")
        raise


if __name__ == "__main__":
    main()