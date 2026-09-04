"""A script can take input from the command line.

Run:  uv run python prerequisites/python/00-setup-and-tooling/code/03_script_with_input.py
      uv run python prerequisites/python/00-setup-and-tooling/code/03_script_with_input.py Lance
Expect: "Hello, world!" without an argument, "Hello, Lance!" with one.
"""

# %% read_argument
import sys

name = sys.argv[1] if len(sys.argv) > 1 else "world"

# %% greet
print(f"Hello, {name}!")
print("Arguments received:", sys.argv[1:])
