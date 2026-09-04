"""Readiness: every dependency answers, or the pod is not ready. Liveness stays cheap and local."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


Check = Callable[[], Awaitable[None]]


async def run_checks(checks: dict[str, Check], *, timeout_s: float = 2.0) -> list[CheckResult]:
    async def one(name: str, check: Check) -> CheckResult:
        try:
            async with asyncio.timeout(timeout_s):
                await check()
            return CheckResult(name, True)
        except Exception as exc:
            return CheckResult(name, False, f"{type(exc).__name__}: {exc}"[:200])

    return list(await asyncio.gather(*(one(n, c) for n, c in checks.items())))


def postgres_check(url: str) -> Check:
    async def check() -> None:
        import asyncpg

        conn = await asyncpg.connect(url.replace("postgresql+asyncpg://", "postgresql://"), timeout=1.5)
        try:
            await conn.fetchval("SELECT 1")
        finally:
            await conn.close()

    return check


def redis_check(url: str) -> Check:
    async def check() -> None:
        from redis.asyncio import Redis

        client = Redis.from_url(url, socket_connect_timeout=1.5)
        try:
            await client.ping()
        finally:
            await client.aclose()

    return check
