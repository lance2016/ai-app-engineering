"""A class is a blueprint; an instance is one thing built from it.

Run:  uv run python prerequisites/python/04-oop-and-dataclasses/code/01_class_and_instance.py
Expect: two counters that keep separate totals, and a method that uses self.
"""


# %% define_a_class
class Counter:
    def __init__(self, name: str) -> None:
        self.name = name  # attributes live on self, one set per instance
        self.total = 0

    def add(self, amount: int = 1) -> None:
        self.total += amount

    def describe(self) -> str:
        return f"{self.name}: {self.total}"


# %% two_instances_two_states
tokens_in = Counter("input tokens")
tokens_out = Counter("output tokens")
tokens_in.add(120)
tokens_in.add(80)
tokens_out.add(35)
print(tokens_in.describe())
print(tokens_out.describe())

# %% what_self_is
print("same object?", tokens_in is tokens_out)
print("type:", type(tokens_in).__name__)
