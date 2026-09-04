"""Variables hold values; every value has a type.

Run:  uv run python prerequisites/python/01-python-basics/code/01_variables_and_types.py
Expect: four values with their types, then a type conversion.
"""

# %% four_basic_types
name = "Aime"
age = 10
height_m = 1.32
is_robot = True

for value in (name, age, height_m, is_robot):
    print(repr(value), "->", type(value).__name__)

# %% types_matter
user_input = "42"  # what you read from a keyboard or a file is always text
print(user_input + "1")  # text + text glues them: "421"
print(int(user_input) + 1)  # convert first, then it is arithmetic: 43
