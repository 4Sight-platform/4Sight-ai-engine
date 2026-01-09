# 4Sight AI Engine - Setup Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for frontend)

## Quick Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/4Sight-platform/4Sight-ai-engine.git
cd 4Sight-ai-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
- `DATABASE_URL` - Your PostgreSQL connection string
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- `ENCRYPTION_KEY` - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- All other API keys as listed in `.env.example`

### 3. Setup Database
```bash
# Create database
createdb foursight_platform

# Run migrations
python run_migration.py
python run_governance_migration.py
python run_asis_cache_migration.py
```

### 4. Start Backend
```bash
python app.py
# Server runs on http://localhost:8001
```

### 5. Complete Onboarding (REQUIRED)
> ⚠️ **IMPORTANT**: Each user MUST complete the onboarding flow to generate OAuth tokens for GSC access.

1. Start the frontend: `cd ../4Sight-dashboard && npm run dev`
2. Visit http://localhost:3000
3. Login and complete full onboarding
4. Connect your Google Search Console during onboarding

## Troubleshooting

### AS-IS State shows "Critical" or empty data
- **Cause**: OAuth tokens not set up. You need to complete onboarding.
- **Fix**: Go through fresh onboarding to authorize GSC access.

### Database connection errors
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running: `pg_isready`

### "Encryption key invalid" error
- Generate new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Update `ENCRYPTION_KEY` in `.env`
