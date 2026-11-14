import asyncio

try:
    from ddgs import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    from duckduckgo_search import DDGS  # type: ignore


def _format(results: list[dict]) -> str:
    return "\n".join(f"- {r.get('title', '')}: {r.get('body', '')}" for r in results)


def _search(query: str, max_results: int) -> str:
    # Text search is sometimes empty for news-style queries; fall back to news search.
    for kind in ("text", "news"):
        try:
            results = list(getattr(DDGS(), kind)(query, max_results=max_results))
        except Exception:
            continue
        if results:
            return _format(results)
    return "No results found."


async def web_search(query: str, max_results: int = 3) -> str:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_search, query, max_results), timeout=10)
    except Exception as e:
        return f"Error: web search failed ({type(e).__name__}: {e})"
