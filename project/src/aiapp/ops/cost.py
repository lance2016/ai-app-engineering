"""Cost as a runtime signal: price every response, attribute it to a tenant, compare with a daily budget while the run is going.

Prices live in one table with a date on it, loaded from config, never scattered through the code.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Protocol

from aiapp.adapters.base import Usage

DEFAULT_PRICES_PATH = Path(__file__).resolve().parents[1] / "prices.json"
CENT_MICRO = Decimal("0.000001")


@dataclass(frozen=True)
class Price:
    input_per_m: Decimal
    output_per_m: Decimal


@dataclass
class PriceTable:
    as_of: str
    prices: dict[str, Price]
    default: Price

    @classmethod
    def load(cls, path: Path | None = None) -> "PriceTable":
        raw = json.loads((path or Path(os.environ.get("AIAPP_PRICES_PATH", DEFAULT_PRICES_PATH))).read_text(encoding="utf-8"))
        prices = {name: Price(Decimal(str(p["input_per_m"])), Decimal(str(p["output_per_m"]))) for name, p in raw["models"].items()}
        default = prices.pop("_default")
        return cls(as_of=raw["as_of"], prices=prices, default=default)

    def cost(self, model: str, usage: Usage) -> Decimal:
        price = self.prices.get(model, self.default)
        cost = (Decimal(usage.input_tokens) * price.input_per_m + Decimal(usage.output_tokens) * price.output_per_m) / Decimal(1_000_000)
        return cost.quantize(CENT_MICRO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Charge:
    tenant_id: str
    day: date
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    calls: int = 1


class CostStore(Protocol):
    async def add(self, charge: Charge) -> None: ...
    async def spent_today(self, tenant_id: str, day: date) -> Decimal: ...
    async def daily_summary(self, tenant_id: str, day: date) -> list[Charge]: ...


@dataclass
class InMemoryCostStore:
    rows: list[Charge] = field(default_factory=list)

    async def add(self, charge: Charge) -> None:
        self.rows.append(charge)

    async def spent_today(self, tenant_id: str, day: date) -> Decimal:
        return sum((r.cost_usd for r in self.rows if r.tenant_id == tenant_id and r.day == day), Decimal(0))

    async def daily_summary(self, tenant_id: str, day: date) -> list[Charge]:
        by_model: dict[str, Charge] = {}
        for r in self.rows:
            if r.tenant_id == tenant_id and r.day == day:
                prev = by_model.get(r.model)
                by_model[r.model] = Charge(tenant_id, day, r.model, (prev.input_tokens if prev else 0) + r.input_tokens, (prev.output_tokens if prev else 0) + r.output_tokens, (prev.cost_usd if prev else Decimal(0)) + r.cost_usd, (prev.calls if prev else 0) + 1)
        return list(by_model.values())


class BudgetExhausted(Exception):
    def __init__(self, tenant_id: str, spent: Decimal, budget: Decimal):
        super().__init__(f"tenant {tenant_id} spent {spent} of daily budget {budget} USD")
        self.spent, self.budget = spent, budget


@dataclass
class CostLedger:
    store: CostStore
    prices: PriceTable
    daily_budget_usd: Decimal | None = None  # None = unlimited

    @staticmethod
    def today() -> date:
        return datetime.now(UTC).date()

    async def charge(self, tenant_id: str, usage: Usage, model: str) -> Decimal:
        cost = self.prices.cost(model, usage)
        await self.store.add(Charge(tenant_id, self.today(), model, usage.input_tokens, usage.output_tokens, cost))
        return cost

    async def remaining(self, tenant_id: str) -> Decimal | None:
        if self.daily_budget_usd is None:
            return None
        return self.daily_budget_usd - await self.store.spent_today(tenant_id, self.today())

    async def ensure_budget(self, tenant_id: str) -> None:
        remaining = await self.remaining(tenant_id)
        if remaining is not None and remaining <= 0:
            raise BudgetExhausted(tenant_id, self.daily_budget_usd - remaining, self.daily_budget_usd)  # type: ignore[operator]
