#!/usr/bin/env python3
"""
GSC Connector Setup Script
Creates complete folder structure and all necessary files
"""

import os
import json
import subprocess
import sys

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✓ Created: {path}/")
    else:
        print(f"  Exists: {path}/")

def create_file(path, content=""):
    """Create file with optional content"""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)
        print(f"✓ Created: {path}")
    else:
        print(f"  Exists: {path}")

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def main():
    print_header("GSC Connector - Complete Setup")
    
    # Step 1: Create folder structure
    print("[1/6] Creating folder structure...")
    
    folders = [
        "config",
        "storage/tokens",
        "storage/properties",
        "src"
    ]
    
    for folder in folders:
        create_directory(folder)
    
    # Step 2: Create config files
    print("\n[2/6] Creating configuration files...")
    
    # credentials.json template
    credentials_template = {
        "client_id": "YOUR_CLIENT_ID_HERE",
        "client_secret": "YOUR_CLIENT_SECRET_HERE",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "oauth_scope": "https://www.googleapis.com/auth/webmasters"
    }
    
    credentials_path = "config/credentials.json"
    if not os.path.exists(credentials_path):
        with open(credentials_path, 'w') as f:
            json.dump(credentials_template, f, indent=2)
        print(f"✓ Created: {credentials_path}")
        print("  ⚠️  You need to add your CLIENT_ID and CLIENT_SECRET!")
    else:
        print(f"  Exists: {credentials_path}")
    
    # .gitkeep files
    create_file("storage/tokens/.gitkeep")
    create_file("storage/properties/.gitkeep")
    
    # Step 3: Create src/ module files
    print("\n[3/6] Creating source modules in src/...")
    
    # src/__init__.py
    init_content = """# GSC Connector Package
__version__ = '1.0.0'
"""
    create_file("src/__init__.py", init_content)
    
    # src/auth.py (placeholder)
    auth_content = """# OAuth Authentication Handler
# This file will contain OAuth flow logic
"""
    create_file("src/auth.py", auth_content)
    
    # src/client.py (placeholder)
    client_content = """# GSC API Client
# This file will contain GSC API wrapper functions
"""
    create_file("src/client.py", client_content)
    
    # src/storage.py (placeholder)
    storage_content = """# Token and Property Storage
# This file will handle file-based storage operations
"""
    create_file("src/storage.py", storage_content)
    
    # src/utils.py (placeholder)
    utils_content = """# Terminal UI Utilities
# This file will contain helper functions for pretty terminal output
"""
    create_file("src/utils.py", utils_content)
    
    # Step 4: Create main scripts
    print("\n[4/6] Creating main scripts...")
    
    # gsc_auth.py (placeholder)
    gsc_auth_content = """#!/usr/bin/env python3
\"\"\"
GSC Authentication Script
Run this first to connect your Google Search Console
\"\"\"

# This will be the main authentication script
# User runs: python gsc_auth.py

print("GSC Authentication - To be implemented")
"""
    create_file("gsc_auth.py", gsc_auth_content)
    
    # gsc_query.py (placeholder)
    gsc_query_content = """#!/usr/bin/env python3
\"\"\"
GSC Query Script
Run this to query keyword performance data
\"\"\"

# This will be the main query script
# User runs: python gsc_query.py

print("GSC Query - To be implemented")
"""
    create_file("gsc_query.py", gsc_query_content)
    
    # Step 5: Create project files
    print("\n[5/6] Creating project files...")
    
    # requirements.txt
    requirements = """google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.2.0
oauth2client==4.1.3
httplib2==0.22.0
"""
    create_file("requirements.txt", requirements)
    
    # .gitignore
    gitignore = """# Credentials and tokens
config/credentials.json
storage/tokens/*.json
storage/properties/*.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    create_file(".gitignore", gitignore)
    
    # README.md
    readme = """# GSC Connector

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
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
"""
    create_file("README.md", readme)
    
    # Step 6: Install dependencies (if in venv)
    print("\n[6/6] Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install dependencies")
        print("  Try manually: pip install -r requirements.txt")
    
    # Final verification
    print_header("Setup Complete!")
    
    print("✓ Folder structure created")
    print("✓ All files created:")
    print("  - config/credentials.json")
    print("  - src/__init__.py")
    print("  - src/auth.py (placeholder)")
    print("  - src/client.py (placeholder)")
    print("  - src/storage.py (placeholder)")
    print("  - src/utils.py (placeholder)")
    print("  - gsc_auth.py (placeholder)")
    print("  - gsc_query.py (placeholder)")
    print("  - requirements.txt")
    print("  - .gitignore")
    print("  - README.md")
    print("")
    print("⚠️  NEXT STEPS:")
    print("")
    print("1. Get OAuth credentials from Google Cloud Console")
    print("   https://console.cloud.google.com/")
    print("")
    print("2. Edit config/credentials.json with your:")
    print("   - CLIENT_ID")
    print("   - CLIENT_SECRET")
    print("")
    print("3. Wait for the actual implementation code")
    print("   (The placeholder files will be replaced with working code)")
    print("")

if __name__ == "__main__":
    main()