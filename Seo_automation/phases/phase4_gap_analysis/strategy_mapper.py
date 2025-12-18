STRATEGIES = {
    'untapped_gold': 'Create new content targeting this keyword',
    'underperformer': 'Optimize existing content',
    'low_priority': 'Monitor or deprioritize'
}

def map_strategy(category: str) -> str:
    return STRATEGIES.get(category, 'No strategy defined')

def get_action_items(classified_keywords: dict) -> list:
    actions = []
    for category, keywords in classified_keywords.items():
        for kw in keywords[:5]:  # Top 5 per category
            actions.append({
                'keyword': kw,
                'category': category,
                'action': map_strategy(category),
                'priority': 'HIGH' if category == 'untapped_gold' else 'MEDIUM'
            })
    return actions
