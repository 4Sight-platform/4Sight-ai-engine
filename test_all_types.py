#!/usr/bin/env python3
"""Test GSC API with ALL search types combined"""

import asyncio
import os
import sys
import httpx
from urllib.parse import quote
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def test_all_types():
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
    
    search_types = ["web", "image", "video", "news", "discover", "googleNews"]
    
    total_all = {"clicks": 0, "impressions": 0}
    
    for search_type in search_types:
        payload = {
            "startDate": "2025-12-10",
            "endDate": "2026-01-09",
            "dimensions": ["query"],
            "rowLimit": 5000,
            "type": search_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            
            if response.status_code == 200:
                data = response.json()
                rows = data.get("rows", [])
                
                clicks = sum(r.get("clicks", 0) for r in rows)
                impressions = sum(r.get("impressions", 0) for r in rows)
                
                if clicks > 0 or impressions > 0:
                    print(f"📊 {search_type.upper()}: {clicks} clicks, {impressions} impressions")
                    total_all["clicks"] += clicks
                    total_all["impressions"] += impressions
            else:
                if "not a valid value" not in response.text:
                    print(f"❌ {search_type}: Error {response.status_code}")
    
    print(f"\n📊 TOTAL ALL TYPES: {total_all['clicks']} clicks, {total_all['impressions']} impressions")

if __name__ == "__main__":
    asyncio.run(test_all_types())
