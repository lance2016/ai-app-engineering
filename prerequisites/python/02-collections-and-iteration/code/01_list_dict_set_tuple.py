"""The four built-in containers and when to reach for each.

Run:  uv run python prerequisites/python/02-collections-and-iteration/code/01_list_dict_set_tuple.py
Expect: each container printed after a typical operation.
"""

# %% list_ordered_changeable
tasks = ["buy milk", "call mom"]
tasks.append("write report")
tasks[0] = "buy oat milk"
print("list:", tasks, "| first:", tasks[0], "| count:", len(tasks))

# %% dict_lookup_by_key
user = {"name": "Lance", "city": "Shenzhen"}
user["age"] = 30
print("dict:", user, "| city:", user["city"])
print("missing key with .get:", user.get("email"), "| default:", user.get("email", "n/a"))

# %% set_unique_unordered
tags = {"python", "ai", "python", "agent"}
tags.add("rag")
print("set:", tags, "| has ai?", "ai" in tags)

# %% tuple_fixed
point = (3, 4)
x, y = point  # unpacking
print("tuple:", point, "| x =", x, "y =", y)
try:
    point[0] = 9
except TypeError as exc:
    print("TypeError:", exc)
