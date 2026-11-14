from typing import Any, Awaitable, Callable

from agent.tools.calculator import calculate
from agent.tools.datetime_tool import get_datetime
from agent.tools.weather import get_weather
from agent.tools.web_search import web_search
from agent.tools.wikipedia import search_wikipedia

tool_functions: dict[str, Callable[..., Awaitable[str]]] = {
    "web_search": web_search,
    "calculate": calculate,
    "get_weather": get_weather,
    "search_wikipedia": search_wikipedia,
    "get_datetime": get_datetime,
}


async def run_tool(name: str, args: dict[str, Any]) -> str:
    fn = tool_functions.get(name)
    if fn is None:
        return f"Error: unknown tool '{name}'"
    try:
        return await fn(**args)
    except TypeError as e:
        return f"Error: invalid arguments for {name} ({e})"
    except Exception as e:
        return f"Error: {name} failed ({e})"
