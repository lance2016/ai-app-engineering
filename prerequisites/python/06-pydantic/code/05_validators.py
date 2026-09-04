"""Custom rules: field_validator for one field, model_validator for cross-field checks.

Run:  uv run python prerequisites/python/06-pydantic/code/05_validators.py
Expect: a normalised email, then two custom error messages.
"""

# %% imports
from pydantic import BaseModel, ValidationError, field_validator, model_validator


# %% define
class Booking(BaseModel):
    email: str
    start: int  # hour of day
    end: int

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("email must contain @")
        return v

    @model_validator(mode="after")
    def end_after_start(self) -> "Booking":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


# %% good
print(Booking(email="  Ada@Example.com ", start=9, end=11))

# %% bad
for data in ({"email": "nope", "start": 9, "end": 11}, {"email": "a@b.c", "start": 11, "end": 9}):
    try:
        Booking(**data)
    except ValidationError as exc:
        print(exc.errors()[0]["msg"])
