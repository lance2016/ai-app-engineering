"""Where does the code run from, and what does it see?

Run:  uv run python prerequisites/python/00-setup-and-tooling/code/02_where_am_i.py
Expect: the working directory, the folder this script lives in, and whether a
        virtual environment is active (it should be, thanks to `uv run`).
"""

# %% imports
import os
import sys
from pathlib import Path

# %% working_directory
print("Working directory:", os.getcwd())
print("This script lives in:", Path(__file__).parent)

# %% virtual_environment
in_venv = sys.prefix != sys.base_prefix
print("Inside a virtual environment:", in_venv)
print("Environment root:", sys.prefix)
