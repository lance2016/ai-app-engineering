"""One module inside the `shapes` package."""

import math


def circle_area(radius: float) -> float:
    return math.pi * radius**2


def rectangle_area(width: float, height: float) -> float:
    return width * height
