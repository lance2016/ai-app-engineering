"""@dataclass writes __init__, __repr__ and __eq__ for you.

Run:  uv run python prerequisites/python/04-oop-and-dataclasses/code/02_dataclass.py
Expect: the same class written by hand and with @dataclass behave the same,
        but the dataclass version is a third of the code.
"""

# %% by_hand
class MessageByHand:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def __repr__(self) -> str:
        return f"MessageByHand(role={self.role!r}, content={self.content!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MessageByHand) and (self.role, self.content) == (other.role, other.content)


# %% with_dataclass
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str = ""  # defaults work like function defaults


# %% same_behaviour
a = Message("user", "hi")
b = Message("user", "hi")
print(a)
print("equal?", a == b)
print("by hand:", MessageByHand("user", "hi"))
print("default content:", Message("assistant"))
