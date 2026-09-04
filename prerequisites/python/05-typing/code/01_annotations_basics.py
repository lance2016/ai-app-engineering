"""Type annotations: say what goes in and what comes out.

Run:  uv run python prerequisites/python/05-typing/code/01_annotations_basics.py
Expect: the same function with and without annotations, and the annotations
        read back at runtime.
"""


# %% without_annotations
def area(w, h):
    return w * h


# %% with_annotations
def area_typed(width: float, height: float) -> float:
    return width * height


print(area(3, 4), area_typed(3, 4))

# %% annotations_are_data
print("annotations:", area_typed.__annotations__)
total: int = 0  # variables can be annotated too
print("total is", total)
