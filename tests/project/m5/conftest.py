import pytest

from aiapp.ops import telemetry
from tests.project.m2.conftest import postgres_url, redis_url  # noqa: F401  (session fixtures shared)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _tracing_in_memory():
    telemetry.setup_tracing(in_memory=True)
    telemetry.clear_recorded_spans()
    yield
