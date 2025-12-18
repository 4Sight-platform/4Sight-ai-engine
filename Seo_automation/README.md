# SEO Automation Platform V2

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
Save to: storage/user_profiles/{user_id}/profile.json
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

## Created: 2025-12-17 16:28:57
