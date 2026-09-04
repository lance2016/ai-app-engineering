"""Duck typing: if it has the method, it works. Protocol writes that down.

Run:  uv run python prerequisites/python/04-oop-and-dataclasses/code/04_protocol_duck_typing.py
Expect: two unrelated classes both accepted by the same function because both
        have a `speak()` method; a third one rejected at runtime.
"""

# %% two_unrelated_classes
class Robot:
    def speak(self) -> str:
        return "beep"


class Human:
    def speak(self) -> str:
        return "hello"


class Rock:
    pass


# %% a_protocol_names_the_shape
from typing import Protocol, runtime_checkable


@runtime_checkable
class Speaker(Protocol):
    def speak(self) -> str: ...


def announce(who: Speaker) -> None:
    print(type(who).__name__, "says", who.speak())


# %% it_just_works
announce(Robot())
announce(Human())
print("Rock is a Speaker?", isinstance(Rock(), Speaker))
try:
    announce(Rock())
except AttributeError as exc:
    print("AttributeError:", exc)
