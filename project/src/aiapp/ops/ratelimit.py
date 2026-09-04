"""Per-tenant token buckets. Redis when available (one Lua script, atomic), in-memory otherwise."""

import time
from dataclasses import dataclass, field
from typing import Protocol

_BUCKET_LUA = """
local key, rate, capacity, now, cost = KEYS[1], tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
local data = redis.call('HMGET', key, 'tokens', 'updated')
local tokens = tonumber(data[1]); local updated = tonumber(data[2])
if tokens == nil then tokens = capacity; updated = now end
tokens = math.min(capacity, tokens + (now - updated) * rate)
local allowed = 0
if tokens >= cost then tokens = tokens - cost; allowed = 1 end
redis.call('HSET', key, 'tokens', tokens, 'updated', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) + 60)
local wait = 0
if allowed == 0 then wait = (cost - tokens) / rate end
return {allowed, tostring(wait)}
"""


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after_s: float = 0.0


class RateLimiter(Protocol):
    async def acquire(self, key: str, *, rate: float, capacity: int, cost: int = 1) -> RateDecision:
        """Try to take ``cost`` tokens from the bucket ``key``. Never waits; the caller decides (429 with Retry-After)."""
        ...


@dataclass
class InMemoryRateLimiter:
    buckets: dict[str, tuple[float, float]] = field(default_factory=dict)  # key -> (tokens, updated)

    async def acquire(self, key: str, *, rate: float, capacity: int, cost: int = 1) -> RateDecision:
        now = time.monotonic()
        tokens, updated = self.buckets.get(key, (float(capacity), now))
        tokens = min(float(capacity), tokens + (now - updated) * rate)
        if tokens >= cost:
            self.buckets[key] = (tokens - cost, now)
            return RateDecision(True)
        self.buckets[key] = (tokens, now)
        return RateDecision(False, retry_after_s=(cost - tokens) / rate)


class RedisRateLimiter:
    def __init__(self, client):
        self._redis = client
        self._script = None

    @classmethod
    def from_url(cls, url: str) -> "RedisRateLimiter":
        from redis.asyncio import Redis

        return cls(Redis.from_url(url, decode_responses=True))

    async def close(self) -> None:
        await self._redis.aclose()

    async def acquire(self, key: str, *, rate: float, capacity: int, cost: int = 1) -> RateDecision:
        allowed, wait = await self._redis.eval(_BUCKET_LUA, 1, f"ratelimit:{key}", rate, capacity, time.time(), cost)
        return RateDecision(bool(int(allowed)), retry_after_s=float(wait))
