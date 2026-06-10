from fastapi import APIRouter, Request

from app.schemas.abp import AttackResponse

router = APIRouter(prefix="/attacks", tags=["attacks"])


@router.post(
    "/elections/{election_id}/tamper-commitment",
    response_model=AttackResponse,
)
def tamper_commitment(election_id: str, request: Request) -> AttackResponse:
    mutation = request.app.state.services.attacks.tamper_commitment(election_id)
    return AttackResponse(
        ok=True,
        attack_type=mutation.attack_type,
        mutation_id=mutation.id,
        message="Commitment tampering applied; audit report should fail.",
    )


@router.post(
    "/elections/{election_id}/inject-duplicate",
    response_model=AttackResponse,
)
def inject_duplicate(election_id: str, request: Request) -> AttackResponse:
    mutation = request.app.state.services.attacks.inject_duplicate(election_id)
    return AttackResponse(
        ok=True,
        attack_type=mutation.attack_type,
        mutation_id=mutation.id,
        message="Duplicate ballot injected; audit report should detect it.",
    )

