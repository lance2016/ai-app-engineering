"""Per-tenant token buckets on memory and Redis; the cost ledger on memory and PostgreSQL."""

import asyncio
import uuid
from datetime import date
from decimal import Decimal

import pytest

from aiapp.adapters.base import Usage
from aiapp.ops.cost import BudgetExhausted, Charge, CostLedger, InMemoryCostStore, PriceTable
from aiapp.ops.ratelimit import InMemoryRateLimiter

pytestmark = pytest.mark.anyio


@pytest.fixture(params=["memory", "redis"])
async def limiter(request):
    if request.param == "memory":
        yield InMemoryRateLimiter()
        return
    from aiapp.ops.ratelimit import RedisRateLimiter

    lim = RedisRateLimiter.from_url(request.getfixturevalue("redis_url"))
    yield lim
    await lim.close()


@pytest.fixture(params=["memory", "postgres"])
async def cost_store(request):
    if request.param == "memory":
        yield InMemoryCostStore()
        return
    from aiapp.ops.postgres_cost import PostgresCostStore

    store = PostgresCostStore.from_url(request.getfixturevalue("postgres_url"))
    yield store
    await store.dispose()


async def test_bucket_allows_burst_then_refills(limiter) -> None:
    key = f"t-{uuid.uuid4().hex[:6]}"
    decisions = [await limiter.acquire(key, rate=50, capacity=3) for _ in range(4)]
    assert [d.allowed for d in decisions] == [True, True, True, False]
    assert 0 < decisions[3].retry_after_s <= 0.05
    await asyncio.sleep(0.05)
    assert (await limiter.acquire(key, rate=50, capacity=3)).allowed
    assert (await limiter.acquire(f"other-{key}", rate=50, capacity=3)).allowed, "buckets are per key: another tenant is unaffected"


async def test_ledger_prices_by_model_and_enforces_the_daily_budget(cost_store) -> None:
    prices = PriceTable.load()
    ledger = CostLedger(cost_store, prices, daily_budget_usd=Decimal("0.001"))
    tenant = f"t-{uuid.uuid4().hex[:6]}"
    cost = await ledger.charge(tenant, Usage(input_tokens=1_000_000, output_tokens=0), "fake")
    assert cost == Decimal("0.27")
    assert await ledger.remaining(tenant) < 0
    with pytest.raises(BudgetExhausted):
        await ledger.ensure_budget(tenant)
    await ledger.ensure_budget(f"{tenant}-other")  # another tenant's budget is untouched
    summary = await cost_store.daily_summary(tenant, ledger.today())
    assert len(summary) == 1 and summary[0].model == "fake" and summary[0].input_tokens == 1_000_000 and summary[0].calls == 1
    unknown = prices.cost("some-new-model", Usage(1_000_000, 1_000_000))
    assert unknown == Decimal("5.0"), "unknown models fall back to the default price rather than costing nothing"


async def test_unlimited_when_no_budget(cost_store) -> None:
    ledger = CostLedger(cost_store, PriceTable.load())
    assert await ledger.remaining("anyone") is None
    await ledger.ensure_budget("anyone")


def test_charge_summary_aggregates_in_memory() -> None:
    store = InMemoryCostStore()
    d = date(2026, 9, 4)
    asyncio.run(store.add(Charge("t", d, "fake", 10, 5, Decimal("0.1"))))
    asyncio.run(store.add(Charge("t", d, "fake", 20, 5, Decimal("0.2"))))
    rows = asyncio.run(store.daily_summary("t", d))
    assert rows[0].input_tokens == 30 and rows[0].cost_usd == Decimal("0.3") and rows[0].calls == 2
