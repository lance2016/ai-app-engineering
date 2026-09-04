"""Undo is cheaper than confirmation, when the action allows it.

Reversible actions commit after a short grace window the user can cancel;
irreversible ones must be confirmed first (lesson 05's gate). The UI shows
the same "Undo" affordance either way, but the runtime decides which path
an action takes from its declared reversibility, never from the model.

Run:  uv run python lessons/22-product-design-ux/code/02_undo_window.py
      USER_UNDOES=1 uv run python lessons/22-product-design-ux/code/02_undo_window.py
Expect: the reversible action commits after the window (or is cancelled with
        injection); the irreversible one waits for explicit approval.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass

USER_UNDOES = os.environ.get("USER_UNDOES") == "1"
UNDO_WINDOW_S = 0.3


# %% action
@dataclass(frozen=True)
class Action:
    name: str
    reversible: bool
    undo_name: str = ""


@dataclass
class Outcome:
    action: Action
    committed: bool
    note: str


# %% runtime
async def perform(action: Action, *, approve: bool = True) -> Outcome:
    if action.reversible:
        print(f"  {action.name}: done. [Undo] available for {UNDO_WINDOW_S:.1f}s")
        try:
            await asyncio.wait_for(user_pressed_undo(), timeout=UNDO_WINDOW_S)
        except TimeoutError:
            return Outcome(action, True, "committed after undo window")
        print(f"  {action.undo_name}: reverted")
        return Outcome(action, False, "undone by user")
    print(f"  {action.name}: irreversible -> asking first")
    if not approve:
        return Outcome(action, False, "declined")
    return Outcome(action, True, "approved and committed")


async def user_pressed_undo() -> None:
    if not USER_UNDOES:
        await asyncio.sleep(10)  # never presses within the window
    await asyncio.sleep(0.1)


# %% run
async def main() -> None:
    plan = [
        Action("archive_conversation", reversible=True, undo_name="unarchive_conversation"),
        Action("send_payment", reversible=False),
    ]
    for action in plan:
        outcome = await perform(action, approve=True)
        print(f"  => {outcome.note}\n")


if __name__ == "__main__":
    asyncio.run(main())
