def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


tool_definitions: list[dict] = [
    _tool(
        "web_search",
        "Search the web for current information, news, facts, or any topic. "
        "Use when the user asks about recent events, current data, or anything you don't know.",
        {"query": {"type": "string", "description": "Search query"}},
        ["query"],
    ),
    _tool(
        "calculate",
        "Calculate any mathematical expression. Use for arithmetic, percentages, conversions, or any math.",
        {"expression": {"type": "string", "description": "Math expression like '(50000 * 0.04) / 12'"}},
        ["expression"],
    ),
    _tool(
        "get_weather",
        "Get current weather for any city in the world.",
        {"city": {"type": "string", "description": "City name like 'Bangalore' or 'New York'"}},
        ["city"],
    ),
    _tool(
        "search_wikipedia",
        "Search Wikipedia for detailed information about any topic, person, place, concept, or event.",
        {"query": {"type": "string", "description": "Topic to search on Wikipedia"}},
        ["query"],
    ),
    _tool(
        "get_datetime",
        "Get current date and time. Use when user asks about today's date, current time, "
        "or time in different timezones.",
        {"timezone": {"type": "string", "description": "Timezone like 'Asia/Kolkata', 'US/Eastern'. Default: 'Asia/Kolkata'"}},
        [],
    ),
]
