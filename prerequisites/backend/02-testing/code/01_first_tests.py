"""A function and its tests in one file. pytest finds functions named test_*.

Run:  uv run python prerequisites/backend/02-testing/code/01_first_tests.py
Expect: pytest output with 3 passed.
"""

# %% code_under_test
def word_count(text: str) -> int:
    return len(text.split())


# %% tests
def test_counts_words():
    assert word_count("hello world") == 2


def test_empty_string():
    assert word_count("") == 0


def test_extra_spaces_do_not_count():
    assert word_count("  a   b  ") == 2


# %% run
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
