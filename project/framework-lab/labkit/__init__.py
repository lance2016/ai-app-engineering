"""Shared pieces of the Framework Lab: the runtime protocol every implementation adapts to, and the scenarios that drive them."""

from labkit.protocol import LabEvent, LabRuntime, NotSupported, RunOutcome

__all__ = ["LabEvent", "LabRuntime", "NotSupported", "RunOutcome"]
