"""model_json_schema(): the same class describes data to Python and to a model.

Run:  uv run python prerequisites/python/06-pydantic/code/04_json_schema.py
Expect: a JSON Schema with properties, required list and the description from Field.
"""

# %% imports
import json
from typing import Literal

from pydantic import BaseModel, Field


# %% define
class GetWeather(BaseModel):
    """Current weather for a city."""

    city: str = Field(description="City name, e.g. Shenzhen")
    unit: Literal["celsius", "fahrenheit"] = "celsius"


# %% schema
schema = GetWeather.model_json_schema()
print(json.dumps(schema, indent=2, ensure_ascii=False))

# %% why_it_matters
print("\nrequired:", schema["required"])  # only city; unit has a default
print("this dict is what lesson 05 passes to the model as a tool's parameters")
