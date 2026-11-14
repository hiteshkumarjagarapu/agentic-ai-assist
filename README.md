# Agentic AI Assistant

A multi-tool LLM agent (LangGraph, ReAct loop) with a streaming React chat UI.

- **Backend:** FastAPI, LangGraph, Groq, MySQL (SQLAlchemy), Redis, JWT auth
- **Tools:** web search (DuckDuckGo), weather (OpenWeatherMap), calculator (AST-safe), Wikipedia, datetime
- **Frontend:** React 18, React Router 6, Tailwind, Axios, SSE streaming with live tool/thinking indicators

## Verification status

Checked end to end against real services (MySQL, Upstash Redis, Groq, OpenWeatherMap, Wikipedia, DuckDuckGo), both with local dev servers and with `docker compose`:

| Area | Status |
|---|---|
| Register / login / JWT / protected routes / logout | Verified in the browser |
| Weather, calculator, Wikipedia, web search, datetime tools | Each verified from the chat UI |
| Multi-step ReAct loop (several tool calls, self-correction after a tool error) | Verified |
| SSE events (`thinking`, `tool_start`, `tool_result`, `token`, `done`) and live tool cards | Verified |
| Conversation history: Redis buffer + MySQL, sidebar, `/chat/:sessionId` | Verified |
| Markdown rendering (tables, lists, bold, code) | Verified |
| Dark / light theme, persists across reloads | Verified |
| Docker Compose (backend + frontend, backend reaching host MySQL, CORS) | Verified |
| Backend unit tests (calculator safety, JWT, routing / step limit, tool errors) | 11 passing |

Not covered by automated tests: the external-API tools and the UI (they were verified manually). The 20 requests/min rate limiter was not load-tested.

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

The backend reads `./.env`. Compose sets `DB_HOST=host.docker.internal`, which replaces the host in `DATABASE_URL` so a MySQL running on your machine is reachable from the container (that MySQL user must be allowed to connect from non-`localhost` addresses). Percent-encode special characters in the password (e.g. `@` → `%40`).

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
