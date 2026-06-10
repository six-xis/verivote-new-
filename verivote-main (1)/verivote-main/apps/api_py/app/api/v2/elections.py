from fastapi import APIRouter, Request, status

from app.schemas.abp import (
    CreateElectionRequest,
    ElectionDetailResponse,
    ElectionListResponse,
    ElectionResponse,
)

router = APIRouter(tags=["elections"])


@router.get("/elections", response_model=ElectionListResponse)
def list_elections(request: Request) -> ElectionListResponse:
    elections = request.app.state.services.elections.list_elections()
    return ElectionListResponse(
        elections=[
            request.app.state.services.elections.public_election_summary(election)
            for election in elections
        ]
    )


@router.post("/elections", response_model=ElectionResponse, status_code=status.HTTP_201_CREATED)
def create_election(payload: CreateElectionRequest, request: Request) -> ElectionResponse:
    election = request.app.state.services.elections.create_election(
        title=payload.title,
        description=payload.description,
    )
    return ElectionResponse(election=election)


@router.get("/elections/{election_id}", response_model=ElectionDetailResponse)
def get_election(election_id: str, request: Request) -> ElectionDetailResponse:
    return ElectionDetailResponse(
        election=request.app.state.services.elections.public_election_detail(election_id)
    )
