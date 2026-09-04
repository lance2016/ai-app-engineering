from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz(request: Request) -> dict[str, str]:
    return {"status": "ok", "model": request.app.state.model.name, "prompt_version": request.app.state.settings.prompt_version}
