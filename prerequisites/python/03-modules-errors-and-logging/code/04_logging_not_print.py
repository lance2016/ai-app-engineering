"""Use logging instead of print: levels, timestamps, and an off switch.

Run:  uv run python prerequisites/python/03-modules-errors-and-logging/code/04_logging_not_print.py
      LOG_LEVEL=DEBUG uv run python prerequisites/python/03-modules-errors-and-logging/code/04_logging_not_print.py
Expect: INFO and above by default; the DEBUG line appears only with LOG_LEVEL=DEBUG.
"""

# %% configure_once
import logging
import os

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
log = logging.getLogger("demo")

# %% levels
log.debug("only visible when you ask for it: payload=%s", {"x": 1})
log.info("normal progress message")
log.warning("something odd but we can continue")
log.error("something failed")

# %% exceptions_with_traceback
try:
    int("oops")
except ValueError:
    log.exception("conversion failed")  # logs the message AND the traceback
