"""Redis as the coordination store: idempotency claims and run locks. Never the source of truth."""

from redis.asyncio import Redis

_RELEASE_IF_OWNER = """
if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end
"""


class RedisKeyValueStore:
    def __init__(self, client: Redis):
        self._redis = client

    @classmethod
    def from_url(cls, url: str) -> "RedisKeyValueStore":
        return cls(Redis.from_url(url, decode_responses=True))

    async def close(self) -> None:
        await self._redis.aclose()

    async def claim(self, key: str, value: str, ttl_s: int) -> bool:
        return bool(await self._redis.set(key, value, nx=True, ex=ttl_s))

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl_s: int) -> None:
        await self._redis.set(key, value, ex=ttl_s)

    async def release(self, key: str, value: str) -> bool:
        return bool(await self._redis.eval(_RELEASE_IF_OWNER, 1, key, value))
