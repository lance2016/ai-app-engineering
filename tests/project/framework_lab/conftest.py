"""Conformance tests run every scenario against every implementation. Frameworks that are not installed are skipped."""

import importlib

import pytest

from labkit.scenarios import SCENARIOS

IMPLEMENTATIONS = {
    "baseline": "baseline.adapter",
    "langgraph": "langgraph_impl.adapter",
    "openai_agents": "openai_agents_impl.adapter",
    "claude_agent_sdk": "claude_agent_sdk_impl.adapter",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(params=list(IMPLEMENTATIONS))
def factory(request):
    module_name = IMPLEMENTATIONS[request.param]
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        pytest.skip(f"{request.param}: {exc} (uv sync --group frameworks)")
    return module.make_runtime


@pytest.fixture(params=list(SCENARIOS))
def scenario(request):
    return SCENARIOS[request.param]
