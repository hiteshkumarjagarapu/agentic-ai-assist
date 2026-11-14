import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import auth.models  # noqa: F401  (register tables)
import memory.models  # noqa: F401
from agent.routes import router as agent_router
from auth.jwt_handler import verify_token
from auth.routes import router as auth_router
from config import settings
from database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Agentic AI Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Max RATE_LIMIT_PER_MIN requests/minute per user (per IP when unauthenticated)."""
    if request.method == "OPTIONS" or request.url.path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)
    key = f"ip:{request.client.host if request.client else 'unknown'}"
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        payload = verify_token(auth_header[7:])
        if payload:
            key = f"user:{payload['user_id']}"
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.RATE_LIMIT_PER_MIN:
        return JSONResponse({"detail": "Rate limit exceeded. Try again in a minute."}, status_code=429,
                            headers={"Retry-After": "60"})
    q.append(now)
    return await call_next(request)


app.include_router(auth_router)
app.include_router(agent_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
