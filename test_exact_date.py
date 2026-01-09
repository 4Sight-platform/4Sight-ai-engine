#!/usr/bin/env python3
"""Test GSC API with exact date range from dashboard"""

import asyncio
import os
import sys
import httpx
from urllib.parse import quote
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def test_exact_date():
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
    
    # Test with EXACTLY the date range visible in screenshot: Dec 10 to Jan 9 (today)
    payload = {
        "startDate": "2025-12-10",
        "endDate": "2026-01-09",  # Including today
        "dimensions": ["query"],
        "rowLimit": 5000,  # Get more rows
        "aggregationType": "auto"
    }
    
    print(f"📅 Testing date range: {payload['startDate']} to {payload['endDate']}")
    print(f"🌐 Site URL: {site_url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get("rows", [])
            
            total_clicks = sum(r.get("clicks", 0) for r in rows)
            total_impressions = sum(r.get("impressions", 0) for r in rows)
            
            print(f"\n📊 API RESULTS:")
            print(f"   Total Clicks: {total_clicks}")
            print(f"   Total Impressions: {total_impressions}")
            print(f"   Total Keywords: {len(rows)}")
            
            # Average position (weighted by impressions)
            if total_impressions > 0:
                avg_pos = sum(r["position"] * r["impressions"] for r in rows) / total_impressions
                print(f"   Avg Position: {avg_pos:.1f}")
            
            print(f"\n🔑 TOP 5 KEYWORDS:")
            sorted_rows = sorted(rows, key=lambda x: x["clicks"], reverse=True)[:5]
            for r in sorted_rows:
                print(f"   {r['keys'][0]} - {r['clicks']} clicks, pos={r['position']:.1f}")
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_exact_date())
