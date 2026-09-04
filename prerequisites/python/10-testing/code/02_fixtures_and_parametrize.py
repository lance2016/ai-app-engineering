"""Fixtures give tests a ready-made object; parametrize runs one test on many inputs.

Run:  uv run python prerequisites/python/10-testing/code/02_fixtures_and_parametrize.py
Expect: 6 passed (1 fixture test + 5 parametrized cases).
"""

# %% imports
import pytest


# %% code_under_test
class Cart:
    def __init__(self) -> None:
        self.items: dict[str, int] = {}

    def add(self, sku: str, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.items[sku] = self.items.get(sku, 0) + qty

    def total_qty(self) -> int:
        return sum(self.items.values())


# %% fixture
@pytest.fixture
def cart() -> Cart:  # a fresh Cart for every test that asks for it
    c = Cart()
    c.add("tea", 2)
    return c


def test_fixture_gives_prefilled_cart(cart: Cart):
    assert cart.total_qty() == 2


# %% parametrize
@pytest.mark.parametrize(
    ("sku", "qty", "expected"),
    [("tea", 1, 3), ("coffee", 1, 3), ("coffee", 5, 7), ("tea", 3, 5), ("milk", 10, 12)],
)
def test_add_many_cases(cart: Cart, sku: str, qty: int, expected: int):
    cart.add(sku, qty)
    assert cart.total_qty() == expected


# %% run
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
