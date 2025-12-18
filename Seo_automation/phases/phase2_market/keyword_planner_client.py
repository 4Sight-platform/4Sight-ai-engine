import json
from pathlib import Path

def get_keyword_data(keywords: list) -> list:
    # TODO: Integrate Google Keyword Planner API
    # Return mock data for now
    return [
        {
            'keyword': kw,
            'avg_monthly_searches': 1000,
            'competition': 'MEDIUM',
            'low_top_of_page_bid_micros': 1000000,
            'high_top_of_page_bid_micros': 3000000
        }
        for kw in keywords
    ]
