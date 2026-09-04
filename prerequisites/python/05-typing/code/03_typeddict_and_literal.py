"""TypedDict describes a dict's shape; Literal restricts a value to a few options.

Run:  uv run python prerequisites/python/05-typing/code/03_typeddict_and_literal.py
Expect: a dict that matches its TypedDict, and a function that only accepts
        certain strings (enforced by the type checker, not at runtime).
"""

# %% typeddict
from typing import Literal, TypedDict


class WeatherReply(TypedDict):
    city: str
    temp_c: float
    condition: Literal["sunny", "cloudy", "rain"]


reply: WeatherReply = {"city": "Shenzhen", "temp_c": 31.0, "condition": "sunny"}
print(reply["city"], reply["condition"])

# %% literal
Unit = Literal["celsius", "fahrenheit"]


def convert(temp: float, unit: Unit) -> float:
    return temp if unit == "celsius" else temp * 9 / 5 + 32


print(convert(31, "celsius"), convert(31, "fahrenheit"))

# %% runtime_does_not_check
print(convert(31, "kelvin"))  # runs! only pyright/mypy would flag this line
