from fastapi import APIRouter, Request

from app.api.v2 import (
    attacks,
    audit,
    ballots,
    blockchain,
    candidates,
    credentials,
    elections,
    tally,
    zk,
)
from app.schemas.abp import StatusResponse

router = APIRouter(prefix="/api/v2")


@router.get("/health", response_model=StatusResponse, tags=["health"])
def v2_health(request: Request) -> StatusResponse:
    return StatusResponse(
        ok=True,
        service="verivote-api-py-v2",
        mode=request.app.state.settings.app_mode,
    )


router.include_router(elections.router)
router.include_router(candidates.router)
router.include_router(credentials.router)
router.include_router(ballots.router)
router.include_router(audit.router)
router.include_router(tally.router)
router.include_router(zk.router)
router.include_router(blockchain.router)
router.include_router(attacks.router)

