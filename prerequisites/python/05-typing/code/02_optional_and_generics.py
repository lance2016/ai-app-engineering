"""Optional values and containers of a known type.

Run:  uv run python prerequisites/python/05-typing/code/02_optional_and_generics.py
Expect: a function that may return None, handled correctly, and typed containers.
"""


# %% may_return_none
def find_user(users: dict[str, int], name: str) -> int | None:
    """Return the user's age, or None when unknown. `int | None` is the modern spelling of Optional[int]."""
    return users.get(name)


users = {"lance": 30, "amy": 10}
age = find_user(users, "bob")
if age is None:
    print("bob not found")
else:
    print("bob is", age + 1)  # safe: inside this branch age is an int

# %% typed_containers
scores: list[float] = [0.9, 0.7]
by_name: dict[str, list[str]] = {"lance": ["python", "ai"]}
pair: tuple[str, int] = ("amy", 10)
print(scores, by_name, pair)


# %% functions_that_take_functions
from collections.abc import Callable


def apply_twice(func: Callable[[int], int], value: int) -> int:
    return func(func(value))


print(apply_twice(lambda x: x * 2, 5))
