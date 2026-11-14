# CLAUDE.md — Agentic AI Assistant (Multi-Tool Agent)

## Project Overview
Build a production-grade Agentic AI Assistant — an LLM-powered chatbot that uses multiple external tools (web search, weather, calculator, Wikipedia, datetime) via LangGraph with ReAct pattern. The agent thinks step-by-step, decides which tool to use, executes it, observes the result, and repeats until it has a complete answer.

## Tech Stack
- Backend: FastAPI + Python 3.10+
- LLM: Groq API (llama3-8b-8192) — free
- Agent Framework: LangGraph (StateGraph)
- Pattern: ReAct (Reasoning + Acting)
- Tools: Web search (DuckDuckGo), Weather (OpenWeatherMap), Calculator, Wikipedia, Datetime
- Cache: Redis (Upstash free tier)
- Database: SQLite (SQLAlchemy ORM)
- Auth: JWT (python-jose)
- Frontend: React 18 + React Router v6 + Tailwind CSS + Axios
- Deploy: Docker + Docker Compose

## Folder Structure
```
agentic-ai-assistant/
├── backend/
│   ├── main.py                  # FastAPI app + CORS + lifespan
│   ├── config.py                # env variables (pydantic BaseSettings)
│   ├── database.py              # SQLAlchemy engine + session + Base
│   ├── auth/
│   │   ├── models.py            # User model
│   │   ├── schemas.py           # UserCreate, UserLogin, TokenResponse
│   │   ├── routes.py            # POST /auth/register, /auth/login
│   │   ├── jwt_handler.py       # create_token, verify_token
│   │   └── dependencies.py      # get_current_user
│   ├── agent/
│   │   ├── routes.py            # POST /agent/chat (streaming SSE)
│   │   ├── state.py             # AgentState TypedDict
│   │   ├── graph.py             # LangGraph setup — nodes, edges, compile
│   │   ├── nodes.py             # think_node, execute_node, answer_node
│   │   ├── tools_config.py      # Tool definitions JSON for Groq
│   │   └── tools/
│   │       ├── __init__.py      # tool_functions map
│   │       ├── web_search.py    # DuckDuckGo search (free, no API key!)
│   │       ├── calculator.py    # Safe math evaluation
│   │       ├── weather.py       # OpenWeatherMap API
│   │       ├── wikipedia.py     # Wikipedia API (no key needed!)
│   │       └── datetime_tool.py # Current date, time, timezone
│   ├── memory/
│   │   ├── models.py            # Conversation, Message SQLAlchemy models
│   │   ├── service.py           # save/get conversation history
│   │   └── redis_memory.py      # Redis conversation buffer
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Routes setup
│   │   ├── api/
│   │   │   └── api.js           # Axios instance + interceptors
│   │   ├── hooks/
│   │   │   ├── useAuth.js       # login, logout, token
│   │   │   └── useAgentChat.js  # SSE streaming + tool status
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login + Register
│   │   │   └── Chat.jsx         # Agent chat interface
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── ChatWindow.jsx      # Messages display
│   │   │   ├── MessageBubble.jsx   # User/AI message
│   │   │   ├── ToolIndicator.jsx   # "🔧 Using weather tool..."
│   │   │   ├── ThinkingStep.jsx    # "🧠 Thinking..."
│   │   │   ├── StreamingText.jsx   # Token by token display
│   │   │   └── Sidebar.jsx         # Conversation history
│   │   └── index.css
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Backend Requirements

### Authentication (same as Project 1)
- POST /auth/register — email, password, name. bcrypt hash. Return JWT.
- POST /auth/login — verify. Return JWT.
- JWT: HS256, 24hr expiry, payload: {user_id, email}.
- Dependency: get_current_user from Authorization header.

### Agent Tools (5 tools)

#### 1. Web Search (DuckDuckGo — FREE, no API key!)
```python
from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 3) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
```

#### 2. Calculator (safe eval)
```python
import ast, operator

SAFE_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.Pow: operator.pow}

def calculate(expression: str) -> str:
    # Safe math eval — no exec/eval security risk
    tree = ast.parse(expression, mode='eval')
    result = _eval_node(tree.body)
    return str(result)
```

#### 3. Weather (OpenWeatherMap)
```python
import httpx

async def get_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    data = response.json()
    return f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
```

#### 4. Wikipedia (no API key needed!)
```python
import httpx

async def search_wikipedia(query: str) -> str:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    data = response.json()
    return data.get("extract", "No article found")[:500]
```

#### 5. Datetime
```python
from datetime import datetime
import pytz

def get_datetime(timezone: str = "Asia/Kolkata") -> str:
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return f"Current date: {now.strftime('%Y-%m-%d')}, Time: {now.strftime('%H:%M:%S')}, Timezone: {timezone}"
```

### Tool Definitions for Groq (tools_config.py)
```python
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, facts, or any topic. Use when the user asks about recent events, current data, or anything you don't know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate any mathematical expression. Use for arithmetic, percentages, conversions, or any math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression like '(50000 * 0.04) / 12'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for any city in the world.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name like 'Bangalore' or 'New York'"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for detailed information about any topic, person, place, concept, or event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic to search on Wikipedia"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Get current date and time. Use when user asks about today's date, current time, or time in different timezones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone like 'Asia/Kolkata', 'US/Eastern'. Default: 'Asia/Kolkata'"}
                },
                "required": []
            }
        }
    }
]
```

### LangGraph Agent Setup

#### State (state.py)
```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    messages: List[dict]          # Full conversation
    tool_calls_log: List[dict]    # Tool usage tracking
    current_step: int             # Step counter
    max_steps: int                # Max 5 steps
    final_answer: Optional[str]   # Final response
    session_id: str               # Conversation ID
```

#### Graph (graph.py)
- Entry point: "think" node
- "think" → calls Groq with messages + tools
- Conditional edge after "think":
  - If tool_calls present → go to "execute" node
  - If no tool_calls → go to END (final answer)
- "execute" → runs tool functions, appends results to messages
- "execute" → back to "think" (loop!)
- Max 5 iterations to prevent infinite loops

#### SSE Streaming Events
The /agent/chat endpoint streams different event types:
```
data: {"type": "thinking", "content": "Analyzing your question..."}\n\n
data: {"type": "tool_start", "tool": "weather", "args": {"city": "Bangalore"}}\n\n
data: {"type": "tool_result", "tool": "weather", "result": "28°C, Partly cloudy"}\n\n
data: {"type": "thinking", "content": "Now I need to calculate..."}\n\n
data: {"type": "tool_start", "tool": "calculate", "args": {"expression": "28 * 1.8 + 32"}}\n\n
data: {"type": "tool_result", "tool": "calculate", "result": "82.4"}\n\n
data: {"type": "token", "content": "The"}\n\n
data: {"type": "token", "content": " temperature"}\n\n
data: {"type": "token", "content": " in"}\n\n
data: {"type": "done"}\n\n
```

This allows the frontend to show:
- 🧠 "Thinking..." animation
- 🔧 "Using weather tool..." with args
- ✅ Tool result display
- 💬 Streaming final answer token by token

### Agent Chat Endpoint
- POST /agent/chat — StreamingResponse (text/event-stream)
- Request: {message: str, session_id: str (optional)}
- Flow:
  1. Load conversation history from Redis/DB (last 10 messages for context)
  2. Build messages array: system prompt + history + user message
  3. Run LangGraph agent — stream events (thinking, tool_start, tool_result, tokens)
  4. After complete: save to conversation history
  5. Cache final answer in Redis (TTL: 1800s)

### System Prompt for Agent
```
You are a helpful AI assistant with access to tools.
Use tools when you need real-time data, calculations, or factual information.
Think step by step. Use the most appropriate tool for each task.
If you can answer directly without tools, do so.
Be concise and helpful. If a tool returns an error, inform the user.
```

### Conversation Memory
- Redis: store last 10 messages per session (buffer memory)
- SQLite: permanent storage of all conversations
- On new message: append to Redis buffer + SQLite
- On agent start: load last 10 from Redis for context

### Rate Limiting
- Max 20 requests per minute per user
- Middleware based — check in request interceptor

## Frontend Requirements

### Routing
- / → redirect to /login
- /login → Login/Register
- /chat → Agent chat (protected)
- /chat/:sessionId → Specific conversation (protected)

### Axios Setup (same as Project 1)
- baseURL, token interceptor, 401 handler

### useAgentChat Hook
```javascript
// Parse different SSE event types
function useAgentChat() {
    const [messages, setMessages] = useState([]);
    const [thinking, setThinking] = useState(false);
    const [activeTool, setActiveTool] = useState(null);
    const [streaming, setStreaming] = useState(false);

    const sendMessage = async (input) => {
        // Add user message
        // Create empty AI message
        // Start SSE stream
        // Parse events:
        //   type: "thinking" → setThinking(true)
        //   type: "tool_start" → setActiveTool({name, args})
        //   type: "tool_result" → update tool result display
        //   type: "token" → append to AI message text
        //   type: "done" → setStreaming(false)
    };

    return { messages, thinking, activeTool, streaming, sendMessage };
}
```

### Chat UI Components

#### ToolIndicator.jsx
```jsx
// Shows: 🔧 Using weather tool... {"city": "Bangalore"}
// Then: ✅ Result: "28°C, Partly cloudy"
// Animated — appears during tool execution
```

#### ThinkingStep.jsx
```jsx
// Shows: 🧠 Thinking... (animated dots)
// Appears between tool calls when agent is reasoning
```

#### MessageBubble.jsx
```jsx
// User messages: right aligned, blue background
// AI messages: left aligned, gray background
// Tool usage: inline cards showing tool name + result
// Streaming text: typing cursor animation
```

### Styling
- Tailwind CSS, dark/light theme
- Tool indicators: colored cards (blue for search, orange for weather, etc.)
- Thinking animation: pulsing dots
- Professional ChatGPT-like UI

## Docker

### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
```

## Build Order
1. backend/config.py + database.py + main.py (skeleton)
2. auth/ (register, login, JWT — same as Project 1)
3. agent/tools/ — all 5 tool functions
4. agent/tools_config.py — tool definitions JSON
5. agent/state.py — AgentState TypedDict
6. agent/nodes.py — think_node + execute_node
7. agent/graph.py — LangGraph StateGraph + compile
8. agent/routes.py — /agent/chat SSE streaming with event types
9. memory/ — Redis buffer + SQLite permanent
10. Frontend: api.js + useAuth + Login
11. Frontend: useAgentChat hook (SSE parsing with event types)
12. Frontend: ChatWindow + MessageBubble + ToolIndicator + ThinkingStep
13. Frontend: Sidebar (conversation list)
14. Docker setup
15. Testing + README

## Important Rules
- Use async/await everywhere
- Pydantic v2 for schemas
- Every tool function must have try/except — return error message, never crash
- Max 5 agent steps — prevent infinite loops
- Stream different event types (thinking, tool_start, tool_result, token, done)
- Tool functions must be fast — timeout 10 seconds max
- Calculator must be SAFE — no eval(), use ast parsing
- .env for all secrets
- Type hints on all functions

## Extra Packages (beyond standard)
```
pip install duckduckgo-search    # web search — free, no API key!
pip install langgraph            # agent framework
pip install pytz                 # timezone support
```