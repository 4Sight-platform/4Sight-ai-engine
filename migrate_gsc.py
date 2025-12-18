#!/usr/bin/env python3
"""
Migrate GSC_automation to SEO_Automation_Platform

This script moves your existing GSC_automation files into the new project structure.
"""

import os
import shutil
from pathlib import Path


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


def print_error(text):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")


def find_gsc_directory():
    """Try to locate GSC_automation directory"""
    cwd = Path.cwd()
    
    # Check current directory
    if (cwd / "GSC_automation").exists():
        return cwd / "GSC_automation"
    
    # Check parent directory
    if (cwd.parent / "GSC_automation").exists():
        return cwd.parent / "GSC_automation"
    
    # Check if we're already inside GSC_automation
    if cwd.name == "GSC_automation":
        return cwd
    
    return None


def find_target_directory():
    """Try to locate target SEO automation project directory"""
    cwd = Path.cwd()
    
    # Common project names to check
    project_names = [
        "SEO_Automation_Platform",
        "SEO_automation",
        "SEO_Automation",
        "seo_automation"
    ]
    
    # Check current directory for any of these names
    for name in project_names:
        if (cwd / name).exists():
            # Verify it has the expected structure
            if (cwd / name / "phases" / "phase3_gsc").exists():
                return cwd / name
    
    # Check parent directory
    for name in project_names:
        if (cwd.parent / name).exists():
            if (cwd.parent / name / "phases" / "phase3_gsc").exists():
                return cwd.parent / name
    
    # Check if we're already inside a valid project directory
    if (cwd / "phases" / "phase3_gsc").exists():
        return cwd
    
    # Search for any directory with the expected structure in current location
    for item in cwd.iterdir():
        if item.is_dir() and (item / "phases" / "phase3_gsc").exists():
            return item
    
    return None


def verify_gsc_structure(gsc_path):
    """Verify GSC_automation has expected structure"""
    required_files = {
        "src/auth.py": "OAuth authentication",
        "src/client.py": "GSC API client",
        "src/storage.py": "Token storage",
        "src/utils.py": "Terminal utilities",
        "fetch_data.py": "Data fetching script",
        "gsc_query.py": "Query script",
    }
    
    missing = []
    for file, desc in required_files.items():
        if not (gsc_path / file).exists():
            missing.append(f"{file} ({desc})")
    
    return missing


def copy_file(src, dest, description):
    """Copy file with error handling"""
    try:
        # Create parent directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(src, dest)
        print_success(f"Copied: {description}")
        return True
    except Exception as e:
        print_error(f"Failed to copy {description}: {str(e)}")
        return False


def copy_directory(src, dest, description):
    """Copy directory with error handling"""
    try:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print_success(f"Copied: {description}")
        return True
    except Exception as e:
        print_error(f"Failed to copy {description}: {str(e)}")
        return False


def migrate_gsc_files(gsc_path, target_path):
    """Migrate GSC files to new structure"""
    
    print_info("Starting migration...")
    
    phase3_path = target_path / "phases" / "phase3_gsc"
    
    # Ensure phase3_gsc exists
    phase3_path.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = 0
    
    # 1. Copy src/ files to phase3_gsc/
    print_info("\n[1/4] Migrating core modules...")
    src_files = [
        ("src/auth.py", "auth.py", "OAuth authentication"),
        ("src/client.py", "client.py", "GSC API client"),
        ("src/storage.py", "storage.py", "Token storage"),
        ("src/utils.py", "utils.py", "Terminal utilities"),
        ("src/__init__.py", "__init__.py", "Package init"),
    ]
    
    for src_file, dest_file, desc in src_files:
        total_count += 1
        src = gsc_path / src_file
        dest = phase3_path / dest_file
        if src.exists():
            if copy_file(src, dest, desc):
                success_count += 1
        else:
            print_warning(f"Skipping {desc} (not found)")
    
    # 2. Copy main scripts
    print_info("\n[2/4] Migrating main scripts...")
    script_files = [
        ("fetch_data.py", "fetch_data.py", "Data fetching script"),
        ("gsc_query.py", "query_data.py", "Query script (renamed)"),  # Rename for clarity
    ]
    
    for src_file, dest_file, desc in script_files:
        total_count += 1
        src = gsc_path / src_file
        dest = phase3_path / dest_file
        if src.exists():
            if copy_file(src, dest, desc):
                success_count += 1
        else:
            print_warning(f"Skipping {desc} (not found)")
    
    # 3. Migrate storage/ directory
    print_info("\n[3/4] Migrating storage data...")
    storage_migrations = [
        (
            "storage/tokens",
            "storage/credentials/gsc_tokens",
            "GSC tokens"
        ),
        (
            "storage/properties",
            "storage/credentials/gsc_properties",
            "GSC properties"
        ),
        (
            "storage/raw_data",
            "storage/raw_data/gsc",
            "Raw GSC data"
        ),
    ]
    
    for src_dir, dest_dir, desc in storage_migrations:
        total_count += 1
        src = gsc_path / src_dir
        dest = target_path / dest_dir
        if src.exists() and any(src.iterdir()):  # Only copy if directory has content
            if copy_directory(src, dest, desc):
                success_count += 1
        else:
            print_info(f"Skipping {desc} (empty or not found)")
    
    # 4. Migrate config if needed
    print_info("\n[4/4] Migrating configuration...")
    total_count += 1
    config_src = gsc_path / "config" / "credentials.json"
    config_dest = target_path / "config" / "credentials.json"
    
    if config_src.exists():
        # Merge with existing config
        import json
        
        try:
            # Read existing config
            with open(config_dest, 'r') as f:
                existing_config = json.load(f)
            
            # Read GSC config
            with open(config_src, 'r') as f:
                gsc_config = json.load(f)
            
            # Merge GSC credentials into existing config
            existing_config["gsc"] = gsc_config
            
            # Write merged config
            with open(config_dest, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            print_success("Merged GSC credentials into config")
            success_count += 1
        except Exception as e:
            print_error(f"Failed to merge config: {str(e)}")
    else:
        print_info("Skipping config (not found)")
    
    return success_count, total_count


def create_phase3_readme(phase3_path):
    """Create README for phase3_gsc"""
    readme_content = """# Phase 3: GSC Integration

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
"""
    
    readme_path = phase3_path / "README.md"
    readme_path.write_text(readme_content)
    print_success("Created: phase3_gsc/README.md")


def main():
    print_header("GSC_automation Migration Script")
    
    # Find source directory
    print_info("Locating GSC_automation directory...")
    gsc_path = find_gsc_directory()
    
    if not gsc_path:
        print_error("Could not find GSC_automation directory!")
        print_info("Please run this script from:")
        print("  - GSC_automation directory")
        print("  - Parent directory containing GSC_automation/")
        print("  - SEO_Automation_Platform directory")
        return
    
    print_success(f"Found GSC_automation at: {gsc_path}")
    
    # Verify GSC structure
    print_info("Verifying GSC_automation structure...")
    missing = verify_gsc_structure(gsc_path)
    
    if missing:
        print_warning("Missing files:")
        for item in missing:
            print(f"  - {item}")
        
        proceed = input(f"\n{Colors.OKBLUE}→{Colors.ENDC} Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print_info("Migration cancelled")
            return
    else:
        print_success("All required files found")
    
    # Find target directory
    print_info("Locating SEO Automation project directory...")
    target_path = find_target_directory()
    
    if not target_path:
        print_warning("Could not auto-detect target directory")
        print_info("Available directories:")
        cwd = Path.cwd()
        for item in cwd.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                print(f"  - {item.name}")
        
        target_name = input(f"\n{Colors.OKBLUE}→{Colors.ENDC} Enter target directory name: ").strip()
        if not target_name:
            print_error("No directory specified")
            return
        
        target_path = cwd / target_name
        
        if not target_path.exists():
            print_error(f"Directory not found: {target_path}")
            return
        
        # Verify it has the expected structure
        if not (target_path / "phases" / "phase3_gsc").exists():
            print_error(f"Invalid structure - missing phases/phase3_gsc/")
            print_info("Please run setup_project.py first")
            return
    
    print_success(f"Found target at: {target_path}")
    
    # Verify phase3_gsc exists
    phase3_path = target_path / "phases" / "phase3_gsc"
    if not phase3_path.exists():
        print_error(f"Phase 3 directory not found at: {phase3_path}")
        print_info("Please run setup_project.py first")
        return
    
    # Confirm migration
    print("\n" + "="*60)
    print(f"  Migration Plan")
    print("="*60)
    print(f"  From: {gsc_path}")
    print(f"  To:   {phase3_path}")
    print("="*60 + "\n")
    
    confirm = input(f"{Colors.OKBLUE}→{Colors.ENDC} Proceed with migration? (y/n): ").strip().lower()
    if confirm != 'y':
        print_info("Migration cancelled")
        return
    
    # Perform migration
    success_count, total_count = migrate_gsc_files(gsc_path, target_path)
    
    # Create README
    create_phase3_readme(phase3_path)
    
    # Summary
    print_header("Migration Complete!")
    print_success(f"Migrated {success_count}/{total_count} items successfully")
    
    if success_count < total_count:
        print_warning(f"{total_count - success_count} items were skipped or failed")
    
    print("\n" + "="*60)
    print(f"  Next Steps")
    print("="*60)
    print(f"  1. Verify migrated files in: {phase3_path}")
    print(f"  2. Check storage data in: {target_path / 'storage'}")
    print(f"  3. Update imports in other phases to use:")
    print(f"     from phases.phase3_gsc.client import GSCClient")
    print(f"  4. Test Phase 3 standalone:")
    print(f"     cd {target_path}")
    print(f"     python -m phases.phase3_gsc.fetch_data")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()