"""Define a model, validate good input, read a validation error.

Run:  uv run python prerequisites/python/06-pydantic/code/01_define_and_validate.py
Expect: one User printed, then the two errors from the bad input, one per line.
"""

# %% imports
from pydantic import BaseModel, ValidationError


# %% define
class User(BaseModel):
    name: str
    age: int
    email: str


# %% validate_good
good = User(name="Ada", age=36, email="ada@example.com")
print(good)
print(f"age is a real int: {good.age + 1}")

# %% validate_bad
try:
    User(name="Bob", age="thirty", email=None)
except ValidationError as exc:
    print(f"\n{exc.error_count()} errors:")
    for err in exc.errors():
        print(f"  field={err['loc'][0]!r:8} problem={err['msg']!r} got={err['input']!r}")
