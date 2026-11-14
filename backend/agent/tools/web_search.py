import asyncio

try:
    from ddgs import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    from duckduckgo_search import DDGS  # type: ignore


def _search(query: str, max_results: int) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    return "\n".join(f"- {r.get('title', '')}: {r.get('body', '')}" for r in results)


async def web_search(query: str, max_results: int = 3) -> str:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_search, query, max_results), timeout=10)
    except Exception as e:
        return f"Error: web search failed ({type(e).__name__}: {e})"
