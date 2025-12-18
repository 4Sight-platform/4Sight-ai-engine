def classify_keywords(market_data: list, gsc_data: list) -> dict:
    gsc_map = {item['keyword']: item for item in gsc_data}
    
    untapped_gold = []
    underperformers = []
    low_priority = []
    
    for item in market_data:
        kw = item['keyword']
        vol = item.get('avg_monthly_searches', 0)
        
        if kw in gsc_map:
            pos = gsc_map[kw].get('position', 100)
            if pos > 10 and vol > 500:
                underperformers.append(kw)
            else:
                low_priority.append(kw)
        else:
            if vol > 1000:
                untapped_gold.append(kw)
            else:
                low_priority.append(kw)
    
    return {
        'untapped_gold': untapped_gold,
        'underperformers': underperformers,
        'low_priority': low_priority
    }
