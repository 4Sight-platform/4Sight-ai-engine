#!/usr/bin/env python3
"""Test script to verify Moz Backlink Service"""

import asyncio
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

async def test_moz_backlinks():
    from asis.moz_backlink_service import MozBacklinkService
    
    moz = MozBacklinkService()
    domain = "ursdigitally.com"
    
    print(f"🔍 Testing Moz Backlink Service for {domain}")
    print("=" * 50)
    
    # Test URL metrics
    print("\n📊 URL METRICS:")
    metrics = await moz.fetch_url_metrics(domain)
    print(f"   Domain Authority: {metrics.get('domain_authority')}")
    print(f"   Spam Score: {metrics.get('spam_score')}")
    print(f"   Linking Root Domains: {metrics.get('linking_root_domains')}")
    print(f"   External Links: {metrics.get('external_links')}")
    
    # Test linking domains
    print("\n🔗 LINKING DOMAINS:")
    linking_domains = await moz.fetch_linking_domains(domain, limit=10)
    for ld in linking_domains[:5]:
        print(f"   - {ld.get('domain')} (DA: {ld.get('domain_authority')})")
    
    # Test anchor text
    print("\n⚓ ANCHOR TEXT DISTRIBUTION:")
    anchors = await moz.fetch_anchor_text(domain)
    dist = anchors.get('anchor_distribution', {})
    for anchor_type, count in dist.items():
        print(f"   - {anchor_type}: {count}")
    
    # Test combined analysis
    print("\n📈 COMPREHENSIVE BACKLINK ANALYSIS:")
    analysis = await moz.get_backlink_analysis(domain)
    print(f"   Referring Domains: {analysis.get('referring_domains')}")
    print(f"   Avg Authority: {analysis.get('avg_authority_score')}")
    print(f"   Dofollow Ratio: {analysis.get('dofollow_ratio'):.2f}")
    print(f"   Spam Status: {analysis.get('spam_analysis', {}).get('status')}")
    print(f"   Authority Distribution: {analysis.get('authority_distribution')}")
    print(f"   Data Source: {analysis.get('data_source')}")
    
    print("\n✅ Moz Backlink Service test complete!")

if __name__ == "__main__":
    asyncio.run(test_moz_backlinks())
