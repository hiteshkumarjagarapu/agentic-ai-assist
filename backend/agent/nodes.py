import json
from typing import Any

from groq import AsyncGroq

from agent.state import AgentState
from agent.tools import run_tool
from agent.tools_config import tool_definitions
from config import settings

SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.
Use tools when you need real-time data, calculations, or factual information.
Think step by step. Use the most appropriate tool for each task.
If you can answer directly without tools, do so.
Be concise and helpful. If a tool returns an error, inform the user."""

_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=30)
    return _client


async def think_node(state: AgentState) -> dict[str, Any]:
    """Call the LLM with messages + tools. The route streams the final answer to the client."""
    step = state["current_step"] + 1
    # On the last allowed step, withhold tools so the model must answer.
    use_tools = step < state["max_steps"]
    messages = state["messages"]
    if not use_tools:
        # Final step: tell the model to answer from what it has (it cannot call tools now).
        messages = messages + [{
            "role": "user",
            "content": "Answer now using the information gathered so far. Do not call any tools. "
                       "If a tool failed, say so briefly.",
        }]
    kwargs: dict[str, Any] = {"model": settings.GROQ_MODEL, "messages": messages, "temperature": 0.3}
    if use_tools:
        kwargs.update(tools=tool_definitions, tool_choice="auto")
    try:
        resp = await get_client().chat.completions.create(**kwargs)
    except Exception as e:
        msg = f"Sorry, the language model request failed: {e}"
        return {
            "current_step": step,
            "final_answer": msg,
            "messages": state["messages"] + [{"role": "assistant", "content": msg}],
        }
    m = resp.choices[0].message
    entry: dict[str, Any] = {"role": "assistant", "content": m.content or ""}
    if m.tool_calls:
        entry["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in m.tool_calls
        ]
        return {"current_step": step, "messages": state["messages"] + [entry], "final_answer": None}
    return {"current_step": step, "messages": state["messages"] + [entry], "final_answer": m.content or ""}


async def execute_node(state: AgentState) -> dict[str, Any]:
    last = state["messages"][-1]
    messages = list(state["messages"])
    log = list(state["tool_calls_log"])
    for tc in last.get("tool_calls", []):
        name = tc["function"]["name"]
        try:
            args = json.loads(tc["function"]["arguments"] or "{}")
        except json.JSONDecodeError:
            args = {}
        result = await run_tool(name, args)
        log.append({"tool": name, "args": args, "result": result})
        messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    return {"messages": messages, "tool_calls_log": log}
