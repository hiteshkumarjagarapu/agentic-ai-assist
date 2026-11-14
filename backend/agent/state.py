from typing import List, Optional, TypedDict


class AgentState(TypedDict):
    messages: List[dict]          # Full conversation
    tool_calls_log: List[dict]    # Tool usage tracking
    current_step: int             # Step counter
    max_steps: int                # Max steps
    final_answer: Optional[str]   # Final response
    session_id: str               # Conversation ID
