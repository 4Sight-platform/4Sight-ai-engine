#!/usr/bin/env python3
"""
Fetch Complete GSC Data Dump
Downloads all available data and saves to file for later querying
"""

import sys
import json
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import httplib2

from src.auth import GSCAuthenticator
from src.storage import TokenStorage, PropertyStorage
from src.utils import print_header, print_success, print_error, print_info

def ensure_data_dir():
    """Create raw_data directory if it doesn't exist"""
    data_dir = "storage/raw_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def main():
    print_header("GSC Complete Data Dump")
    
    session_id = "user_session"
    token_storage = TokenStorage()
    property_storage = PropertyStorage()
    
    # Check authentication
    if not token_storage.session_exists(session_id):
        print_error("Not authenticated! Run: python gsc_auth.py")
        sys.exit(1)
    
    # Load credentials
    print_info("Loading credentials...")
    tokens = token_storage.load_tokens(session_id)
    site_url = property_storage.load_property(session_id)
    
    if not tokens or not site_url:
        print_error("Missing credentials or property")
        sys.exit(1)
    
    print_success(f"Property: {site_url}")
    
    # Refresh access token
    print_info("Refreshing access token...")
    authenticator = GSCAuthenticator()
    
    try:
        access_token = authenticator.refresh_access_token(tokens['refresh_token'])
        credentials = authenticator.build_credentials(access_token, tokens['refresh_token'])
        print_success("Token refreshed")
    except Exception as e:
        print_error(f"Token refresh failed: {str(e)}")
        sys.exit(1)
    
    # Build service
    print_info("Building GSC service...")
    try:
        http = credentials.authorize(httplib2.Http())
        service = build('webmasters', 'v3', http=http)
        print_success("Service ready")
    except Exception as e:
        print_error(f"Service build failed: {str(e)}")
        sys.exit(1)
    
    # Date range (last 90 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    print()
    print_info(f"Date Range: {start_date} to {end_date}")
    print()
    
    # Prepare output structure
    complete_data = {
        "site_url": site_url,
        "fetch_time": datetime.now().isoformat(),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }
    
    # 1. Fetch ALL queries (top 1000)
    print_info("[1/6] Fetching top 1000 queries...")
    try:
        query_request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query"],
            "rowLimit": 1000
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=query_request).execute()
        complete_data["all_queries"] = response.get('rows', [])
        print_success(f"  Fetched {len(complete_data['all_queries'])} queries")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["all_queries"] = []
    
    # 2. Fetch top pages
    print_info("[2/6] Fetching top 100 pages...")
    try:
        page_request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["page"],
            "rowLimit": 100
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=page_request).execute()
        complete_data["top_pages"] = response.get('rows', [])
        print_success(f"  Fetched {len(complete_data['top_pages'])} pages")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["top_pages"] = []
    
    # 3. Fetch country breakdown
    print_info("[3/6] Fetching country breakdown...")
    try:
        country_request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["country"],
            "rowLimit": 50
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=country_request).execute()
        complete_data["countries"] = response.get('rows', [])
        print_success(f"  Fetched {len(complete_data['countries'])} countries")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["countries"] = []
    
    # 4. Fetch device breakdown
    print_info("[4/6] Fetching device breakdown...")
    try:
        device_request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["device"]
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=device_request).execute()
        complete_data["devices"] = response.get('rows', [])
        print_success(f"  Fetched {len(complete_data['devices'])} device types")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["devices"] = []
    
    # 5. Fetch daily timeline
    print_info("[5/6] Fetching 90-day timeline...")
    try:
        timeline_request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["date"]
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=timeline_request).execute()
        complete_data["timeline"] = response.get('rows', [])
        print_success(f"  Fetched {len(complete_data['timeline'])} days")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["timeline"] = []
    
    # 6. Fetch sitemap status
    print_info("[6/6] Fetching sitemap status...")
    try:
        response = service.sitemaps().list(siteUrl=site_url).execute()
        complete_data["sitemaps"] = response.get('sitemap', [])
        print_success(f"  Fetched {len(complete_data['sitemaps'])} sitemaps")
    except Exception as e:
        print_error(f"  Failed: {str(e)}")
        complete_data["sitemaps"] = []
    
    # Save to file
    data_dir = ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"complete_dump_{timestamp}.json"
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(complete_data, f, indent=2)
    
    print()
    print_header("Data Dump Complete!")
    print_success(f"Saved to: {filepath}")
    print()
    
    # Summary
    print_info("Data Summary:")
    print(f"  • Queries: {len(complete_data.get('all_queries', []))}")
    print(f"  • Pages: {len(complete_data.get('top_pages', []))}")
    print(f"  • Countries: {len(complete_data.get('countries', []))}")
    print(f"  • Devices: {len(complete_data.get('devices', []))}")
    print(f"  • Timeline Days: {len(complete_data.get('timeline', []))}")
    print(f"  • Sitemaps: {len(complete_data.get('sitemaps', []))}")
    print()
    
    print_info("Next: Run 'python gsc_query.py' to search this data")
    print()

if __name__ == "__main__":
    main()