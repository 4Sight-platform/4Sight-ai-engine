def analyze_competitor(url_data: dict) -> dict:
    title_length = len(url_data.get('title', ''))
    has_keyword = url_data.get('keyword', '').lower() in url_data.get('title', '').lower()
    
    return {
        'url': url_data.get('url'),
        'title_length': title_length,
        'keyword_in_title': has_keyword,
        'insights': 'Good title optimization' if has_keyword else 'Missing keyword in title'
    }
