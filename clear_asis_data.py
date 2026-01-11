#!/usr/bin/env python3
"""
Clear AS-IS State Data - Comprehensive Reset
Clears all AS-IS related tables so new data can be loaded
"""

from sqlalchemy import create_engine, text
from Database.database import DATABASE_URL
import sys

def clear_asis_data():
    """Clear all AS-IS state data from the database"""
    engine = create_engine(DATABASE_URL)
    
    print("=" * 70)
    print("🗑️  CLEARING ALL AS-IS STATE DATA")
    print("=" * 70)
    
    # List of AS-IS related tables to clear
    asis_tables = [
        # Core AS-IS State Tables
        'as_is_scores',
        'as_is_summary_cache',
        'asis_progress_timeline',
        
        # GSC Data
        'gsc_daily_metrics',
        
        # Keyword Tracking
        'tracked_keywords',
        'keyword_position_snapshots',
        
        # SERP Features
        'serp_feature_presence',
        
        # Competitor Data
        'competitor_visibility_scores',
        
        # Crawl Data
        'crawl_pages',
        'onpage_signals',
        'backlink_signals',
        'technical_signals',
        'cwv_signals',
        'ai_crawl_governance',
    ]
    
    with engine.connect() as connection:
        cleared_count = 0
        total_rows_deleted = 0
        
        print("\n📋 Tables to clear:")
        for table in asis_tables:
            print(f"   - {table}")
        
        print("\n🔄 Starting deletion...\n")
        
        for table in asis_tables:
            try:
                result = connection.execute(text(f"DELETE FROM {table}"))
                connection.commit()
                rows_deleted = result.rowcount
                total_rows_deleted += rows_deleted
                print(f"   ✓ Cleared {table} ({rows_deleted} rows)")
                cleared_count += 1
            except Exception as e:
                print(f"   ⚠️  {table}: {str(e)[:50]}...")
        
        print("\n" + "=" * 70)
        print(f"✅ CLEARED {cleared_count}/{len(asis_tables)} TABLES SUCCESSFULLY!")
        print(f"📊 Total rows deleted: {total_rows_deleted}")
        print("=" * 70)
        print("\n💡 AS-IS State data has been cleared!")
        print("🔄 You can now load fresh AS-IS data from GSC/GA4")
        print("\n📌 Note: User accounts, onboarding data, and action plans preserved")

if __name__ == "__main__":
    # Confirmation prompt
    print("\n⚠️  WARNING: This will DELETE ALL AS-IS STATE DATA!")
    print("   This includes:")
    print("   - AS-IS scores and summary cache")
    print("   - GSC daily metrics")
    print("   - Keyword tracking data")
    print("   - SERP features")
    print("   - Competitor visibility scores")
    print("   - Crawl data (pages, signals, CWV)")
    print("   - Progress timeline")
    print("\n   Other data preserved:")
    print("   ✓ User accounts")
    print("   ✓ Onboarding data")
    print("   ✓ Action plan tasks")
    print("   ✓ OAuth tokens")
    
    response = input("\n🤔 Are you sure? Type 'yes' to confirm: ")
    
    if response.lower() == 'yes':
        clear_asis_data()
    else:
        print("❌ Cancelled. No data was deleted.")
