"""Every ThreadStore implementation must pass these. The fixture runs them on memory and PostgreSQL."""

import pytest

from aiapp.storage.base import InvalidTransition, SeqConflict, ThreadNotFound, flush
from aiapp.thread import Event, Thread

pytestmark = pytest.mark.anyio


async def test_create_then_load_returns_an_equal_snapshot(thread_store) -> None:
    thread = await thread_store.create("tenant-a")
    thread.append("user_message", content="hi")
    thread.append("run_started", model="fake")
    await flush(thread_store, thread, 0)

    loaded = await thread_store.load(thread.thread_id, tenant_id="tenant-a")
    assert loaded.thread_id == thread.thread_id
    assert [(e.type, e.data) for e in loaded.events] == [(e.type, e.data) for e in thread.events]
    assert loaded.status() == "running"

    loaded.append("assistant_message", content="draft")  # mutating the snapshot is invisible until appended
    again = await thread_store.load(thread.thread_id, tenant_id="tenant-a")
    assert len(again.events) == 2


async def test_other_tenant_and_unknown_id_are_the_same_error(thread_store) -> None:
    thread = await thread_store.create("tenant-a")
    with pytest.raises(ThreadNotFound):
        await thread_store.load(thread.thread_id, tenant_id="tenant-b")
    with pytest.raises(ThreadNotFound):
        await thread_store.load("thr_nope", tenant_id="tenant-a")


async def test_two_writers_on_one_thread_one_loses(thread_store) -> None:
    """Failure injection: two processes load the same thread and both append. Exactly one wins."""
    thread = await thread_store.create("tenant-a")
    thread.append("user_message", content="hi")
    await flush(thread_store, thread, 0)

    writer_1 = await thread_store.load(thread.thread_id, tenant_id="tenant-a")
    writer_2 = await thread_store.load(thread.thread_id, tenant_id="tenant-a")
    writer_1.append("run_started", model="fake")
    writer_2.append("run_started", model="other")
    await flush(thread_store, writer_1, 1)
    with pytest.raises(SeqConflict):
        await flush(thread_store, writer_2, 1)

    final = await thread_store.load(thread.thread_id, tenant_id="tenant-a")
    assert [e.type for e in final.events] == ["user_message", "run_started"]
    assert final.events[1].data == {"model": "fake"}, "no lost or reordered events"


async def test_assistant_message_cannot_follow_human_input_requested(thread_store) -> None:
    thread = await thread_store.create("tenant-a")
    thread.append("user_message", content="book a table")
    thread.append("human_input_requested", tool_call_id="c1", question="which one?")
    await flush(thread_store, thread, 0)
    with pytest.raises(InvalidTransition):
        await thread_store.append(thread.thread_id, Event(type="assistant_message", data={"content": "sure"}), expected_seq=2)
    # the right next event is the human's answer
    await thread_store.append(thread.thread_id, Event(type="human_input", data={"tool_call_id": "c1", "content": "A"}), expected_seq=2)
    assert (await thread_store.load(thread.thread_id, tenant_id="tenant-a")).status() == "running"


async def test_append_to_unknown_thread_raises(thread_store) -> None:
    with pytest.raises(ThreadNotFound):
        await thread_store.append("thr_ghost", Event(type="user_message", data={}), expected_seq=0)


async def test_status_is_derived_from_the_log_after_a_restart(thread_store, request) -> None:
    """Lesson 07: status is a fold over events. A new store instance over the same data must agree."""
    thread = await thread_store.create("tenant-a")
    for e in [
        Event("user_message", {"content": "hi"}),
        Event("run_started", {"model": "fake"}),
        Event("assistant_message", {"content": "hello", "tool_calls": []}),
        Event("run_finished", {"answer": "hello", "usage": {"input_tokens": 12, "output_tokens": 3}}),
    ]:
        thread.events.append(e)
    await flush(thread_store, thread, 0)

    if type(thread_store).__name__ == "PostgresThreadStore":
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import create_async_engine

        from aiapp.storage.models import Conversation, Task
        from aiapp.storage.postgres import PostgresThreadStore

        fresh = PostgresThreadStore.from_url(request.getfixturevalue("postgres_url"))  # "another process"
        try:
            reloaded = await fresh.load(thread.thread_id, tenant_id="tenant-a")
            assert reloaded.status() == "finished"
            engine = create_async_engine(request.getfixturevalue("postgres_url"))
            async with engine.connect() as conn:
                cached = await conn.scalar(select(Conversation.status).where(Conversation.id == thread.thread_id))
                task = (await conn.execute(select(Task.stop_reason, Task.tokens_in, Task.tokens_out).where(Task.conversation_id == thread.thread_id))).one()
            await engine.dispose()
            assert cached == reloaded.status(), "the cache must agree with the fold"
            assert task == ("finished", 12, 3)
        finally:
            await fresh.dispose()
    else:
        assert (await thread_store.load(thread.thread_id, tenant_id="tenant-a")).status() == "finished"
