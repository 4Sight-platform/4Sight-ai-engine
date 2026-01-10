#!/usr/bin/env python3
"""
Clear ALL data from database for fresh testing
Clears all 35 tables
"""

from sqlalchemy import create_engine, text
from Database.database import DATABASE_URL
import sys

def clear_all_tables():
    """Clear all data from all tables"""
    engine = create_engine(DATABASE_URL)
    
    print("=" * 70)
    print("🗑️  CLEARING ALL DATA FROM DATABASE (35 TABLES)")
    print("=" * 70)
    
    # List of all tables to clear
    tables_to_clear = [
        # AS-IS State
        'as_is_scores',
        'as_is_summary_cache',
        'asis_progress_timeline',
        'competitor_visibility_scores',
        
        # Onboarding
        'onboarding_competitors',
        'onboarding_keywords',
        'business_profiles',
        'products',
        'services',
        'audience_profiles',
        'differentiators',
        'page_urls',
        'reporting_preferences',
        'seo_goals',
        
        # Keywords & Strategy
        'keyword_universe_items',
        'keyword_universes',
        'tracked_keywords',
        'keyword_position_snapshots',
        'strategy_goals',
        
        # Crawl & Signals
        'ai_crawl_governance',
        'crawl_pages',
        'onpage_signals',
        'backlink_signals',
        'technical_signals',
        'cwv_signals',
        'serp_feature_presence',
        
        # Action Plans
        'action_plan_task_history',
        'action_plan_task_pages',
        'action_plan_tasks',
        
        # GSC Data
        'gsc_daily_metrics',
        
        # Integrations & OAuth
        'integrations',
        'oauth_tokens',
        
        # Users (SKIP - don't delete users)
        # 'users',
        # 'email_verification_tokens',
        # 'password_reset_tokens',
    ]
    
    with engine.connect() as connection:
        cleared_count = 0
        skipped_count = 0
        
        for table in tables_to_clear:
            try:
                result = connection.execute(text(f"DELETE FROM {table}"))
                connection.commit()
                rows_deleted = result.rowcount
                print(f"   ✓ Cleared {table} ({rows_deleted} rows)")
                cleared_count += 1
            except Exception as e:
                print(f"   ⚠️  {table}: {str(e)[:50]}...")
                skipped_count += 1
        
        print("\n" + "=" * 70)
        print(f"✅ CLEARED {cleared_count} TABLES SUCCESSFULLY!")
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} tables (errors or don't exist)")
        print("=" * 70)
        print("\n💡 Database is now clean - ready for fresh testing!")
        print("🔒 User accounts preserved (users table not cleared)")

if __name__ == "__main__":
    # Confirmation prompt
    print("\n⚠️  WARNING: This will DELETE ALL DATA from 35 tables!")
    print("   (User accounts will be preserved)")
    response = input("\nAre you sure? Type 'yes' to confirm: ")
    
    if response.lower() == 'yes':
        clear_all_tables()
    else:
        print("❌ Cancelled. No data was deleted.")
