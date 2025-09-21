import os
from serpapi.google_search import GoogleSearch


def serpapi_search(query: str, num_results: int = 3):
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY not set in env")
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        # other params you might want e.g., "gl": "us"
    }
    search = GoogleSearch(params)
    data = search.get_dict()
    items = data.get('organic_results') or []
    results = []
    for item in items[:num_results]:
        results.append({
            'title': item.get('title'),
            'link': item.get('link') or item.get('url'),
            'snippet': item.get('snippet')
        })
    return results
