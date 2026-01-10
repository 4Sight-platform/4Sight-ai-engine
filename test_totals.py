#!/usr/bin/env python3
"""Fetch GSC totals without dimensions"""

import asyncio
import os
import sys
import httpx
from urllib.parse import quote
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def test_totals():
    from onboarding.oauth_manager import OAuthManager
    
    oauth = OAuthManager()
    token_result = await oauth.get_fresh_access_token('user_892ffe13fed3')
    access_token = token_result.get('access_token')
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    site_url = "https://ursdigitally.com/"
    encoded_site = quote(site_url, safe='')
    url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
    
    # Test 1: No dimensions at all (raw totals)
    print("=== TEST 1: NO DIMENSIONS (Raw totals) ===")
    payload = {
        "startDate": "2025-12-10",
        "endDate": "2026-01-09",
        "type": "web"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    
    # Test 2: With date dimension to get daily breakdown
    print("\n=== TEST 2: DATE DIMENSION (Daily) ===")
    payload2 = {
        "startDate": "2025-12-10",
        "endDate": "2026-01-09",
        "dimensions": ["date"],
        "type": "web"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload2, headers=headers, timeout=60.0)
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get("rows", [])
            
            total_clicks = sum(r.get("clicks", 0) for r in rows)
            total_impressions = sum(r.get("impressions", 0) for r in rows)
            
            print(f"Total Days: {len(rows)}")
            print(f"Total Clicks: {total_clicks}")
            print(f"Total Impressions: {total_impressions}")
            
            # Show last 5 days
            print("\nLast 5 days:")
            for row in sorted(rows, key=lambda x: x['keys'][0], reverse=True)[:5]:
                print(f"  {row['keys'][0]}: {row['clicks']} clicks, {row['impressions']} impr")
        else:
            print(f"Error: {response.text}")
    
    # Test 3: Check the exact property URL format
    print("\n=== TEST 3: PROPERTY VERIFICATION ===")
    sites_url = "https://www.googleapis.com/webmasters/v3/sites"
    async with httpx.AsyncClient() as client:
        response = await client.get(sites_url, headers=headers)
        if response.status_code == 200:
            sites = response.json().get("siteEntry", [])
            for site in sites:
                print(f"Property: {site['siteUrl']} - Permission: {site['permissionLevel']}")

if __name__ == "__main__":
    asyncio.run(test_totals())
