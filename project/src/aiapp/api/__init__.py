"""HTTP surface of the service. ``create_app`` is the only entry point; everything else is wiring."""

from aiapp.api.app import create_app

__all__ = ["create_app"]
