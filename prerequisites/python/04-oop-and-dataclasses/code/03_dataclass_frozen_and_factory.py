"""Two dataclass options you will meet constantly: frozen=True and default_factory.

Run:  uv run python prerequisites/python/04-oop-and-dataclasses/code/03_dataclass_frozen_and_factory.py
Expect: a frozen instance refuses changes; a shared-list bug is shown and fixed.
"""

# %% frozen
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


call = ToolCall("get_weather", {"city": "Shenzhen"})
try:
    call.name = "delete_everything"
except Exception as exc:  # FrozenInstanceError
    print(type(exc).__name__ + ":", exc)


# %% default_factory
@dataclass
class Thread:
    events: list[str] = field(default_factory=list)  # a NEW list per instance


t1, t2 = Thread(), Thread()
t1.events.append("hello")
print("t1:", t1.events, "| t2:", t2.events)  # t2 stays empty

# %% why_not_a_plain_default
try:
    @dataclass
    class Broken:
        events: list[str] = []  # Python refuses: one list would be shared by all instances
except ValueError as exc:
    print("ValueError:", exc)
