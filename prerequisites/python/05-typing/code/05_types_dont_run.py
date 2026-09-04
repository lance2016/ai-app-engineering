"""Annotations do not change how Python runs. A checker is a separate tool.

Run:  uv run python prerequisites/python/05-typing/code/05_types_dont_run.py
      uvx pyright prerequisites/python/05-typing/code/05_types_dont_run.py   # the checker complains
Expect: the script runs and prints a wrong-typed result without error;
        pyright reports the mismatch.
"""


# %% wrong_type_still_runs
def double(n: int) -> int:
    return n * 2


print(double("ab"))  # annotation says int, we pass str: Python happily returns "abab"

# %% the_checker_is_a_separate_step
print("Run `uvx pyright <this file>` to see the type error that Python ignored.")
