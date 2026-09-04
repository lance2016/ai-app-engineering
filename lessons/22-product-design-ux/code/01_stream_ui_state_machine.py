"""What the user sees is a state machine, not a string that grows.

A streaming AI reply passes through distinct states: waiting, streaming text,
running a tool, waiting for the user's confirmation, done, failed. Each state
has its own rendering and its own legal transitions. Modelling this explicitly
is what keeps the UI honest when a tool takes ten seconds or the connection
drops half-way.

Run:  uv run python lessons/22-product-design-ux/code/01_stream_ui_state_machine.py
      INJECT_DISCONNECT=1 uv run python lessons/22-product-design-ux/code/01_stream_ui_state_machine.py
Expect: a rendered frame per state; with injection the reply fails but the
        partial text the user already saw is kept, not blanked.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass, field
from enum import StrEnum

INJECT_DISCONNECT = os.environ.get("INJECT_DISCONNECT") == "1"


# %% states
class UIState(StrEnum):
    IDLE = "idle"
    WAITING = "waiting"  # request sent, nothing back yet -> show a spinner, allow cancel
    STREAMING = "streaming"  # text arriving -> append, allow stop
    TOOL_RUNNING = "tool_running"  # model is using a tool -> say which, keep prior text visible
    NEEDS_CONFIRMATION = "needs_confirmation"  # side effect pending -> show approve / decline
    DONE = "done"
    FAILED = "failed"


TRANSITIONS: dict[UIState, set[UIState]] = {
    UIState.IDLE: {UIState.WAITING},
    UIState.WAITING: {UIState.STREAMING, UIState.TOOL_RUNNING, UIState.NEEDS_CONFIRMATION, UIState.DONE, UIState.FAILED},
    UIState.STREAMING: {UIState.STREAMING, UIState.TOOL_RUNNING, UIState.NEEDS_CONFIRMATION, UIState.DONE, UIState.FAILED},
    UIState.TOOL_RUNNING: {UIState.STREAMING, UIState.NEEDS_CONFIRMATION, UIState.DONE, UIState.FAILED},
    UIState.NEEDS_CONFIRMATION: {UIState.TOOL_RUNNING, UIState.STREAMING, UIState.DONE, UIState.FAILED},
    UIState.DONE: {UIState.WAITING},
    UIState.FAILED: {UIState.WAITING},
}


@dataclass
class ReplyView:
    state: UIState = UIState.IDLE
    text: str = ""
    tool_label: str = ""
    pending_action: str = ""
    error: str = ""
    citations: list[str] = field(default_factory=list)

    def go(self, new: UIState) -> None:
        if new not in TRANSITIONS[self.state]:
            raise RuntimeError(f"illegal transition {self.state} -> {new}")
        self.state = new

    def render(self) -> str:
        """One frame, as a UI would draw it. Prior text always stays visible."""
        head = {
            UIState.IDLE: "",
            UIState.WAITING: "[ thinking...              (cancel) ]",
            UIState.STREAMING: "[ answering...             (stop)   ]",
            UIState.TOOL_RUNNING: f"[ using {self.tool_label}...   (cancel) ]",
            UIState.NEEDS_CONFIRMATION: f"[ confirm: {self.pending_action}?   (approve) (decline) ]",
            UIState.DONE: "[ done ] " + (f"sources: {', '.join(self.citations)}" if self.citations else ""),
            UIState.FAILED: f"[ failed: {self.error} ]  (retry)  -- partial answer kept below",
        }[self.state]
        body = self.text if self.text else "(no text yet)"
        return f"{head}\n  {body}"


# %% event_feed
async def events():
    """Stand-in for the SSE stream from lesson 07. Names match Thread event types."""
    yield ("run_started", {})
    yield ("assistant_delta", {"text": "Your order "})
    yield ("assistant_delta", {"text": "shipped yesterday"})
    yield ("tool_started", {"name": "track_parcel"})
    await asyncio.sleep(0.05)
    if INJECT_DISCONNECT:
        yield ("connection_lost", {"reason": "network"})
        return
    yield ("tool_result", {"content": "ETA Friday"})
    yield ("assistant_delta", {"text": " and should arrive Friday."})
    yield ("confirmation_requested", {"action": "send SMS with tracking link"})
    yield ("confirmation_given", {"approved": True})
    yield ("tool_started", {"name": "send_sms"})
    yield ("tool_result", {"content": "sent"})
    yield ("assistant_delta", {"text": " I've texted you the link."})
    yield ("run_finished", {"citations": ["order #4411", "carrier API"]})


# %% reducer
def apply(view: ReplyView, kind: str, data: dict) -> None:
    match kind:
        case "run_started":
            view.go(UIState.WAITING)
        case "assistant_delta":
            view.go(UIState.STREAMING)
            view.text += data["text"]
        case "tool_started":
            view.tool_label = data["name"]
            view.go(UIState.TOOL_RUNNING)
        case "tool_result":
            pass  # stay in TOOL_RUNNING until text or the next event moves us
        case "confirmation_requested":
            view.pending_action = data["action"]
            view.go(UIState.NEEDS_CONFIRMATION)
        case "confirmation_given":
            pass  # the next tool_started / delta moves the state
        case "run_finished":
            view.citations = data.get("citations", [])
            view.go(UIState.DONE)
        case "connection_lost":
            view.error = data["reason"]
            view.go(UIState.FAILED)


# %% run
async def main() -> None:
    view = ReplyView()
    async for kind, data in events():
        apply(view, kind, data)
        print(f"--- {kind}\n{view.render()}\n")
    print(f"final state={view.state} text_kept={bool(view.text)}")


if __name__ == "__main__":
    asyncio.run(main())
