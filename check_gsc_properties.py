#!/usr/bin/env python3
"""Check available GSC properties for the user"""

import asyncio
import os
import sys
import httpx
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def check_gsc_properties():
    from onboarding.oauth_manager import OAuthManager
    
    # Get fresh token
    oauth = OAuthManager()
    token_result = await oauth.get_fresh_access_token('user_892ffe13fed3')
    access_token = token_result.get('access_token')
    
    if not access_token:
        print("ERROR: Could not get access token")
        return
    
    print("✅ Got access token")
    
    # List all GSC sites/properties
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Get list of sites
        response = await client.get(
            "https://www.googleapis.com/webmasters/v3/sites",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            sites = data.get("siteEntry", [])
            
            print(f"\n🌐 AVAILABLE GSC PROPERTIES ({len(sites)} total):")
            for site in sites:
                url = site.get("siteUrl", "")
                perm = site.get("permissionLevel", "")
                print(f"   {url} [{perm}]")
                
            # Find ursdigitally properties
            print(f"\n🔍 URSDIGITALLY PROPERTIES:")
            urs_sites = [s for s in sites if 'ursdigitally' in s.get('siteUrl', '').lower()]
            for site in urs_sites:
                print(f"   {site.get('siteUrl')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(check_gsc_properties())
