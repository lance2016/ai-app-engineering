"""Functions package a piece of logic so you can reuse and name it.

Run:  uv run python prerequisites/python/01-python-basics/code/04_functions_and_scope.py
Expect: two greetings, a computed total, and a demonstration that a variable
        created inside a function does not exist outside it.
"""


# %% define_and_call
def greet(name: str, excited: bool = False) -> str:
    """Return a greeting. `excited` has a default, so it is optional."""
    ending = "!" if excited else "."
    return f"Hello, {name}{ending}"


print(greet("Lance"))
print(greet("Lance", excited=True))


# %% return_values
def total_price(prices: list[float], discount: float = 0.0) -> float:
    subtotal = sum(prices)
    return subtotal * (1 - discount)


print("total:", total_price([10.0, 20.0, 5.0], discount=0.1))


# %% scope
def make_message() -> str:
    inner = "I only exist inside this function"
    return inner


print(make_message())
try:
    print(inner)  # noqa: F821 - deliberately wrong
except NameError as exc:
    print("NameError:", exc)
