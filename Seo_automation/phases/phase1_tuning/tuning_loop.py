def interactive_tuning(keywords: list) -> list:
    print(f"Current keywords ({len(keywords)}):")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")
    
    action = input("\n[a]dd, [r]emove, [d]one: ").strip().lower()
    
    if action == 'a':
        new = input("Add keyword: ").strip()
        keywords.append(new)
    elif action == 'r':
        idx = int(input("Remove # : ")) - 1
        keywords.pop(idx)
    
    return keywords
