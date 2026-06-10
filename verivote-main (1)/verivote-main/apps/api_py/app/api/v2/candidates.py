from fastapi import APIRouter, Request, status

from app.schemas.abp import CandidateResponse, CreateCandidateRequest

router = APIRouter(tags=["candidates"])


@router.post(
    "/elections/{election_id}/candidates",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_candidate(
    election_id: str,
    payload: CreateCandidateRequest,
    request: Request,
) -> CandidateResponse:
    candidate = request.app.state.services.elections.add_candidate(
        election_id=election_id,
        name=payload.name,
        description=payload.description,
    )
    return CandidateResponse(candidate=candidate)

