"""Assert that errors happen, and replace slow or external things with a mock.

Run:  uv run python prerequisites/python/10-testing/code/03_raises_and_mock.py
Expect: 3 passed; no real network call is made.
"""

# %% imports
import sys
from unittest.mock import patch

import pytest


# %% code_under_test
def fetch_price(sku: str) -> float:
    raise RuntimeError("this would call a real API; never run it in tests")


def price_with_tax(sku: str) -> float:
    if not sku:
        raise ValueError("sku required")
    return round(fetch_price(sku) * 1.13, 2)


# %% raises
def test_empty_sku_rejected():
    with pytest.raises(ValueError, match="sku required"):
        price_with_tax("")


# %% mock
def test_tax_applied_using_mocked_price():
    with patch.object(sys.modules[__name__], "fetch_price", return_value=100.0) as fake:
        assert price_with_tax("tea") == 113.0
        fake.assert_called_once_with("tea")


def test_mock_can_simulate_failure():
    with patch.object(sys.modules[__name__], "fetch_price", side_effect=TimeoutError("slow API")):
        with pytest.raises(TimeoutError):
            price_with_tax("tea")


# %% run
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
