#!/usr/bin/env python3
"""
Query Saved GSC Data
Search and filter data from saved complete dump
"""

import sys
import json
import os
from glob import glob
from src.utils import (
    print_header, print_success, print_error, print_info,
    get_user_input, print_table, get_user_choice
)

def find_latest_dump():
    """Find the most recent data dump file"""
    dump_files = glob("storage/raw_data/complete_dump_*.json")
    
    if not dump_files:
        return None
    
    # Sort by filename (timestamp is in filename)
    dump_files.sort(reverse=True)
    return dump_files[0]

def load_data(filepath):
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load data: {str(e)}")
        return None

def search_queries(data, search_terms):
    """
    Search for queries matching search terms
    
    Args:
        data: Complete data dump
        search_terms: List of keywords to search for
        
    Returns:
        dict: Matching queries with their metrics
    """
    all_queries = data.get('all_queries', [])
    results = {}
    
    for term in search_terms:
        term_lower = term.lower()
        
        # Find exact match first
        exact_match = None
        for query_data in all_queries:
            query = query_data.get('keys', [''])[0]
            if query.lower() == term_lower:
                exact_match = {
                    "keyword": query,
                    "impressions": query_data.get('impressions', 0),
                    "clicks": query_data.get('clicks', 0),
                    "ctr": round(query_data.get('ctr', 0) * 100, 2),
                    "position": round(query_data.get('position', 0), 1),
                    "match_type": "exact"
                }
                break
        
        if exact_match:
            results[term] = exact_match
        else:
            # No match found
            results[term] = {
                "keyword": term,
                "impressions": 0,
                "clicks": 0,
                "ctr": 0.0,
                "position": None,
                "match_type": "not_found"
            }
    
    return results

def display_results(results, data):
    """Display query results in a formatted table"""
    print_header("Keyword Performance Report")
    
    site_url = data.get('site_url', 'Unknown')
    date_range = data.get('date_range', {})
    
    print_info(f"Property: {site_url}")
    print_info(f"Date Range: {date_range.get('start')} to {date_range.get('end')}")
    print_info(f"Data fetched: {data.get('fetch_time', 'Unknown')}")
    print()
    
    # Prepare table
    headers = ["Keyword", "Impressions", "Clicks", "Position", "CTR (%)", "Status"]
    rows = []
    
    for term, result in results.items():
        if result['match_type'] == 'exact':
            position = f"{result['position']:.1f}" if result['position'] else "-"
            status = "✓ Found"
        else:
            position = "-"
            status = "✗ Not ranking"
        
        rows.append([
            result['keyword'],
            f"{result['impressions']:,}",
            f"{result['clicks']:,}",
            position,
            f"{result['ctr']:.2f}%",
            status
        ])
    
    print_table(headers, rows)
    
    # Analysis
    print_header("Analysis")
    
    ranking = [k for k, r in results.items() if r['match_type'] == 'exact']
    not_ranking = [k for k, r in results.items() if r['match_type'] == 'not_found']
    
    if ranking:
        print_success(f"Ranking keywords: {len(ranking)}")
        for kw in ranking:
            r = results[kw]
            print(f"  • {kw}: Position {r['position']:.1f} ({r['impressions']:,} impressions)")
    
    print()
    
    if not_ranking:
        print_error(f"Not ranking: {len(not_ranking)}")
        for kw in not_ranking:
            print(f"  • {kw}: No data in top 1000 queries")
    
    print()

def show_summary(data):
    """Show summary of available data"""
    print_header("Available Data Summary")
    
    print_info(f"Property: {data.get('site_url', 'Unknown')}")
    print_info(f"Fetched: {data.get('fetch_time', 'Unknown')}")
    print()
    
    total_queries = len(data.get('all_queries', []))
    total_pages = len(data.get('top_pages', []))
    
    print(f"  • Total queries tracked: {total_queries}")
    print(f"  • Total pages tracked: {total_pages}")
    print(f"  • Countries: {len(data.get('countries', []))}")
    print(f"  • Devices: {len(data.get('devices', []))}")
    print()
    
    if total_queries > 0:
        # Show top 5 queries
        print_info("Top 5 Queries:")
        for i, query_data in enumerate(data['all_queries'][:5], 1):
            query = query_data.get('keys', [''])[0]
            impressions = query_data.get('impressions', 0)
            clicks = query_data.get('clicks', 0)
            print(f"  {i}. {query}: {impressions:,} impressions, {clicks} clicks")
    
    print()

def main():
    print_header("GSC Data Query Tool")
    
    # Find latest data dump
    print_info("Looking for saved data...")
    dump_file = find_latest_dump()
    
    if not dump_file:
        print_error("No data found!")
        print()
        print_info("Run 'python fetch_data.py' first to download GSC data")
        sys.exit(1)
    
    print_success(f"Found: {dump_file}")
    
    # Load data
    print_info("Loading data...")
    data = load_data(dump_file)
    
    if not data:
        print_error("Failed to load data")
        sys.exit(1)
    
    print_success("Data loaded")
    print()
    
    # Show menu
    while True:
        print("Options:")
        print("  1) Search specific keywords")
        print("  2) View data summary")
        print("  3) Exit")
        print()
        
        choice = get_user_input("Select option (1-3)")
        
        if choice == "1":
            # Search keywords
            print()
            keywords_input = get_user_input("Enter keywords (comma-separated)")
            keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
            
            if not keywords:
                print_error("No keywords provided")
                continue
            
            print()
            print_info(f"Searching for {len(keywords)} keywords...")
            results = search_queries(data, keywords)
            print()
            
            display_results(results, data)
            
        elif choice == "2":
            # Show summary
            print()
            show_summary(data)
            
        elif choice == "3":
            # Exit
            print()
            print_info("Goodbye!")
            break
        else:
            print_error("Invalid choice")
            print()

if __name__ == "__main__":
    main()