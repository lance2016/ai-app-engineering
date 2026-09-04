"""Custom exceptions name your failures; finally cleans up no matter what.

Run:  uv run python prerequisites/python/03-modules-errors-and-logging/code/03_custom_exception_and_finally.py
Expect: the full try / except / else / finally order printed for a success
        and for a failure.
"""


# %% custom_exception
class PaymentError(Exception):
    """Base class for everything that can go wrong with a payment."""


class InsufficientFunds(PaymentError):
    def __init__(self, needed: float, available: float):
        super().__init__(f"need {needed}, have {available}")
        self.needed = needed
        self.available = available


# %% try_except_else_finally
def pay(amount: float, balance: float) -> None:
    print(f"-- paying {amount} with balance {balance}")
    try:
        if amount > balance:
            raise InsufficientFunds(amount, balance)
        print("  try: charged")
    except InsufficientFunds as exc:
        print("  except:", exc, "| short by", exc.needed - exc.available)
    else:
        print("  else: only runs when nothing was raised")
    finally:
        print("  finally: always runs, e.g. close a connection")


pay(30, 100)
pay(300, 100)

# %% catch_the_family
try:
    raise InsufficientFunds(1, 0)
except PaymentError as exc:  # the parent class catches all its children
    print("caught via parent class:", type(exc).__name__)
