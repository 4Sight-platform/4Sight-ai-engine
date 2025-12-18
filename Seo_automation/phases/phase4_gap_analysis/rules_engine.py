RULES = {
    'untapped_gold': lambda vol, pos: vol > 1000 and pos == 0,
    'underperformer': lambda vol, pos: 0 < pos < 20 and vol > 500,
    'low_priority': lambda vol, pos: vol < 500 or pos > 50
}

def apply_rules(keyword, volume, position):
    for rule_name, rule_func in RULES.items():
        if rule_func(volume, position):
            return rule_name
    return 'unknown'
