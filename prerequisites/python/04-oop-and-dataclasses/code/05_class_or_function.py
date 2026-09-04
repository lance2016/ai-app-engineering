"""When to write a class and when a function is enough.

Run:  uv run python prerequisites/python/04-oop-and-dataclasses/code/05_class_or_function.py
Expect: the same job done both ways, with the rule of thumb printed at the end.
"""

# %% function_is_enough
def word_count(text: str) -> int:
    return len(text.split())


print("function:", word_count("the quick brown fox"))


# %% class_when_state_must_persist
class RunningWordCount:
    def __init__(self) -> None:
        self.total = 0

    def feed(self, text: str) -> None:
        self.total += len(text.split())


counter = RunningWordCount()
counter.feed("the quick brown fox")
counter.feed("jumps over")
print("class:", counter.total)

# %% rule_of_thumb
print("No state between calls -> function. State that several methods share -> class.")
print("Just a bundle of fields -> @dataclass, not a hand-written class.")
