"""One error envelope for every failure, and the mapping from exceptions to HTTP status codes.

Clients see the same three fields whether the token was missing, the JSON was
malformed or the model timed out. ``request_id`` lets support find the trace.
"""

import logging
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

log = logging.getLogger("aiapp.api")

ErrorCode = Literal["unauthorized", "invalid_request", "not_found", "conflict", "model_timeout", "provider_error", "internal_error"]


class ErrorEnvelope(BaseModel):
    code: ErrorCode
    message: str
    request_id: str


class AppError(Exception):
    status: int = 500
    code: ErrorCode = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Unauthorized(AppError):
    status, code = 401, "unauthorized"


class NotFound(AppError):
    status, code = 404, "not_found"


class InvalidRequest(AppError):
    status, code = 422, "invalid_request"


class Conflict(AppError):
    """A run is already in progress on this thread, or a concurrent writer won the race."""

    status, code = 409, "conflict"


class ProviderError(AppError):
    status, code = 502, "provider_error"


class ModelTimeout(AppError):
    status, code = 504, "model_timeout"


def request_id_of(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def envelope(request: Request, status: int, code: ErrorCode, message: str) -> JSONResponse:
    body = ErrorEnvelope(code=code, message=message, request_id=request_id_of(request))
    return JSONResponse(status_code=status, content=body.model_dump(), headers={"X-Request-ID": body.request_id})


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return envelope(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p != "body")
        message = f"{where}: {first.get('msg', 'invalid request')}" if where else str(first.get("msg", "invalid request"))
        return envelope(request, 422, "invalid_request", message)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error request_id=%s", request_id_of(request))
        return envelope(request, 500, "internal_error", "internal error")
