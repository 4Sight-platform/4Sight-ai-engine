def analyze_market_data(keyword_data: list) -> dict:
    total = len(keyword_data)
    avg_vol = sum(k.get('avg_monthly_searches', 0) for k in keyword_data) / total if total else 0
    
    high_vol = [k for k in keyword_data if k.get('avg_monthly_searches', 0) > 5000]
    low_comp = [k for k in keyword_data if k.get('competition', '') == 'LOW']
    
    return {
        'total_keywords': total,
        'avg_search_volume': avg_vol,
        'high_volume_keywords': len(high_vol),
        'low_competition_keywords': len(low_comp)
    }
