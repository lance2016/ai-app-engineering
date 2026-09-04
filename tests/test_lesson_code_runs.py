"""Smoke test: every lesson code sample runs to completion without an API key.

Run:  uv run pytest
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = sorted(
    p for pattern in ("lessons/*/code/*.py", "prerequisites/*/*/code/*.py", "project/*/code/*.py") for p in ROOT.glob(pattern)
)


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: str(p.relative_to(ROOT)))
def test_sample_runs(sample: Path, tmp_path: Path) -> None:
    env = {**os.environ, "MODEL_PROVIDER": "fake", "CHECKPOINT_DIR": str(tmp_path)}
    result = subprocess.run([sys.executable, str(sample)], capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
