import httpx

_UA = "AgenticAIAssistant/1.0 (https://github.com/agentic-ai-assistant; educational project)"
_HEADERS = {"User-Agent": _UA, "Api-User-Agent": _UA}


async def search_wikipedia(query: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10, headers=_HEADERS, follow_redirects=True) as client:
            # Resolve the query to the best-matching title first.
            s = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "opensearch", "search": query, "limit": 1, "format": "json"},
            )
            titles = s.json()[1] if s.status_code == 200 else []
            title = titles[0] if titles else query
            resp = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")
            )
        if resp.status_code == 404:
            return "No article found"
        if resp.status_code != 200:
            return f"Error: Wikipedia returned HTTP {resp.status_code}"
        return (resp.json().get("extract") or "No article found")[:800]
    except Exception as e:
        return f"Error: Wikipedia lookup failed ({type(e).__name__}: {e})"
