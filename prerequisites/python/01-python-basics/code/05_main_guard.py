"""Why every script ends with `if __name__ == "__main__":`.

Run:  uv run python prerequisites/python/01-python-basics/code/05_main_guard.py
Expect: the module name is "__main__" when run directly, so main() runs.
        If another file imported this one, __name__ would be the file name
        and main() would NOT run, but `celsius_to_fahrenheit` would be usable.
"""


# %% reusable_part
def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


# %% script_part
def main() -> None:
    print("__name__ is", __name__)
    print("31 C =", celsius_to_fahrenheit(31), "F")


if __name__ == "__main__":
    main()
