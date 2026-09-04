"""Ask for JSON, validate it, and treat a parse failure as something the model can fix.

The Pydantic model generates the JSON Schema you show the model *and* validates
what comes back. When validation fails the error text goes back as the next
user turn; most models correct themselves on the second try. The runtime never
patches the JSON by hand.

Run:  uv run python lessons/02-model-api-structured-output-streaming/code/02_structured_output.py
      INJECT_BAD_JSON=1 uv run python lessons/02-model-api-structured-output-streaming/code/02_structured_output.py
      MODEL_PROVIDER=deepseek uv run python lessons/02-model-api-structured-output-streaming/code/02_structured_output.py
Expect: a validated Invoice object. With injection the first reply is broken
        (wrong type, missing field), the error is fed back, the second reply passes.
"""

# %% imports
import asyncio
import json
import os

from pydantic import BaseModel, Field, ValidationError

from aiapp import FakeAdapter, Message, ModelResponse, get_adapter

INJECT_BAD_JSON = os.environ.get("INJECT_BAD_JSON") == "1"

TEXT = "Invoice #4471 from Acme Ltd, dated 2026-08-30. Total 1,280.50 EUR. Items: 2x desk lamp, 1x cable set."


# %% schema
class LineItem(BaseModel):
    description: str
    quantity: int = Field(ge=1)


class Invoice(BaseModel):
    number: str
    vendor: str
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    total: float
    currency: str = Field(min_length=3, max_length=3)
    items: list[LineItem]


SYSTEM = (
    "Extract the invoice as JSON matching this JSON Schema exactly. Output only the JSON object.\n"
    + json.dumps(Invoice.model_json_schema(), ensure_ascii=False)
)


# %% extract_with_repair_loop
async def extract(model, text: str, *, max_attempts: int = 3) -> Invoice:
    messages = [Message(role="system", content=SYSTEM), Message(role="user", content=text)]
    for attempt in range(1, max_attempts + 1):
        reply = await model.complete(messages)
        try:
            invoice = Invoice.model_validate_json(_strip_fences(reply.content))
            print(f"attempt {attempt}: valid")
            return invoice
        except (ValidationError, ValueError) as exc:
            detail = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) else str(exc)
            print(f"attempt {attempt}: invalid -> {detail}")
            messages.append(Message(role="assistant", content=reply.content))
            messages.append(Message(role="user", content=f"That was not valid: {detail}. Return only the corrected JSON."))
    raise RuntimeError("model never produced valid JSON")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text


# %% fake_script
GOOD = json.dumps({"number": "4471", "vendor": "Acme Ltd", "date": "2026-08-30", "total": 1280.5, "currency": "EUR",
                   "items": [{"description": "desk lamp", "quantity": 2}, {"description": "cable set", "quantity": 1}]})
BAD = json.dumps({"number": 4471, "vendor": "Acme Ltd", "date": "30/08/2026", "total": "1,280.50", "currency": "EUR", "items": []})


def build_model():
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    if provider != "fake":
        return get_adapter(provider)
    script = [ModelResponse(content=BAD), ModelResponse(content=GOOD)] if INJECT_BAD_JSON else [ModelResponse(content=GOOD)]
    return FakeAdapter(script=script)


# %% run
async def main() -> None:
    invoice = await extract(build_model(), TEXT)
    print(f"\n{invoice!r}")
    print(f"\nschema shown to the model is {len(SYSTEM)} chars; validation used the same Pydantic model. one source of truth.")


if __name__ == "__main__":
    asyncio.run(main())
