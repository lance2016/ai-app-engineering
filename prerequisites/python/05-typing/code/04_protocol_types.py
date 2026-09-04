"""Protocol from the type checker's point of view: structural typing.

Run:  uv run python prerequisites/python/05-typing/code/04_protocol_types.py
Expect: two adapters with the same method shape both satisfy the Protocol;
        the checker (not Python) would reject the third.
"""

# %% protocol
from typing import Protocol


class Greeter(Protocol):
    def greet(self, name: str) -> str: ...


class Formal:
    def greet(self, name: str) -> str:
        return f"Good day, {name}."


class Casual:
    def greet(self, name: str) -> str:
        return f"hey {name}"


class Silent:
    def wave(self) -> None: ...


# %% use_the_protocol_as_a_type
def welcome(greeter: Greeter, name: str) -> None:
    print(greeter.greet(name))


welcome(Formal(), "Lance")
welcome(Casual(), "Lance")
# welcome(Silent(), "Lance")  # pyright: "Silent" is incompatible with protocol "Greeter"
print("Silent would be rejected by the type checker; uncomment the line above and run pyright.")
