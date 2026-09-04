"""Make decisions with if / elif / else; repeat with for and while.

Run:  uv run python prerequisites/python/01-python-basics/code/03_conditions_and_loops.py
Expect: a temperature label, then a countdown, then a filtered list.
"""

# %% if_elif_else
temp = 31
if temp >= 35:
    label = "hot"
elif temp >= 25:
    label = "warm"
else:
    label = "cool"
print(f"{temp} degrees is {label}")

# %% for_loop
for number in range(3, 0, -1):
    print("countdown:", number)
print("go!")

# %% while_loop
attempts = 0
while attempts < 3:
    attempts += 1
    print("attempt", attempts)

# %% loop_with_condition
words = ["apple", "kiwi", "banana", "fig"]
short_words = []
for word in words:
    if len(word) <= 4:
        short_words.append(word)
print("short words:", short_words)
