"""One test = one scenario on one implementation. A NotSupported becomes an xfail with the framework's reason, and lands on the scorecard."""

import pytest

from labkit.protocol import NotSupported

pytestmark = pytest.mark.anyio


async def test_scenario(factory, scenario, tmp_path) -> None:
    try:
        await scenario(factory, tmp_path)
    except NotSupported as exc:
        pytest.xfail(f"not supported: {exc}")
