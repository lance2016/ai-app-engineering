"""An MCP server's tools become ordinary registry tools; a dead server is a transient error, never a 500."""

import sys

import pytest

from aiapp import Thread, ToolCall
from aiapp.runtime import NeedsConfirmation, ToolRegistry, ToolRunner
from aiapp.runtime.mcp_source import MCPToolSource
from aiapp.storage.memory import InMemoryKeyValueStore
from tests.project.m3.conftest import ctx_for

pytestmark = pytest.mark.anyio
SERVER = [sys.executable, "-m", "aiapp.mcp.toy_notes_server"]


@pytest.fixture
def source():
    created: list[MCPToolSource] = []

    def make(*args: str) -> MCPToolSource:
        src = MCPToolSource([*SERVER, *args], name="notes")
        created.append(src)
        return src

    yield make
    for src in created:
        src.close()


async def test_read_only_server_registers_only_read_only_tools(source) -> None:
    reg = ToolRegistry()
    names = source("--read-only").register_into(reg)
    assert names == ["search_notes"] and reg.get("search_notes").has_side_effects is False


async def test_write_tools_are_side_effects_and_go_through_confirmation(source) -> None:
    reg = ToolRegistry()
    source().register_into(reg)
    assert reg.get("delete_note").has_side_effects is True
    runner = ToolRunner(reg, InMemoryKeyValueStore())
    thread = Thread()
    out = await runner.run(ToolCall(id="c1", name="delete_note", arguments={"uri": "notes://todo"}), ctx_for(thread, {"delete_note"}), thread)
    assert isinstance(out, NeedsConfirmation)


async def test_call_round_trips_and_server_errors_become_results(source) -> None:
    reg = ToolRegistry()
    source().register_into(reg)
    runner = ToolRunner(reg, InMemoryKeyValueStore())
    thread = Thread()
    ctx = ctx_for(thread, {"search_notes", "delete_note"})
    out = await runner.run(ToolCall(id="c1", name="search_notes", arguments={"query": "milk"}), ctx, thread)
    assert out.route == "ok" and "notes://todo" in out.message.content
    thread.append("human_input", confirm_tool_call_id="c2", approved=True)
    out = await runner.run(ToolCall(id="c2", name="delete_note", arguments={"uri": "notes://nope"}), ctx, thread)
    assert out.route == "failed" and out.message.is_error and "no such note" in out.message.content


async def test_server_that_died_is_restarted_transparently(source) -> None:
    reg = ToolRegistry()
    src = source()
    src.register_into(reg)
    src.client._proc.kill()  # the server process goes away between two calls
    src.client._proc.wait()
    runner = ToolRunner(reg, InMemoryKeyValueStore(), retry_base_delay_s=0.001)
    thread = Thread()
    out = await runner.run(ToolCall(id="c1", name="search_notes", arguments={"query": "mum"}), ctx_for(thread, {"search_notes"}), thread)
    assert out.route == "ok" and "notes://todo" in out.message.content
    assert src.client.alive


async def test_server_that_keeps_crashing_is_an_error_result_not_an_exception(source) -> None:
    reg = ToolRegistry()
    source("--crash-on", "tools/call").register_into(reg)
    runner = ToolRunner(reg, InMemoryKeyValueStore(), retry_base_delay_s=0.001)
    thread = Thread()
    out = await runner.run(ToolCall(id="c1", name="search_notes", arguments={"query": "mum"}), ctx_for(thread, {"search_notes"}), thread)
    assert out.route == "transient_exhausted" and out.message.is_error and out.attempts == 3
    assert "disconnected" in out.message.content or "unavailable" in out.message.content
