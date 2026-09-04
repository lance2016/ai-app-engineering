"""A tiny package: a folder with __init__.py. `import shapes` reads this file."""

from shapes.area import circle_area, rectangle_area

__all__ = ["circle_area", "rectangle_area"]
