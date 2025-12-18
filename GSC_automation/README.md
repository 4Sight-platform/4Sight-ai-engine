# GSC Connector

Terminal-based Google Search Console API connector with OAuth 2.0 authentication.

## Project Structure

```
GSC_automation/
├── config/
│   └── credentials.json       # OAuth credentials (you need to fill this)
├── storage/
│   ├── tokens/                # Stored refresh tokens (auto-generated)
│   └── properties/            # Selected GSC properties (auto-generated)
├── src/
│   ├── __init__.py
│   ├── auth.py                # OAuth flow handler
│   ├── client.py              # GSC API wrapper
│   ├── storage.py             # File storage operations
│   └── utils.py               # Terminal UI helpers
├── gsc_auth.py                # Main authentication script
├── gsc_query.py               # Main query script
├── requirements.txt           # Python dependencies
└── setup.py                   # This setup script
```

## Setup Instructions

### 1. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Run Setup

```bash
python setup.py
```

### 3. Get Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "SEO-Automation-Tool")
3. Enable "Google Search Console API"
4. Go to "Credentials" → Create "OAuth 2.0 Client ID"
5. Application type: "Desktop app" or "Other"
6. Copy CLIENT_ID and CLIENT_SECRET

### 4. Configure Credentials

Edit `config/credentials.json` and replace:
- `YOUR_CLIENT_ID_HERE` with your actual CLIENT_ID
- `YOUR_CLIENT_SECRET_HERE` with your actual CLIENT_SECRET

### 5. Authenticate

```bash
python gsc_auth.py
```

Follow the terminal prompts to authorize access.

### 6. Query Keywords

```bash
python gsc_query.py
```

Enter keywords to check their performance in GSC.

## Usage Flow

1. **First Time:**
   - Run `gsc_auth.py` → Opens authorization URL
   - You authorize in browser → Get auth code
   - Paste auth code → Tokens saved automatically
   - Select GSC property → Configuration complete

2. **Ongoing:**
   - Run `gsc_query.py` → Enter keywords → Get performance data
   - No re-authorization needed (uses stored refresh token)

## Notes

- Refresh tokens are stored in `storage/tokens/` (gitignored)
- Selected GSC property stored in `storage/properties/` (gitignored)
- Never commit `config/credentials.json` to version control
