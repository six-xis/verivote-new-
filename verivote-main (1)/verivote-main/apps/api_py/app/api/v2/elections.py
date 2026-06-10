from fastapi import APIRouter, Request, status

from app.schemas.abp import CreateElectionRequest, ElectionResponse

router = APIRouter(tags=["elections"])


@router.post("/elections", response_model=ElectionResponse, status_code=status.HTTP_201_CREATED)
def create_election(payload: CreateElectionRequest, request: Request) -> ElectionResponse:
    election = request.app.state.services.elections.create_election(
        title=payload.title,
        description=payload.description,
    )
    return ElectionResponse(election=election)

