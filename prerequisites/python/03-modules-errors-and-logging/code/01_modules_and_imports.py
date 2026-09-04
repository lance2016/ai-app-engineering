"""Modules and packages: split code into files and pull it back with import.

Run:  uv run python prerequisites/python/03-modules-errors-and-logging/code/01_modules_and_imports.py
Expect: areas computed by functions that live in the `shapes/` folder next to
        this file, plus three ways of writing an import.
"""

# %% standard_library_imports
import math  # whole module, use as math.pi
from pathlib import Path  # one name out of a module

print("pi:", round(math.pi, 4), "| this file:", Path(__file__).name)

# %% your_own_package
import shapes  # the folder `shapes/` next to this script, found via sys.path[0]
from shapes.area import rectangle_area

print("circle:", round(shapes.circle_area(2), 2))
print("rectangle:", rectangle_area(3, 4))

# %% alias
import shapes.area as area_tools

print("same function?", area_tools.rectangle_area is rectangle_area)
