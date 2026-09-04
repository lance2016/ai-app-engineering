"""When output varies (a model, randomness, time), test its shape and bounds, not its exact text.

Run:  uv run python prerequisites/backend/02-testing/code/05_testing_uncertain_output.py
Expect: 3 passed even though summarise() gives different text every run.
"""

# %% imports
import random

import pytest


# %% code_under_test
def summarise(text: str) -> dict:
    """Stands in for a model call: the wording changes, the contract must not."""
    openers = ["In short,", "Summary:", "Briefly,"]
    return {
        "summary": f"{random.choice(openers)} {text[:20]}...",
        "confidence": round(random.uniform(0.5, 1.0), 2),
        "source_chars": len(text),
    }


# %% tests_on_shape_and_bounds
TEXT = "The quick brown fox jumps over the lazy dog near the river bank."


def test_has_required_keys():
    out = summarise(TEXT)
    assert set(out) == {"summary", "confidence", "source_chars"}


def test_confidence_in_range():
    for _ in range(20):  # run many times; the bound must always hold
        assert 0.5 <= summarise(TEXT)["confidence"] <= 1.0


def test_summary_is_shorter_than_source():
    out = summarise(TEXT)
    assert len(out["summary"]) < out["source_chars"]


# %% run
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
