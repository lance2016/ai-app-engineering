"""Test first: write what you want, watch it fail, then make it pass.

The test below was written before slugify() existed. Read the test, then the code.

Run:  uv run python prerequisites/backend/02-testing/code/04_test_first.py
Expect: 4 passed.
"""

# %% imports
import re

import pytest


# %% step_1_the_tests_written_first
@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("Hello World", "hello-world"),
        ("  Trim  me ", "trim-me"),
        ("Python 3.12 rocks!", "python-3-12-rocks"),
        ("already-a-slug", "already-a-slug"),
    ],
)
def test_slugify(title: str, slug: str):
    assert slugify(title) == slug


# %% step_2_minimal_code_to_pass
def slugify(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return "-".join(words)


# %% run
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
