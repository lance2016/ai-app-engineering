"""Stop conditions the runtime owns: steps, tokens, wall-clock. The model never decides when to stop."""

import time
from dataclasses import dataclass, field
from enum import StrEnum


class StopReason(StrEnum):
    FINISHED = "finished"  # the model answered without asking for a tool
    PAUSED = "paused"  # waiting for a human: a question or a confirmation
    STEP_LIMIT = "step_limit"
    TOKEN_BUDGET = "token_budget"
    TIME_BUDGET = "time_budget"
    OFF_TRACK = "off_track"  # the model repeated itself after a warning; a person should look
    MODEL_TIMEOUT = "model_timeout"
    PROVIDER_ERROR = "provider_error"


@dataclass
class Budget:
    max_steps: int = 10
    max_tokens: int = 50_000
    max_seconds: float = 120.0
    steps: int = 0
    tokens: int = 0
    started: float = field(default_factory=time.monotonic)

    def start(self) -> None:
        self.started = time.monotonic()

    def charge(self, *, tokens: int) -> StopReason | None:
        """Record one model call and return the first exhausted budget, if any."""
        self.steps += 1
        self.tokens += tokens
        if self.tokens > self.max_tokens:
            return StopReason.TOKEN_BUDGET
        if time.monotonic() - self.started > self.max_seconds:
            return StopReason.TIME_BUDGET
        if self.steps >= self.max_steps:
            return StopReason.STEP_LIMIT
        return None

    def snapshot(self) -> dict[str, float | int]:
        return {"steps": self.steps, "tokens": self.tokens, "elapsed_s": round(time.monotonic() - self.started, 3)}
