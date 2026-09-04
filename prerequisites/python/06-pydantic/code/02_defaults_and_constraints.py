"""Optional fields, defaults, and value constraints with Field.

Run:  uv run python prerequisites/python/06-pydantic/code/02_defaults_and_constraints.py
Expect: a product with defaults filled in, then a constraint error for a negative price.
"""

# %% imports
from pydantic import BaseModel, Field, ValidationError


# %% define
class Product(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    price: float = Field(gt=0, description="in yuan")
    tags: list[str] = []  # pydantic copies this per instance; safe here
    note: str | None = None  # optional: may be missing or null


# %% defaults
p = Product(name="Tea", price=12.5)
print(p)
print(f"tags is its own list: {p.tags is Product(name='X', price=1).tags}")  # False

# %% constraint_error
try:
    Product(name="", price=-1)
except ValidationError as exc:
    for err in exc.errors():
        print(f"{err['loc'][0]}: {err['msg']}")
