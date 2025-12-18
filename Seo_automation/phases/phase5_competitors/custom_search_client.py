def search_keyword(keyword: str, num_results: int = 10) -> list:
    # TODO: Integrate Google Custom Search API
    return [
        {
            'url': f'https://result{i}.com',
            'title': f'Result {i} for {keyword}',
            'snippet': f'Snippet about {keyword}'
        }
        for i in range(1, num_results + 1)
    ]
