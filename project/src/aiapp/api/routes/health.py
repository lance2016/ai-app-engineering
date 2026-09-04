"""Liveness is local and cheap; readiness asks every dependency (lesson 19: fail fast, do not hang)."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from aiapp.ops.health import postgres_check, redis_check, run_checks

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz(request: Request) -> dict[str, str]:
    return {"status": "ok", "model": request.app.state.model.name, "prompt_version": request.app.state.settings.prompt_version}


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    checks = {}
    if settings.database_url:
        checks["postgres"] = postgres_check(settings.database_url)
    if settings.redis_url:
        checks["redis"] = redis_check(settings.redis_url)

    async def model_ok() -> None:
        if getattr(request.app.state.model, "name", "").startswith("failing("):
            raise RuntimeError("model adapter is a failure injection")

    checks["model"] = model_ok
    results = await run_checks(checks)
    ready = all(r.ok for r in results)
    return JSONResponse(status_code=200 if ready else 503, content={"ready": ready, "checks": {r.name: {"ok": r.ok, "detail": r.detail} for r in results}})
