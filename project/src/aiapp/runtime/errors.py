"""How a tool tells the runtime what kind of failure happened. The runtime decides what to do about it."""


class TransientToolError(Exception):
    """Network blip, rate limit, upstream restart. Retrying the same call may succeed."""


class ToolFailed(Exception):
    """The tool ran and could not do the job for a reason retrying will not fix. Reported to the model as an error result."""
