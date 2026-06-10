from fastapi import APIRouter, Request

from app.schemas.abp import PrivateValidVoteStatusResponse

router = APIRouter(prefix="/zk", tags=["zk"])


@router.get("/status")
def zk_status(request: Request) -> dict:
    return request.app.state.services.zk.status()


@router.get(
    "/private-valid-vote/status",
    response_model=PrivateValidVoteStatusResponse,
)
def private_valid_vote_status(request: Request) -> PrivateValidVoteStatusResponse:
    return PrivateValidVoteStatusResponse(
        **request.app.state.services.zk.private_valid_vote_status()
    )
