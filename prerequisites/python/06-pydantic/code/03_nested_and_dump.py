"""Nested models, and moving between models, dicts and JSON.

Run:  uv run python prerequisites/python/06-pydantic/code/03_nested_and_dump.py
Expect: an order built from a raw dict, dumped back to a dict and to JSON, then re-parsed.
"""

# %% imports
from pydantic import BaseModel


# %% define
class Item(BaseModel):
    sku: str
    qty: int


class Order(BaseModel):
    order_id: str
    items: list[Item]
    paid: bool = False


# %% from_dict
raw = {"order_id": "o_1", "items": [{"sku": "A1", "qty": 2}, {"sku": "B7", "qty": "1"}]}
order = Order.model_validate(raw)  # "1" becomes 1: lax mode coerces compatible types
print(order.items[1].qty + 1)

# %% to_dict_and_json
print(order.model_dump())
text = order.model_dump_json()
print(text)

# %% back_from_json
again = Order.model_validate_json(text)
print(f"round trip equal: {again == order}")
