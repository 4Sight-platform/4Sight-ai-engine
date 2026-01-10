#!/usr/bin/env python3
"""Test script to verify GSC API data"""

import asyncio
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def test_gsc():
    from onboarding.oauth_manager import OAuthManager
    from asis.gsc_data_service import GSCDataService
    
    # Get fresh token
    oauth = OAuthManager()
    token_result = await oauth.get_fresh_access_token('user_892ffe13fed3')
    access_token = token_result.get('access_token')
    
    if not access_token:
        print("ERROR: Could not get access token")
        return
    
    print("✅ Got access token")
    
    # Initialize GSC service
    gsc = GSCDataService(access_token)
    
    # Check the date ranges being used
    date_ranges = gsc._get_date_ranges()
    print(f"\n📅 DATE RANGES:")
    print(f"   Current: {date_ranges['current']['start']} to {date_ranges['current']['end']}")
    print(f"   Previous: {date_ranges['previous']['start']} to {date_ranges['previous']['end']}")
    
    # Test with the correct site URL
    site_url = "https://ursdigitally.com/"
    print(f"\n🌐 SITE URL: {site_url}")
    
    # Fetch data
    print("\n🔄 Fetching GSC data...")
    data = await gsc.fetch_all_metrics(site_url)
    
    print(f"\n📊 CURRENT PERIOD RESULTS:")
    totals = data['current']['totals']
    print(f"   Total Clicks: {totals['total_clicks']}")
    print(f"   Total Impressions: {totals['total_impressions']}")
    print(f"   Avg Position: {totals['avg_position']}")
    print(f"   Top 10 Keywords: {totals['top10_count']}")
    print(f"   Total Keywords: {totals['keyword_count']}")
    
    print(f"\n🔑 TOP 10 KEYWORDS (by clicks):")
    queries = sorted(data['current']['queries'], key=lambda x: x['clicks'], reverse=True)[:10]
    for q in queries:
        print(f"   [{q['position']:.1f}] {q['query']} - {q['clicks']} clicks, {q['impressions']} impr")
    
    # Check if "digital marketing agency" is in the list
    dma_keyword = [q for q in data['current']['queries'] if 'digital marketing agency' in q['query'].lower()]
    if dma_keyword:
        print(f"\n⚠️ 'digital marketing agency' FOUND in GSC data:")
        for k in dma_keyword:
            print(f"   Position: {k['position']}, Clicks: {k['clicks']}, Impressions: {k['impressions']}")
    else:
        print(f"\n✅ 'digital marketing agency' NOT found in raw GSC data")

if __name__ == "__main__":
    asyncio.run(test_gsc())
