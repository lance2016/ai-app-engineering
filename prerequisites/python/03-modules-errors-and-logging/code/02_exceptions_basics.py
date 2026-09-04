"""Errors are values you can catch. Catch the specific one, not everything.

Run:  uv run python prerequisites/python/03-modules-errors-and-logging/code/02_exceptions_basics.py
Expect: three handled errors with their messages, and the program keeps going.
"""

# %% catch_a_specific_error
try:
    number = int("forty-two")
except ValueError as exc:
    print("ValueError:", exc)

# %% different_errors_different_handlers
data = {"name": "Lance"}
try:
    print(data["age"])
except KeyError as exc:
    print("KeyError: missing key", exc)

try:
    print(10 / 0)
except ZeroDivisionError as exc:
    print("ZeroDivisionError:", exc)

# %% raise_your_own
def withdraw(balance: float, amount: float) -> float:
    if amount > balance:
        raise ValueError(f"cannot withdraw {amount}, balance is {balance}")
    return balance - amount


try:
    withdraw(50, 80)
except ValueError as exc:
    print("raised on purpose:", exc)
print("program still running")
