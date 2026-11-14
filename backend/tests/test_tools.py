import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from agent.graph import route_after_think  # noqa: E402
from agent.routes import chunk_text  # noqa: E402
from agent.tools import run_tool  # noqa: E402
from agent.tools.calculator import calculate  # noqa: E402
from agent.tools.datetime_tool import get_datetime  # noqa: E402
from auth.jwt_handler import create_token, verify_token  # noqa: E402


@pytest.mark.asyncio
async def test_calculator_basic() -> None:
    assert await calculate("(50000 * 0.04) / 12") == "166.6666666667"
    assert await calculate("2 ** 10") == "1024"
    assert await calculate("-3 + 5") == "2"


@pytest.mark.asyncio
@pytest.mark.parametrize("expr", ["__import__('os').system('echo hi')", "open('x')", "1/0", "9**9**9", "abc"])
async def test_calculator_rejects_unsafe(expr: str) -> None:
    assert (await calculate(expr)).startswith("Error")


@pytest.mark.asyncio
async def test_datetime() -> None:
    assert "Timezone: US/Eastern" in await get_datetime("US/Eastern")
    assert (await get_datetime("Nope/Zone")).startswith("Error")


@pytest.mark.asyncio
async def test_run_tool_unknown_and_bad_args() -> None:
    assert (await run_tool("nope", {})).startswith("Error")
    assert (await run_tool("calculate", {"wrong": 1})).startswith("Error")


def test_jwt_roundtrip() -> None:
    payload = verify_token(create_token(7, "a@b.com"))
    assert payload and payload["user_id"] == 7 and payload["email"] == "a@b.com"
    assert verify_token("garbage") is None


def test_routing_respects_max_steps() -> None:
    tc = {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]}
    base = {"messages": [tc], "tool_calls_log": [], "final_answer": None, "session_id": "s", "max_steps": 5}
    assert route_after_think({**base, "current_step": 1}) == "execute"  # type: ignore[arg-type]
    assert route_after_think({**base, "current_step": 5}) != "execute"  # type: ignore[arg-type]
    plain = {**base, "messages": [{"role": "assistant", "content": "hi"}], "current_step": 1}
    assert route_after_think(plain) != "execute"  # type: ignore[arg-type]


def test_chunk_text_roundtrip() -> None:
    assert "".join(chunk_text("The temp in Paris is 20C.")) == "The temp in Paris is 20C."
