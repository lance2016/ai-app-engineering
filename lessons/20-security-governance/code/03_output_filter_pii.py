"""Two filters on the way out: redact PII, and never echo the system prompt.

Tool results can carry personal data the user is not entitled to see, and a
model can be talked into printing its own instructions. Both are handled by
deterministic filters at the boundary, applied to tool results before they
enter the context and to the final answer before it leaves.

Run:  uv run python lessons/20-security-governance/code/03_output_filter_pii.py
      INJECT_NO_FILTER=1 uv run python lessons/20-security-governance/code/03_output_filter_pii.py
Expect: filtered output masks phone numbers, emails and ID numbers and refuses
        to leak the system prompt. Unfiltered output shows everything.
"""

# %% imports
import os
import re

INJECT_NO_FILTER = os.environ.get("INJECT_NO_FILTER") == "1"

SYSTEM_PROMPT = "You are Ava, a support agent. Internal escalation code: ESC-7741."
CANARY = "ESC-7741"  # a token that only appears in the system prompt


# %% pii_patterns
PII_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone_cn": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_cn": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for label, pattern in PII_PATTERNS.items():
        text, n = pattern.subn(f"<{label}>", text)
        if n:
            counts[label] = n
    return text, counts


# %% system_prompt_leak_check
def leaks_system_prompt(text: str) -> bool:
    return CANARY in text or "Internal escalation code" in text


# %% boundary_filter
def filter_outbound(text: str) -> str:
    if INJECT_NO_FILTER:
        return text
    if leaks_system_prompt(text):
        return "I can't share my internal instructions, but I'm happy to help with your request."
    redacted, counts = redact(text)
    if counts:
        print(f"  redacted: {counts}")
    return redacted


# %% run
def main() -> None:
    tool_result = "Customer: Li Wei, phone 13812345678, email li.wei@example.com, id 110101199001011234, order #A17."
    model_answer_1 = f"The customer Li Wei ({tool_result.split('phone ')[1].split(',')[0]}) has order #A17 pending."
    model_answer_2 = f"Sure! My instructions say: {SYSTEM_PROMPT}"

    print("tool result into context :", filter_outbound(tool_result))
    print("final answer 1 to user   :", filter_outbound(model_answer_1))
    print("final answer 2 to user   :", filter_outbound(model_answer_2))


if __name__ == "__main__":
    main()
