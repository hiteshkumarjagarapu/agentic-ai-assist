# Agentic AI Assistant

A multi-tool LLM agent (LangGraph, ReAct loop) with a streaming React chat UI.

- **Backend:** FastAPI, LangGraph, Groq, MySQL (SQLAlchemy), Redis, JWT auth
- **Tools:** web search (DuckDuckGo), weather (OpenWeatherMap), calculator (AST-safe), Wikipedia, datetime
- **Frontend:** React 18, React Router 6, Tailwind, Axios, SSE streaming with live tool/thinking indicators

## Configuration

Create `.env` in the project root (see `backend/.env.example`):

| Variable | Notes |
|---|---|
| `DATABASE_URL` | e.g. `mysql+pymysql://user:pass@localhost:3306/agentic_ai_assistant` (database must exist; tables are auto-created) |
| `GROQ_API_KEY` | Groq key |
| `GROQ_MODEL` | default `openai/gpt-oss-20b` (the `llama3-8b-8192` model in the original spec has been retired by Groq) |
| `REDIS_URL` | `redis://` / `rediss://` URL. An Upstash `redis-cli --tls -u redis://...` string is also accepted. Optional: without Redis, history is read from MySQL |
| `WEATHER_API_KEY` | OpenWeatherMap key |
| `JWT_SECRET` | long random string |

## Run locally

```bash
# backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # source .venv/bin/activate on Linux/macOS
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Docker

```bash
docker compose up --build   # frontend :3000, backend :8000
```

`DATABASE_URL` must be reachable from inside the container (use `host.docker.internal` instead of `localhost` for a MySQL on the host).

## API

- `POST /auth/register`, `POST /auth/login` → JWT (HS256, 24h)
- `POST /agent/chat` — body `{message, session_id?}`, streams SSE events:
  `session`, `thinking`, `tool_start`, `tool_result`, `token`, `error`, `done`
- `GET /agent/conversations`, `GET /agent/conversations/{id}/messages`, `DELETE /agent/conversations/{id}`
- `GET /health`

Limits: 20 requests/min per user, max 5 agent steps, 10 s tool timeout, last 10 messages as context, final answers cached in Redis for 1800 s.

## Notes

- The agent loop runs non-streaming LLM calls (needed to detect tool calls); the final answer is emitted to the client word by word.
- Rate limiting is in-process memory, so it is per backend instance.

## Tests

```bash
cd backend && pytest
```
