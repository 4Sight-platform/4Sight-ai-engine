# Phase 3: GSC Integration

This module handles Google Search Console data fetching and analysis.

## Files

- **auth.py**: OAuth 2.0 authentication flow
- **client.py**: GSC API wrapper (webmasters v3)
- **storage.py**: Token and property persistence
- **utils.py**: Terminal UI utilities
- **fetch_data.py**: Complete data dump fetcher
- **query_data.py**: Search and query saved data

## Usage

### Standalone Testing

```bash
# From project root
cd phases/phase3_gsc

# Authenticate (one-time)
python -c "from auth import GSCAuthenticator; a = GSCAuthenticator(); print('Auth ready')"

# Fetch complete data
python fetch_data.py

# Query specific keywords
python query_data.py
```

### Integration with Workflow

```python
from phases.phase3_gsc.client import GSCClient
from phases.phase3_gsc.auth import GSCAuthenticator

# Authenticate
auth = GSCAuthenticator()
credentials = auth.load_credentials("user_session")

# Query
client = GSCClient(credentials)
data = client.batch_query_keywords(site_url, keywords)
```

## Storage Locations

- **Tokens**: `storage/credentials/gsc_tokens/`
- **Properties**: `storage/credentials/gsc_properties/`
- **Raw Data**: `storage/raw_data/gsc/`

## API Details

- **API**: Google Search Console (webmasters v3)
- **Scope**: `https://www.googleapis.com/auth/webmasters`
- **Rate Limit**: 200 queries/day
- **Auth**: OAuth 2.0 with refresh tokens
