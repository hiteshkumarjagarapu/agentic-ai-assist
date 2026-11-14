from langgraph.graph import END, StateGraph

from agent.nodes import execute_node, think_node
from agent.state import AgentState


def route_after_think(state: AgentState) -> str:
    last = state["messages"][-1]
    if last.get("tool_calls") and state["current_step"] < state["max_steps"]:
        return "execute"
    return END


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("think", think_node)
    g.add_node("execute", execute_node)
    g.set_entry_point("think")
    g.add_conditional_edges("think", route_after_think, {"execute": "execute", END: END})
    g.add_edge("execute", "think")
    return g.compile()


agent_graph = build_graph()
