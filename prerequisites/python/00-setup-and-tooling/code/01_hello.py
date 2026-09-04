"""Your first script: print a line, then prove which Python ran it.

Run:  uv run python prerequisites/python/00-setup-and-tooling/code/01_hello.py
Expect: a greeting, the Python version (3.12.x), and a path that contains ".venv".
"""

# %% hello
print("Hello from Python!")

# %% which_python
import sys

print("Python version:", sys.version.split()[0])
print("Interpreter path:", sys.executable)
