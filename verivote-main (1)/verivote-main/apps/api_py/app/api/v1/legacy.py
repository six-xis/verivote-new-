from fastapi import APIRouter, Request

from app.schemas.abp import StatusResponse

router = APIRouter(prefix="/api/v1/legacy", tags=["legacy"])


@router.get("/health", response_model=StatusResponse)
def legacy_health(request: Request) -> StatusResponse:
    return StatusResponse(
        ok=True,
        service="verivote-api-py-legacy-compat",
        mode=request.app.state.settings.app_mode,
        legacy=True,
    )

