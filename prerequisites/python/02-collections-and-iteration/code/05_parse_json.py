"""JSON is how programs exchange data. In Python it becomes dicts and lists.

Run:  uv run python prerequisites/python/02-collections-and-iteration/code/05_parse_json.py
Expect: fields pulled out of a parsed JSON reply, a nested value, and the
        dict written back out as JSON text.
"""

# %% parse
import json

raw = '{"city": "Shenzhen", "temp_c": 31, "forecast": [{"day": "Mon", "high": 33}, {"day": "Tue", "high": 30}]}'
data = json.loads(raw)
print(type(data).__name__, "with keys:", list(data))

# %% walk_the_structure
print("city:", data["city"])
print("first forecast day:", data["forecast"][0]["day"])
highs = [day["high"] for day in data["forecast"]]
print("highs:", highs, "| max:", max(highs))

# %% write_back
data["source"] = "demo"
print(json.dumps(data, indent=2, ensure_ascii=False))
