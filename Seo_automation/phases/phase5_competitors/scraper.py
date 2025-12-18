def scrape_competitors(keywords: list) -> dict:
    # TODO: Implement real scraping with Custom Search API
    return {
        kw: {
            'keyword': kw,
            'top_urls': [
                {'url': f'https://example{i}.com', 'title': f'Example {i}', 'description': f'Description for {kw}'}
                for i in range(1, 4)
            ]
        }
        for kw in keywords[:5]
    }
