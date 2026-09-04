"""PostgreSQL CostStore over cost_ledger."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, Text, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from aiapp.ops.cost import Charge
from aiapp.storage.models import Base


class CostRow(Base):
    __tablename__ = "cost_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    calls: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PostgresCostStore:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    @classmethod
    def from_url(cls, url: str) -> "PostgresCostStore":
        return cls(create_async_engine(url, pool_pre_ping=True))

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def add(self, charge: Charge) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(CostRow.__table__.insert().values(tenant_id=charge.tenant_id, day=charge.day, model=charge.model, input_tokens=charge.input_tokens, output_tokens=charge.output_tokens, cost_usd=charge.cost_usd, calls=charge.calls))

    async def spent_today(self, tenant_id: str, day: date) -> Decimal:
        async with self._engine.connect() as conn:
            total = await conn.scalar(select(func.coalesce(func.sum(CostRow.cost_usd), 0)).where(CostRow.tenant_id == tenant_id, CostRow.day == day))
        return Decimal(total or 0)

    async def daily_summary(self, tenant_id: str, day: date) -> list[Charge]:
        stmt = (
            select(CostRow.model, func.sum(CostRow.input_tokens), func.sum(CostRow.output_tokens), func.sum(CostRow.cost_usd), func.sum(CostRow.calls))
            .where(CostRow.tenant_id == tenant_id, CostRow.day == day)
            .group_by(CostRow.model)
        )
        async with self._engine.connect() as conn:
            rows = await conn.execute(stmt)
        return [Charge(tenant_id, day, m, int(i), int(o), Decimal(c), int(n)) for m, i, o, c, n in rows]
